import customtkinter as ctk

from fesium.ui.theme.styles import get_button_style

# Buttons never render narrower than this, so the same action is the same size
# wherever it appears.
MIN_BUTTON_WIDTH = 150


class Button(ctk.CTkButton):
    """The one button in Fesium.

    Views used to build ``CTkButton`` by hand and spread ``get_button_style``
    over the call, which meant every view repeated the enabled/disabled dance
    and picked its own width. Both now live here.

    ``variant`` is one of ``primary``, ``secondary``, ``danger``,
    ``danger_secondary`` or ``nav``. Use ``set_enabled`` rather than
    ``configure(state=...)``: the state and the colours have to change
    together, or a disabled button keeps the fill of an enabled one.
    """

    def __init__(
        self,
        master,
        text: str,
        *,
        variant: str = "secondary",
        enabled: bool = True,
        active: bool = False,
        command=None,
        **kwargs,
    ):
        self._variant = variant
        self._active = active
        self._enabled = enabled
        kwargs.setdefault("width", MIN_BUTTON_WIDTH)
        super().__init__(
            master,
            text=text,
            state="normal" if enabled else "disabled",
            command=command,
            **get_button_style(variant, active=active, enabled=enabled),
            **kwargs,
        )

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.configure(
            state="normal" if enabled else "disabled",
            **get_button_style(self._variant, active=self._active, enabled=enabled),
        )

    def set_active(self, active: bool) -> None:
        """Only meaningful for the ``nav`` variant, which marks the current view."""
        self._active = active
        self.configure(**get_button_style(self._variant, active=active, enabled=self._enabled))
