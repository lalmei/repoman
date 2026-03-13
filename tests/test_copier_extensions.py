"""Tests for Copier extension lifecycle helpers."""

# ruff: noqa: D103

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from repoman.copier.extension_lifecycle import (
    MIRROR_KEY,
    ExtensionLifecycleError,
    ExtensionManifest,
    create_command_extension,
    create_graphrag_extension,
    load_manifest,
    save_manifest,
    sync_extensions,
)


def _write_base_answers(project_dir: Path) -> Path:
    answers_file = project_dir / ".copier-answers.yml"
    answers_file.write_text(
        yaml.safe_dump(
            {
                "python_package_import_name": "pkg",
                "python_package_command_line_name": "pkg",
                "rag_enabled": True,
                "fastapi_enabled": True,
                "include_health_endpoints": True,
            },
            sort_keys=False,
        )
    )
    return answers_file


def test_load_manifest_missing_returns_empty(tmp_path: Path) -> None:
    manifest = load_manifest(tmp_path)
    assert manifest.version == 1
    assert manifest.extensions == []


def test_save_and_load_manifest_roundtrip(tmp_path: Path) -> None:
    manifest = ExtensionManifest(version=1, extensions=[])
    save_manifest(tmp_path, manifest)

    loaded = load_manifest(tmp_path)
    assert loaded.version == 1
    assert loaded.extensions == []


def test_create_command_extension_dry_run_does_not_write_manifest(
    tmp_path: Path,
) -> None:
    answers_file = _write_base_answers(tmp_path)

    instance, copier_options, command_file, test_file = create_command_extension(
        project_dir=tmp_path,
        base_answers_file=answers_file,
        answers={
            "python_package_import_name": "pkg",
            "python_package_command_line_name": "pkg",
        },
        command_name="foo",
        force=False,
        dry_run=True,
    )

    assert instance.id == "command:foo"
    assert copier_options["dst_path"] == str(tmp_path)
    assert command_file == tmp_path / "src" / "pkg" / "cli" / "commands" / "foo" / "__init__.py"
    assert test_file == tmp_path / "tests" / "test_cli" / "test_foo.py"
    assert not (tmp_path / ".repoman" / "extensions.yml").exists()


def test_create_command_extension_persists_manifest_and_answers(tmp_path: Path) -> None:
    answers_file = _write_base_answers(tmp_path)

    worker_ctx = MagicMock()
    worker_ctx.__enter__.return_value = worker_ctx
    worker_ctx.__exit__.return_value = None

    with patch("repoman.copier.extension_lifecycle.Worker", return_value=worker_ctx) as mock_worker:
        create_command_extension(
            project_dir=tmp_path,
            base_answers_file=answers_file,
            answers={
                "python_package_import_name": "pkg",
                "python_package_command_line_name": "pkg",
            },
            command_name="foo",
            force=False,
            dry_run=False,
        )

    mock_worker.assert_called_once()
    worker_ctx.run_copy.assert_called_once()

    manifest = load_manifest(tmp_path)
    assert len(manifest.extensions) == 1
    assert manifest.extensions[0].id == "command:foo"

    base_answers = yaml.safe_load(answers_file.read_text())
    assert MIRROR_KEY in base_answers
    assert base_answers[MIRROR_KEY]["extensions"][0]["id"] == "command:foo"


def test_sync_extensions_dry_run_returns_options(tmp_path: Path) -> None:
    answers_file = _write_base_answers(tmp_path)

    worker_ctx = MagicMock()
    worker_ctx.__enter__.return_value = worker_ctx
    worker_ctx.__exit__.return_value = None

    with patch("repoman.copier.extension_lifecycle.Worker", return_value=worker_ctx):
        create_command_extension(
            project_dir=tmp_path,
            base_answers_file=answers_file,
            answers={
                "python_package_import_name": "pkg",
                "python_package_command_line_name": "pkg",
            },
            command_name="foo",
            force=False,
            dry_run=False,
        )

    result = sync_extensions(
        project_dir=tmp_path,
        force=False,
        conflict="inline",
        dry_run=True,
        extension_type=None,
        extension_name=None,
    )
    assert len(result.synced) == 1
    assert len(result.dry_run_options) == 1


def test_sync_extensions_runs_worker_update(tmp_path: Path) -> None:
    answers_file = _write_base_answers(tmp_path)

    create_ctx = MagicMock()
    create_ctx.__enter__.return_value = create_ctx
    create_ctx.__exit__.return_value = None

    update_ctx = MagicMock()
    update_ctx.__enter__.return_value = update_ctx
    update_ctx.__exit__.return_value = None

    with patch(
        "repoman.copier.extension_lifecycle.Worker",
        side_effect=[create_ctx, update_ctx],
    ):
        create_command_extension(
            project_dir=tmp_path,
            base_answers_file=answers_file,
            answers={
                "python_package_import_name": "pkg",
                "python_package_command_line_name": "pkg",
            },
            command_name="foo",
            force=False,
            dry_run=False,
        )

        result = sync_extensions(
            project_dir=tmp_path,
            force=False,
            conflict="inline",
            dry_run=False,
            extension_type="command",
            extension_name="foo",
        )

    assert len(result.synced) == 1
    update_ctx.run_update.assert_called_once()


def test_create_graphrag_extension_persists_manifest(tmp_path: Path) -> None:
    answers_file = _write_base_answers(tmp_path)
    worker_ctx = MagicMock()
    worker_ctx.__enter__.return_value = worker_ctx
    worker_ctx.__exit__.return_value = None

    with patch("repoman.copier.extension_lifecycle.Worker", return_value=worker_ctx):
        create_graphrag_extension(
            project_dir=tmp_path,
            base_answers_file=answers_file,
            answers={
                "python_package_import_name": "pkg",
                "python_package_command_line_name": "pkg",
                "rag_enabled": True,
                "fastapi_enabled": True,
                "include_health_endpoints": True,
            },
            instance_name="graphrag",
            force=False,
            dry_run=False,
        )

    manifest = load_manifest(tmp_path)
    assert any(ext.type == "graphrag" and ext.name == "graphrag" for ext in manifest.extensions)


def test_create_graphrag_extension_requires_rag_enabled(tmp_path: Path) -> None:
    answers_file = _write_base_answers(tmp_path)
    with (
        patch("repoman.copier.extension_lifecycle.Worker"),
        pytest.raises(ExtensionLifecycleError, match="rag_enabled=true"),
    ):
        create_graphrag_extension(
            project_dir=tmp_path,
            base_answers_file=answers_file,
            answers={
                "python_package_import_name": "pkg",
                "python_package_command_line_name": "pkg",
                "rag_enabled": False,
                "fastapi_enabled": True,
            },
            instance_name="graphrag",
            force=False,
            dry_run=False,
        )


def test_create_graphrag_extension_singleton_guard(tmp_path: Path) -> None:
    answers_file = _write_base_answers(tmp_path)
    worker_ctx = MagicMock()
    worker_ctx.__enter__.return_value = worker_ctx
    worker_ctx.__exit__.return_value = None

    with patch("repoman.copier.extension_lifecycle.Worker", return_value=worker_ctx):
        create_graphrag_extension(
            project_dir=tmp_path,
            base_answers_file=answers_file,
            answers={
                "python_package_import_name": "pkg",
                "python_package_command_line_name": "pkg",
                "rag_enabled": True,
                "fastapi_enabled": False,
            },
            instance_name="graphrag",
            force=False,
            dry_run=False,
        )

        with pytest.raises(ExtensionLifecycleError, match="Only one graphrag extension"):
            create_graphrag_extension(
                project_dir=tmp_path,
                base_answers_file=answers_file,
                answers={
                    "python_package_import_name": "pkg",
                    "python_package_command_line_name": "pkg",
                    "rag_enabled": True,
                    "fastapi_enabled": False,
                },
                instance_name="other",
                force=False,
                dry_run=False,
            )


def test_sync_extensions_filters_graphrag_type(tmp_path: Path) -> None:
    answers_file = _write_base_answers(tmp_path)
    create_ctx = MagicMock()
    create_ctx.__enter__.return_value = create_ctx
    create_ctx.__exit__.return_value = None
    update_ctx = MagicMock()
    update_ctx.__enter__.return_value = update_ctx
    update_ctx.__exit__.return_value = None

    with patch(
        "repoman.copier.extension_lifecycle.Worker",
        side_effect=[create_ctx, update_ctx],
    ):
        create_graphrag_extension(
            project_dir=tmp_path,
            base_answers_file=answers_file,
            answers={
                "python_package_import_name": "pkg",
                "python_package_command_line_name": "pkg",
                "rag_enabled": True,
                "fastapi_enabled": False,
            },
            instance_name="graphrag",
            force=False,
            dry_run=False,
        )

        result = sync_extensions(
            project_dir=tmp_path,
            force=False,
            conflict="inline",
            dry_run=False,
            extension_type="graphrag",
            extension_name="graphrag",
        )

    assert len(result.synced) == 1
    update_ctx.run_update.assert_called_once()
