from pathlib import Path

from fesium.app import build_app_context


def test_build_app_context_uses_last_project_or_cwd(tmp_path):
    context = build_app_context(
        cwd=tmp_path,
        config_data={"last_project": ""},
    )

    assert context.project_root == tmp_path
    assert context.active_view == "overview"
