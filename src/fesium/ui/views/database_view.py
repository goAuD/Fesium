import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token, get_shape_token
from fesium.ui.widgets.bento import BentoGrid
from fesium.ui.widgets.body_text import BodyText
from fesium.ui.widgets.button import Button
from fesium.ui.widgets.tile import Tile
from fesium.ui.widgets.view_header import HEADER_GAP, ViewHeader

# CTkTextbox asks for 200px by default. Stacked, that overflows the window and
# grid stops honouring row weights, so the tiles clip instead of sharing the
# space. Asking for little lets the weights decide.
TEXTBOX_MIN_HEIGHT = 60

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


def format_schema_table(columns_info: tuple[dict, ...] | list[dict]) -> str:
    if not columns_info:
        return "Select a table to inspect its columns."

    rows = [
        (
            column["name"],
            column["type"] or "TEXT",
            "YES" if column["nullable"] else "NO",
            "YES" if column["primary_key"] else "",
        )
        for column in columns_info
    ]
    return format_query_result_table(["name", "type", "nullable", "pk"], rows)


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
        table = format_query_result_table(columns, rows)
        return {
            "title": f"{count} row" if count == 1 else f"{count} rows",
            "body": "\n".join((f"Columns: {len(columns)}", "", table)),
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
        # Not "Results": the panel this sits in is already titled Results, and
        # the two stacked headings read as a rendering bug.
        "title": "Nothing run yet",
        "body": "Run a query, or use Preview 100 Rows, to see results here",
        "tone": "accent.primary",
    }


def build_database_schema_view_model(
    *,
    tables: tuple[str, ...],
    selected_table: str,
    selected_table_info: tuple[dict, ...],
) -> dict[str, object]:
    resolved_table = selected_table if selected_table in tables else tables[0] if tables else ""
    if not tables:
        body = "No tables detected in the active database."
    else:
        body = format_schema_table(selected_table_info)

    return {
        "tables": tuple({"name": table_name, "active": table_name == resolved_table} for table_name in tables),
        "selected_table": resolved_table,
        "title": resolved_table or "No Table Selected",
        "body": body,
        "preview_enabled": bool(resolved_table),
        "table_count": len(tables),
        "column_count": len(selected_table_info),
    }


class DatabaseView(ctk.CTkFrame):
    """SQLite workbench laid out as a bento grid.

    The old version stacked six equally weighted panels, which put the reason
    you opened the page - write a query, read the rows - below the fold. Here
    the table list runs the full height on the left, and schema, editor and
    results share the right at 2:2:3, so results get the most room.

    The read-only switch sits with the Run button rather than in a separate
    controls panel: it gates what Run does, so that is where it belongs.
    """

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
        tables: tuple[str, ...] = (),
        selected_table: str = "",
        selected_table_info: tuple[dict, ...] = (),
        on_select_database=None,
        on_reset_project_database=None,
        on_toggle_read_only=None,
        on_select_table=None,
        on_preview_table=None,
        on_run_sql=None,
    ):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        summary = build_database_summary(
            db_path,
            read_only,
            source=source,
            project_database_available=project_database_available,
        )
        result_model = build_database_result_view_model(last_result or {"kind": "none"}, last_error)
        schema_model = build_database_schema_view_model(
            tables=tables,
            selected_table=selected_table,
            selected_table_info=selected_table_info,
        )

        header = ViewHeader(
            self,
            "Database",
            "SQLite queries with explicit safety defaults",
            badges=(
                (summary["source_badge"], summary["source_tone"]),
                (summary["mode_badge"], summary["mode_tone"]),
            ),
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, HEADER_GAP))

        grid = BentoGrid(self)
        grid.grid(row=1, column=0, sticky="nsew")

        grid.place_tile(
            self._build_connection_tile(
                grid, summary, on_select_database, on_reset_project_database
            ),
            row=0,
            column=0,
            span=12,
        )
        grid.place_tile(
            self._build_tables_tile(grid, schema_model, on_select_table),
            row=1,
            column=0,
            span=3,
            rowspan=2,
        )
        grid.place_tile(
            self._build_schema_tile(grid, schema_model, on_preview_table),
            row=1,
            column=3,
            span=9,
            # Schema carries a button row that the editor does not, so it needs
            # a little more weight to show the same number of lines.
            row_weight=3,
        )
        grid.place_tile(
            self._build_editor_tile(grid, db_path, read_only, last_query, on_toggle_read_only, on_run_sql),
            row=2,
            column=3,
            span=9,
            row_weight=2,
        )
        # Result tables are the widest thing here, so they get the full width.
        grid.place_tile(
            self._build_results_tile(grid, result_model),
            row=3,
            column=0,
            span=12,
            row_weight=3,
        )

    def _build_connection_tile(self, parent, summary, on_select_database, on_reset_project_database):
        tile = Tile(parent, "Connection")
        body = tile.body
        body.grid_columnconfigure(0, weight=1)

        path_value = BodyText(body, summary["path"], tone="text.secondary")
        path_value.grid(row=0, column=0, sticky="ew", padx=(0, 16))

        select_button = Button(body, "Select Database File", command=on_select_database)
        select_button.grid(row=0, column=1, sticky="e", padx=(0, 8))

        reset_button = Button(
            body,
            "Reset to Project Database",
            enabled=summary["can_reset"],
            width=210,
            command=on_reset_project_database,
        )
        reset_button.grid(row=0, column=2, sticky="e")
        return tile

    def _build_tables_tile(self, parent, schema_model, on_select_table):
        count = schema_model["table_count"]
        tile = Tile(parent, "Tables", meta=f"{count} detected" if count else "none")
        body = tile.body
        body.grid_rowconfigure(0, weight=1)

        if not schema_model["tables"]:
            empty = BodyText(
                body,
                "The active database does not expose any browseable tables yet.",
                tone="text.secondary",
            )
            empty.grid(row=0, column=0, sticky="new")
            return tile

        table_list = ctk.CTkScrollableFrame(body, fg_color="transparent", corner_radius=0)
        table_list.grid(row=0, column=0, sticky="nsew")
        table_list.grid_columnconfigure(0, weight=1)

        for row_index, table_entry in enumerate(schema_model["tables"]):
            button = Button(
                table_list,
                table_entry["name"],
                variant="nav",
                active=table_entry["active"],
                anchor="w",
                command=lambda table_name=table_entry["name"]: on_select_table(table_name)
                if on_select_table
                else None,
            )
            button.grid(row=row_index, column=0, sticky="ew", pady=(0 if row_index == 0 else 6, 0))
        return tile

    def _build_schema_tile(self, parent, schema_model, on_preview_table):
        columns = schema_model["column_count"]
        tile = Tile(
            parent,
            "Schema",
            meta=(
                f"{schema_model['title']} - {columns} columns"
                if schema_model["preview_enabled"]
                else "select a table"
            ),
        )
        body = tile.body
        body.grid_rowconfigure(0, weight=1)

        self.schema_textbox = ctk.CTkTextbox(
            body,
            fg_color=get_color_token("bg.app"),
            text_color=get_color_token("text.primary"),
            font=get_font_token("mono"),
            border_width=0,
            corner_radius=get_shape_token("input.radius"),
            height=TEXTBOX_MIN_HEIGHT,
        )
        self.schema_textbox.grid(row=0, column=0, sticky="nsew")
        self.schema_textbox.insert("1.0", schema_model["body"])
        self.schema_textbox.configure(state="disabled")

        preview_button = Button(
            body,
            "Preview 100 Rows",
            enabled=schema_model["preview_enabled"],
            command=on_preview_table,
        )
        preview_button.grid(row=1, column=0, sticky="e", pady=(12, 0))
        return tile

    def _build_editor_tile(self, parent, db_path, read_only, last_query, on_toggle_read_only, on_run_sql):
        tile = Tile(parent, "SQL", meta="one statement at a time")
        body = tile.body
        body.grid_rowconfigure(0, weight=1)

        self.query_textbox = ctk.CTkTextbox(
            body,
            fg_color=get_color_token("bg.app"),
            text_color=get_color_token("text.primary"),
            font=get_font_token("mono"),
            border_width=0,
            corner_radius=get_shape_token("input.radius"),
            height=TEXTBOX_MIN_HEIGHT,
        )
        self.query_textbox.grid(row=0, column=0, columnspan=2, sticky="nsew")
        if last_query:
            self.query_textbox.insert("1.0", last_query)

        # The switch gates what Run does, so it sits with Run rather than in a
        # separate controls panel three tiles away.
        self.read_only_switch = ctk.CTkSwitch(
            body,
            text="Read-only",
            text_color=get_color_token("text.primary"),
            font=get_font_token("body_medium"),
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
        self.read_only_switch.grid(row=1, column=0, sticky="w", pady=(12, 0))

        run_button = Button(
            body,
            "Run SQL",
            variant="primary",
            enabled=bool(db_path),
            command=lambda: on_run_sql(self.query_textbox.get("1.0", "end-1c")) if on_run_sql else None,
        )
        run_button.grid(row=1, column=1, sticky="e", pady=(12, 0))
        return tile

    def _build_results_tile(self, parent, result_model):
        tile = Tile(
            parent,
            "Results",
            meta=result_model["title"],
            meta_tone=result_model["tone"],
            surface="bg.panel_alt",
        )
        body = tile.body
        body.grid_rowconfigure(0, weight=1)

        self.result_textbox = ctk.CTkTextbox(
            body,
            fg_color=get_color_token("bg.app"),
            text_color=get_color_token("text.primary"),
            font=get_font_token("mono"),
            border_width=0,
            corner_radius=get_shape_token("input.radius"),
            height=TEXTBOX_MIN_HEIGHT,
        )
        self.result_textbox.grid(row=0, column=0, sticky="nsew")
        self.result_textbox.insert("1.0", result_model["body"])
        self.result_textbox.configure(state="disabled")
        return tile
