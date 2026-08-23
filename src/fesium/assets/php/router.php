<?php
// Fesium's filter for the PHP built-in server.
//
// `php -S` serves the document root raw: .env and .git/config are one plain
// GET away, with none of the checks ProjectFileHandler applies on the Python
// side. Returning false hands the request to the built-in handler unchanged;
// anything reaching for a dot-file gets a 403 instead.
//
// The path is decoded repeatedly because PHP decodes it once more when it
// resolves the file - the same two-phase decode that let /%252Eenv read as
// %2Eenv in a single-pass filter and as .env at the filesystem.
$parts = parse_url($_SERVER["REQUEST_URI"] ?? "/", PHP_URL_PATH);
$path = is_string($parts) ? $parts : "/";

$decoded = urldecode($path);
while (($next = urldecode($decoded)) !== $decoded) {
    $decoded = $next;
}

foreach (explode("/", str_replace("\\", "/", $decoded)) as $segment) {
    if ($segment !== "" && $segment[0] === ".") {
        http_response_code(403);
        exit("Not served");
    }
}

return false;