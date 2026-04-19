import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.panel_card import PanelCard
from fesium.ui.widgets.scrollable_view_body import ScrollableViewBody
from fesium.ui.widgets.status_badge import StatusBadge

SOURCE_BADGES = {
    "project": ("Project Database", "accent.primary"),
    "manual": ("Manual Database", "accent.warning"),
    "none": ("No Database Selected", "accent.danger"),
}


def format_query_result_table(columns: list, rows: list) -> str:
    if not columns:
        return "Query returned no rows"

    string_columns = [str(column) for column in columns]
    widths = [len(column) for column in string_columns]

    normalized_rows = []
    for row in rows:
        normalized_row = ["" if cell is None else str(cell) for cell in row]
        normalized_rows.append(normalized_row)
        for index, cell in enumerate(normalized_row):
            widths[index] = max(widths[index], len(cell))

    header = " | ".join(column.ljust(widths[index]) for index, column in enumerate(string_columns))
    divider = "-+-".join("-" * widths[index] for index in range(len(widths)))

    if not normalized_rows:
        return "\n".join((header, divider, "(no rows)"))

    body_lines = [
        " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))
        for row in normalized_rows
    ]
    return "\n".join((header, divider, *body_lines))


def build_database_summary(
    db_path: str,
    read_only: bool,
    *,
    source: str,
    project_database_available: bool,
):
    source_badge, source_tone = SOURCE_BADGES.get(
        source,
        ("Unknown Database", "accent.danger"),
    )
    return {
        "path": db_path or "No database selected",
        "source_badge": source_badge,
        "source_tone": source_tone,
        "mode_badge": "Read-only Enabled" if read_only else "Write Mode",
        "mode_tone": "accent.primary" if read_only else "accent.warning",
        "can_reset": project_database_available,
    }


def build_database_result_view_model(result: dict, last_error: str) -> dict[str, str]:
    if last_error:
        return {
            "title": "Execution Error",
            "body": last_error,
            "tone": "accent.danger",
        }

    kind = result.get("kind", "none")
    if kind == "read":
        count = result.get("count", 0)
        columns = result.get("columns", [])
        rows = result.get("rows", [])
        return {
            "title": f"{count} row" if count == 1 else f"{count} rows",
            "body": format_query_result_table(columns, rows),
            "tone": "accent.success",
        }

    if kind == "write":
        affected = result.get("affected", 0)
        return {
            "title": "Write query executed",
            "body": f"Affected rows: {affected}",
            "tone": "accent.warning",
        }

    return {
        "title": "Results",
        "body": "Run a query to see results",
        "tone": "accent.primary",
    }


class DatabaseView(ctk.CTkFrame):
    """Database operations view with safety-first messaging."""

    def __init__(
        self,
        master,
        db_path: str,
        read_only: bool,
        *,
        source: str,
        project_database_available: bool,
        last_query: str = "",
        last_result: dict | None = None,
        last_error: str = "",
        on_select_database=None,
        on_reset_project_database=None,
        on_toggle_read_only=None,
        on_run_sql=None,
    ):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        summary = build_database_summary(
            db_path,
            read_only,
            source=source,
            project_database_available=project_database_available,
        )
        result_model = build_database_result_view_model(last_result or {"kind": "none"}, last_error)

        title = ctk.CTkLabel(
            self,
            text="Database",
            text_color=get_color_token("text.primary"),
            font=get_font_token("heading"),
        )
        title.grid(row=0, column=0, sticky="w")

        badge_row = ctk.CTkFrame(self, fg_color="transparent")
        badge_row.grid(row=0, column=1, sticky="e")

        source_badge = StatusBadge(
            badge_row,
            text=summary["source_badge"],
            tone=summary["source_tone"],
        )
        source_badge.pack(side="left", padx=(0, 8))

        mode_badge = StatusBadge(
            badge_row,
            text=summary["mode_badge"],
            tone=summary["mode_tone"],
        )
        mode_badge.pack(side="left")

        subtitle = ctk.CTkLabel(
            self,
            text="SQLite queries with explicit safety defaults",
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 20))

        body = ScrollableViewBody(self)
        body.grid(row=2, column=0, columnspan=2, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        summary_panel = PanelCard(body, surface_variant="inset")
        summary_panel.grid(row=0, column=0, sticky="ew")
        summary_content = summary_panel.content_frame
        summary_content.grid_columnconfigure(0, weight=1)
        summary_content.grid_columnconfigure(1, weight=0)

        label = ctk.CTkLabel(
            summary_content,
            text="Selected Database",
            text_color=get_color_token("text.primary"),
            font=get_font_token("body_medium"),
        )
        label.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

        path_value = ctk.CTkLabel(
            summary_content,
            text=summary["path"],
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
            justify="left",
            wraplength=720,
        )
        path_value.grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 16))

        actions_panel = PanelCard(body, surface_variant="inset")
        actions_panel.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        actions_content = actions_panel.content_frame
        actions_content.grid_columnconfigure((0, 1), weight=1)
        actions_content.grid_columnconfigure(2, weight=0)

        select_database_button = ctk.CTkButton(
            actions_content,
            text="Select Database File",
            command=on_select_database,
        )
        select_database_button.grid(row=0, column=0, sticky="ew", padx=(16, 8), pady=(16, 12))

        reset_database_button = ctk.CTkButton(
            actions_content,
            text="Reset to Project Database",
            state="normal" if summary["can_reset"] else "disabled",
            fg_color=get_color_token("bg.app"),
            hover_color=get_color_token("bg.sidebar"),
            text_color=get_color_token("text.primary"),
            border_width=1,
            border_color=get_color_token("border.default"),
            command=on_reset_project_database,
        )
        reset_database_button.grid(row=0, column=1, sticky="ew", padx=8, pady=(16, 12))

        self.read_only_switch = ctk.CTkSwitch(
            actions_content,
            text="Read-only",
            text_color=get_color_token("text.primary"),
            progress_color=get_color_token("accent.primary"),
            button_color=get_color_token("text.primary"),
            button_hover_color=get_color_token("text.secondary"),
            command=lambda: on_toggle_read_only(bool(self.read_only_switch.get()))
            if on_toggle_read_only
            else None,
        )
        if read_only:
            self.read_only_switch.select()
        else:
            self.read_only_switch.deselect()
        self.read_only_switch.grid(row=0, column=2, sticky="e", padx=(8, 16), pady=(16, 12))

        editor_panel = PanelCard(body, surface_variant="inset")
        editor_panel.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        editor_content = editor_panel.content_frame
        editor_content.grid_columnconfigure(0, weight=1)

        editor_label = ctk.CTkLabel(
            editor_content,
            text="SQL Editor",
            text_color=get_color_token("text.primary"),
            font=get_font_token("body_medium"),
        )
        editor_label.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 12))

        self.query_textbox = ctk.CTkTextbox(
            editor_content,
            fg_color=get_color_token("bg.app"),
            text_color=get_color_token("text.primary"),
            font=get_font_token("mono"),
            height=180,
        )
        self.query_textbox.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        if last_query:
            self.query_textbox.insert("1.0", last_query)

        run_button = ctk.CTkButton(
            editor_content,
            text="Run SQL",
            state="normal" if db_path else "disabled",
            command=lambda: on_run_sql(self.query_textbox.get("1.0", "end-1c"))
            if on_run_sql
            else None,
        )
        run_button.grid(row=2, column=0, sticky="e", padx=16, pady=(0, 16))

        result_panel = PanelCard(body, surface_variant="inset_strong")
        result_panel.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        result_content = result_panel.content_frame
        result_content.grid_columnconfigure(0, weight=1)

        result_label = ctk.CTkLabel(
            result_content,
            text=result_model["title"],
            text_color=get_color_token(result_model["tone"]),
            font=get_font_token("body_medium"),
        )
        result_label.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 12))

        self.result_textbox = ctk.CTkTextbox(
            result_content,
            fg_color=get_color_token("bg.app"),
            text_color=get_color_token("text.secondary"),
            font=get_font_token("mono"),
            height=240,
        )
        self.result_textbox.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.result_textbox.insert("1.0", result_model["body"])
        self.result_textbox.configure(state="disabled")
