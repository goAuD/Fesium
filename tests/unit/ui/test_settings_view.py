from fesium.ui.views.settings_view import NO_DEFAULT_PROJECT, build_settings_model


def test_build_settings_model_renders_stored_preferences():
    model = build_settings_model(
        {
            "port": 9001,
            "default_project": "/projects/default",
            "restore_last_project": False,
            "last_project": "/projects/portal",
        }
    )

    assert model["port"] == "9001"
    assert model["default_project"] == "/projects/default"
    assert model["has_default_project"] is True
    assert model["restore_last_project"] is False


def test_build_settings_model_is_explicit_when_no_default_folder_is_set():
    model = build_settings_model({"port": 8000})

    assert model["default_project"] == NO_DEFAULT_PROJECT
    assert model["has_default_project"] is False


def test_build_settings_model_defaults_to_restoring_the_last_project():
    """An older config file has no restore key, and the old behaviour was to restore."""
    assert build_settings_model({})["restore_last_project"] is True


def test_build_settings_model_states_which_folder_opens_next():
    restoring = build_settings_model(
        {"last_project": "/projects/portal", "restore_last_project": True}
    )
    not_restoring = build_settings_model(
        {
            "last_project": "/projects/portal",
            "default_project": "/projects/default",
            "restore_last_project": False,
        }
    )

    assert "/projects/portal" in restoring["startup_summary"]
    assert "/projects/default" in not_restoring["startup_summary"]


def test_build_settings_model_quotes_the_allowed_port_range_in_its_hint():
    hint = build_settings_model({})["port_hint"]

    assert "1024" in hint
    assert "65535" in hint
