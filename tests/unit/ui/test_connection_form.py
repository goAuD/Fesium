"""Connection form model tests - pure functions, no display needed."""

from fesium.core.project_database import ConnectionSettings, DatabaseRequirement
from fesium.ui.views.database_view import build_connection_form_model

MYSQL_REQUIREMENT = DatabaseRequirement(
    connection="mysql",
    host="127.0.0.1",
    port=3306,
    database="shop",
)

SETTINGS = ConnectionSettings(
    engine="mysql", host="db.local", port=3307, database="shop", user="student"
)


def field_values(model):
    return {field["key"]: field["value"] for field in model["fields"]}


def test_form_prefills_host_port_database_from_the_project_env():
    model = build_connection_form_model(MYSQL_REQUIREMENT, connected=False)

    assert model["visible"] is True
    values = field_values(model)
    assert values["host"] == "127.0.0.1"
    assert values["port"] == "3306"
    assert values["database"] == "shop"
    # No credential ever arrives from the .env, so these start empty.
    assert values["user"] == ""
    assert values["password"] == ""


def test_form_falls_back_to_the_default_port_when_none_is_set():
    requirement = DatabaseRequirement(connection="mariadb", host="localhost", port=None, database="app")

    model = build_connection_form_model(requirement, connected=False)

    assert field_values(model)["port"] == "3306"
    assert model["engine_label"] == "mariadb"


def test_form_stays_hidden_for_file_backed_projects():
    sqlite_requirement = DatabaseRequirement(connection="sqlite", host="", port=None, database="")

    model = build_connection_form_model(sqlite_requirement, connected=False)

    assert model["visible"] is False


def test_connected_form_keeps_session_settings_and_asks_to_disconnect():
    model = build_connection_form_model(MYSQL_REQUIREMENT, connected=True, settings=SETTINGS)

    assert model["connected"] is True
    assert model["button_label"] == "Disconnect"
    values = field_values(model)
    assert values["host"] == "db.local"
    assert values["port"] == "3307"
    assert values["user"] == "student"
    # The password is never carried back into the form.
    assert values["password"] == ""
    assert "Connected to mysql at db.local:3307" in model["status"]
    assert model["status_tone"] == "accent.success"


def test_connection_failure_surfaces_with_the_error_tone():
    model = build_connection_form_model(
        MYSQL_REQUIREMENT,
        connected=False,
        last_error="Nothing is listening at 127.0.0.1:3306.",
    )

    assert "Nothing is listening" in model["status"]
    assert model["status_tone"] == "accent.danger"


def test_no_field_of_the_model_ever_carries_a_password():
    model = build_connection_form_model(MYSQL_REQUIREMENT, connected=True, settings=SETTINGS)

    for field in model["fields"]:
        if field["secret"]:
            # The password entry starts empty on every rebuild - the value a
            # user typed lives only in the widget, never in a model or state.
            assert field["value"] == ""
        assert field["value"] != SETTINGS.address or field["key"] != "password"
