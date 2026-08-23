# Biztonsági átnézés: lokális szerver (ox-alpha, 2026-08-23)

Tárgy: `src/fesium/core/static_server.py`, `src/fesium/core/server.py`, `src/fesium/core/browser.py`,
illetve a dokumentumgyökér-validálás (`src/fesium/core/security.py`, `src/fesium/app/controller.py`).

Módszer: statikus kódelemzés, a stdlib `http.server` (`SimpleHTTPRequestHandler.translate_path`)
viselkedésével összevetve. Nem készült futásidejű exploit-teszt.

Fenyegetési modell: csak-localhost fejlesztői szerver, publikus expozíció nélkül. Authentikáció,
HTTPS, rate limiting és külső függőségek szándékosan nem javasoltak.

---

## Összegzés prioritás szerint

| # | Megállapítás | Hely | Kockázat |
|---|---|---|---|
| 1 | Dupla dekódolás bypass (`%252E`) | `static_server.py:31` vs. stdlib `translate_path` | Magas |
| 2 | PHP backend: nincs dotfile-szűrő | `server.py:133` | Magas |
| 3 | DNS rebinding: nincs Host-fejléc-ellenőrzés | `static_server.py:70–97` | Közepes |
| 4 | Szimlink/junction kilépés a gyökérből | `static_server.py:78–82` | Közepes |
| 5 | 8.3 rövid nevek (Windows, kötetfüggő) | `static_server.py:32` | Közepes/alacsony |
| 6 | NTFS ADS (`::$DATA`) | az #1 altípusa | Az #1-gyel együtt oldódik |

---

## A) `is_hidden_path()` megkerülése — IGEN, megkerülhető

### A1. Dupla URL-kódolás — megtalált bypass (legfontosabb eredmény)

- **Hely:** `src/fesium/core/static_server.py:31` (egyszeri `urllib.parse.unquote`) szemben a
  `SimpleHTTPRequestHandler.translate_path` belső, saját `unquote`-jával, amelyet a
  `super().send_head()` (78–82. sor) hív meg.
- **Probléma:** a saját ellenőrzés egyszer dekódol, a stdlib még egyszer. Két dekódolási fázis,
  egy ellenőrzési fázis.
- **Támadó bemenet:** `GET /%252Eenv` vagy `GET /%252Egit/config`
  - `is_hidden_path()` az első dekódolás után `%2Eenv`-et lát → nem ponttal kezdődik → átengedi.
  - `translate_path` második dekódolása → `.env` → **kiszolgálja a fájlt**.
- **Hatás:** a `.env` teljes tartalma és a `.git` teljes fája olvasható — pontosan az, ami ellenére
  a védelmet írták (a docstring, 20–26. sor, ezt a célt mondja ki).
- **Kockázat:** magas ebben a modellben. Nem kell hálózati támadó: egy böngészőfülben futó oldal
  DNS-rebinding-gel (lásd C) vagy egy projektoldalon lévő `<img src="/%252Eenv">` is eléri.
- **Javasolt javítás:** ismételt `unquote`, amíg a string stabil (`while new != current`), vagy ha
  a dekódolás után `%` marad a szegmensben, elutasítás.

### A2. NTFS Alternate Data Stream — ugyanazon a bypasson át

- **Hely:** `static_server.py:31–32` — a `$DATA`/kettőspont nem szerepel a szűrőben, de önmagában
  a `/.env::$DATA` blokkolva lenne (ponttal kezdődő szegmens).
- **Támadó bemenet:** `GET /%252Eenv::$DATA` → az A1 bypass-szal a Windows a `.env`
  tartalom-streamjét nyitja meg.
- **Kockázat:** közepes — gyakorlatilag az A1 altípusa; az A1 javítása ezt lefedi.

### A3. Windows rövid nevek (8.3) — külön bypass, kódolástól függetlenül

- **Hely:** `static_server.py:32` — csak a szöveges útvonalat nézi; a `GIT~1` nem tartalmaz pontot.
- **Támadó bemenet:** `GET /GIT~1/config` (a `.git` rövid neve), ha a köteten engedélyezett a
  8.3-névgenerálás (SMB-megosztásokon és régebbi Windows-köteteken alapértelmezett; sok modern
  rendszeren kikapcsolt).
- **Kockázat:** közepes, platformfüggő. Tiszta szöveges szinten nem védhető ki; reális enyhítés:
  a kért útvonal `resolve()`-olása után ellenőrizni, hogy bármelyik szegmens valódi neve ponttal-e
  kezdődik — vagy dokumentálni a korlátot.

### A4. Szimbolikus linkek / junctions — a gyökéren kívülre vezetnek

- **Hely:** `static_server.py:78–82` — csak szöveget ellenőriz; a `translate_path`/`open` követi a
  linket, tartalmazás-ellenőrzés nélkül.
- **Támadó bemenet:** nem HTTP-bemenet, hanem **projekt-tartalom**: egy klónozott repóban lévő
  `link -> /home/user` vagy Windows junction `C:\Users\xxx\documents`-ra. Utána
  `GET /link/.ssh/id_rsa`.
- **Forgatókönyv:** diák klónoz egy rosszindulatú „gyakorló" repót, Fesiummal kiszolgálja →
  tetszőleges fájl olvasható a gépéről.
- **Kockázat:** közepes. Javítás: a lefordított útvonalat `Path.resolve()`-olni és ellenőrizni,
  hogy a dokumentumgyökér prefixe-e — ez az A3-at is részben kezeli.

### Ami NEM problémának bizonyult (ellenőrizve)

- **`..` szegmensek:** a `translate_path` a végső dekódolás **után** `normpath`-ol, és a gyökérre
  fog vissza — a klasszikus `../../../etc/passwd` nem jut ki a gyökérből. Rendben.
- **Backslash:** a 32. sor `replace("\", "/")`-je lefedi; a stdlib `dirname(word)`-szűrése a
  vegyes formákat is kiszűri. Rendben.
- **Unicode-normalizálás:** a pont (U+002E) normalizálás-álló, a fullwidth variánsokat a
  fájlrendszer nem mappeli `.`-ra. Nem kihasználható.

## B) Dokumentumgyökéren kívüli kiszolgálás a `send_head` felüldefiniálás mellett

Két csatorna van:

1. **Szimlinkek/junctions** (A4) — ez az egyetlen valódi „gyökéren kívüli" vektor.
2. A dupla dekódolás (A1) a gyökéren **belül** ér el rejtett fájlokat, kívülre nem juttat.

Maguk a `list_directory` (84–91. sor) és a `render_no_index_page` (35–67. sor) rendben vannak:
minden interpolált érték `html.escape`-elve, nincs XSS a 404-oldalon.

## C) A `127.0.0.1`-re kötés

- `static_server.py:133` és `server.py:133`: tényleg csak az IPv4 loopbacken figyel, hálózati
  interfészen nem elérhető. Ebben az értelemben korrekt.
- **Kivételek, ahol mégis van expozíció:**
  1. **Azonos gépen lévő többi felhasználó/folyamat** (pl. laborgép, közös munkaállomás) — a
     loopbacket minden helyi fiók eléri. Az A1 bypass-szal ez azt jelenti: másik felhasználó
     olvashatja a `.env`-et.
  2. **DNS rebinding** — a legfontosabb távoli vektor. Egy rosszindulatú weboldal az `evil.com`-ot
     átirányítja `127.0.0.1`-re, majd ugyanarról az originről `fetch`-elheti a szervert (a böngésző
     SOP már nem véd, mert az origin „egyezik"). A port 8000–8009-es tartománya könnyen
     találgatható. **Javítás függőségnélkül:** a `ProjectFileHandler.send_head`-ben
     Host-fejléc-ellenőrzés (`self.headers["Host"]` == `127.0.0.1:{port}`) — a rebinding kérések
     Host-ja a támadó domainje lesz. Pár sor, külső könyvtár nélkül. A PHP-szervernél ez a vektor
     nyitva marad (ott nem mi kezeljük a fejléceket).
  3. Periférikus: WSL2 mirrored networking / Docker port-publish esetén a konténerben futtatott
     szerver kiszivároghat a gazdagépig — dokumentációs megjegyzés szintjén.

## D) `php -S 127.0.0.1:PORT -t docroot` — IGEN, kiszolgál mindent, amit nem kellene

- **Hely:** `src/fesium/core/server.py:133` — nincs router script, tehát a PHP beépített szervere
  **nyers statikus kiszolgálást** ad, ponttal kezdődő fájlok szűrése nélkül. Ez dokumentált
  viselkedés a PHP-ben.
- **Támadó bemenet:** sima `GET /.env` vagy `GET /.git/config` — semmilyen kódolási trükk sem
  kell, mert **nincs szűrő, amit megkerülni**.
- **Hatás:** ugyanaz az adat, ami ellenére a `ProjectFileHandler`-t írták, a PHP backendre
  váltással szabadon olvasható. A két backend közötti biztonsági szint tehát inkonzisztens.
- **Kockázat:** magas a projekt célkitűzéseihez képest, mert a legkézenfekvőbb kérés (`/.env`)
  működik.
- **Javasolt javítás:** egy kis beépített `router.php` (a `php -S` negyedik paramétere), amely
  ugyanazt az `is_hidden_path` logikát alkalmazza, és minden mást `false`-zal a stdlib-re bízzon.
  Nulla új függőség.

## E) `browser.py` URL-validálás — szilárd, apró megjegyzések

- `src/fesium/core/browser.py:10` — csak `http` séma engedélyezett (`file://`, `javascript:`
  blokkolva). Jó.
- `:13` — userinfo-ellenőrzés elkapja a `http://127.0.0.1@evil.com/` trükköt. Jó.
- `:16` — hostname-whitelist (`localhost`, `127.0.0.1`); a `[::1]` elutasított, ami konzisztens
  az IPv4-only kötéssel. Jó.
- `:19–22` — a `parsed.port` ValueError-kezelése elkapja az érvénytelen portokat. Jó.
- Megjegyzés (nem sebezhetőség): a whitelist szigorúbb, mint amire szükség lenne — a
  `127.0.0.2`–`127.255.255.254` is loopback —, de szigorúbb whitelist biztonsági szempontból
  helyes irány. A URL-ek belsőleg generáltak (`LOOPBACK` + port), így ez a réteg
  védelem-mélység; jelen állapotában rendben hagyható.

---

## Javasolt javítási sorrend

1. **#1** — stabilizáló `unquote`-ciklus az `is_hidden_path`-ban (kb. 3 sor) + egységtesztek
   `%252E`, `%252Egit/config`, `%252Eenv::$DATA` bemenetekre.
2. **#3** — Host-fejléc-ellenőrzés a `ProjectFileHandler`-ben (kb. 10 sor) + teszt idegen Host
   fejléccel.
3. **#2** — mini `router.php` a `PHPServer` parancssorába (a `php -S` negyedik paramétere),
   ugyanazzal a dotfile-logikával.
4. **#4** — `resolve()` + dokumentumgyökér-prefix-ellenőrzés a `send_head`-ben (részben kezeli
   az A3-at is).
5. **#5** — dokumentálni a korlátot, vagy a #4 resolve-alapú ellenőrzésével együtt kezelni.