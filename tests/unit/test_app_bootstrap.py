from pathlib import Path

from fesium.app import build_app_context, build_default_paths, main


def test_fesium_app_package_exports_bootstrap_symbols():
    assert callable(build_app_context)
    assert callable(build_default_paths)
    assert callable(main)


def test_build_app_context_uses_last_project_or_cwd(tmp_path):
    context = build_app_context(
        cwd=tmp_path,
        config_data={"last_project": ""},
    )

    assert context.project_root == tmp_path
    assert context.active_view == "overview"
