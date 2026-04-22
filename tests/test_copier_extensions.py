"""Tests for Copier extension lifecycle helpers."""

# ruff: noqa: D103

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from copier.errors import CopierError

from repoman.copier.extension_lifecycle import (
    MIRROR_KEY,
    EXTENSION_TYPE_COMMAND,
    ExtensionManifest,
    ExtensionInstance,
    ExtensionLifecycleError,
    _create_extension_instance,
    _ensure_no_conflicting_instance,
    _run_copy_or_raise,
    _seed_extension_answers_file,
    _set_copier_answers_mirror,
    _template_dir_for_type,
    _upsert_instance,
    create_command_extension,
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


def test_load_manifest_rejects_invalid_version_and_entry_shapes(tmp_path: Path) -> None:
    """Reject unsupported manifest versions and malformed entries."""
    manifest_path = tmp_path / ".repoman" / "extensions.yml"
    manifest_path.parent.mkdir(parents=True)

    manifest_path.write_text("version: 2\nextensions: []\n", encoding="utf-8")
    with pytest.raises(ExtensionLifecycleError, match="Unsupported extension manifest version"):
        load_manifest(tmp_path)

    manifest_path.write_text("version: 1\nextensions: {}\n", encoding="utf-8")
    with pytest.raises(ExtensionLifecycleError, match="'extensions' must be a list"):
        load_manifest(tmp_path)

    manifest_path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "extensions": [
                    {
                        "id": "command:foo",
                        "type": "command",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    with pytest.raises(ExtensionLifecycleError, match="Missing key"):
        load_manifest(tmp_path)


def test_seed_extension_answers_file_preserves_existing_files(tmp_path: Path) -> None:
    """Do not overwrite extension answers when Copier already created them."""
    answers_path = tmp_path / "foo.answers.yml"
    answers_path.write_text("existing: true\n", encoding="utf-8")

    _seed_extension_answers_file(answers_path, tmp_path, {"command_name": "foo"})

    assert answers_path.read_text(encoding="utf-8") == "existing: true\n"


def test_set_copier_answers_mirror_requires_existing_answers_file(tmp_path: Path) -> None:
    """Reject mirror updates when the base answers file is missing."""
    manifest = ExtensionManifest(version=1, extensions=[])

    with pytest.raises(ExtensionLifecycleError, match="Answers file not found"):
        _set_copier_answers_mirror(manifest, tmp_path / ".copier-answers.yml")


def test_upsert_and_conflict_detection_cover_replace_duplicate_and_singleton_rules() -> None:
    """Replace matching instances and reject duplicate or singleton conflicts."""
    existing = ExtensionInstance(
        id="command:foo",
        type="command",
        name="foo",
        status="active",
        answers_file=".repoman/extensions/command/foo.answers.yml",
        template_id="command",
        created_with_repoman_version="1.0.0",
    )
    replacement = ExtensionInstance(
        id="command:foo",
        type="command",
        name="foo",
        status="inactive",
        answers_file=".repoman/extensions/command/foo.answers.yml",
        template_id="command",
        created_with_repoman_version="2.0.0",
    )
    other = ExtensionInstance(
        id="command:bar",
        type="command",
        name="bar",
        status="active",
        answers_file=".repoman/extensions/command/bar.answers.yml",
        template_id="command",
        created_with_repoman_version="1.0.0",
    )
    manifest = ExtensionManifest(version=1, extensions=[existing, other])

    updated = _upsert_instance(manifest, replacement)
    assert updated.extensions == [replacement, other]

    with pytest.raises(ExtensionLifecycleError, match="already exists"):
        _ensure_no_conflicting_instance(
            manifest=manifest,
            extension_type="command",
            name="foo",
            force=False,
            singleton=False,
        )

    with pytest.raises(ExtensionLifecycleError, match="Only one command extension is supported"):
        _ensure_no_conflicting_instance(
            manifest=manifest,
            extension_type="command",
            name="baz",
            force=False,
            singleton=True,
        )


def test_run_copy_or_raise_wraps_copier_errors() -> None:
    """Translate Copier errors into lifecycle errors."""
    with patch("repoman.copier.extension_lifecycle.Worker", side_effect=CopierError("boom")):
        with pytest.raises(ExtensionLifecycleError, match="boom"):
            _run_copy_or_raise({"src_path": "/tmp/template"})


def test_create_command_extension_rejects_missing_package_name(tmp_path: Path) -> None:
    """Require python_package_import_name in Copier answers."""
    answers_file = _write_base_answers(tmp_path)

    with pytest.raises(ExtensionLifecycleError, match="Missing required answer"):
        create_command_extension(
            project_dir=tmp_path,
            base_answers_file=answers_file,
            answers={"python_package_import_name": "   "},
            command_name="foo",
            force=False,
            dry_run=True,
        )


def test_create_extension_instance_rejects_missing_template_dir(tmp_path: Path) -> None:
    """Fail early when the bundled extension template cannot be found."""
    answers_file = _write_base_answers(tmp_path)

    with pytest.raises(ExtensionLifecycleError, match="Extension template not found"):
        _create_extension_instance(
            project_dir=tmp_path,
            base_answers_file=answers_file,
            template_dir=tmp_path / "missing-template",
            extension_type=EXTENSION_TYPE_COMMAND,
            name="foo",
            extension_data={"command_name": "foo"},
            singleton=False,
            force=False,
            dry_run=True,
            expected_files=(tmp_path / "a", tmp_path / "b"),
        )


def test_template_dir_for_type_rejects_unknown_extension_type() -> None:
    """Reject unsupported extension types during sync."""
    with pytest.raises(ExtensionLifecycleError, match="Unsupported extension type"):
        _template_dir_for_type("not-supported")


def test_sync_extensions_handles_empty_manifest_and_filter_skips(tmp_path: Path) -> None:
    """Return empty sync results and skip inactive or filtered instances."""
    empty = sync_extensions(
        project_dir=tmp_path,
        force=False,
        conflict="inline",
        dry_run=True,
        extension_type=None,
        extension_name=None,
    )
    assert empty.synced == []
    assert empty.dry_run_options == []

    manifest = ExtensionManifest(
        version=1,
        extensions=[
            ExtensionInstance(
                id="command:inactive",
                type="command",
                name="inactive",
                status="inactive",
                answers_file=".repoman/extensions/command/inactive.answers.yml",
                template_id="command",
                created_with_repoman_version="1.0.0",
            ),
            ExtensionInstance(
                id="command:foo",
                type="command",
                name="foo",
                status="active",
                answers_file=".repoman/extensions/command/foo.answers.yml",
                template_id="command",
                created_with_repoman_version="1.0.0",
            ),
            ExtensionInstance(
                id="custom:bar",
                type="custom",
                name="bar",
                status="active",
                answers_file=".repoman/extensions/custom/bar.answers.yml",
                template_id="custom",
                created_with_repoman_version="1.0.0",
            ),
        ],
    )
    save_manifest(tmp_path, manifest)

    filtered = sync_extensions(
        project_dir=tmp_path,
        force=False,
        conflict="inline",
        dry_run=True,
        extension_type="command",
        extension_name="baz",
    )

    assert filtered.synced == []
    assert filtered.dry_run_options == []


def test_sync_extensions_rejects_missing_template_answers_and_worker_failures(tmp_path: Path) -> None:
    """Fail clearly on missing template paths, missing answers files, and Copier update errors."""
    save_manifest(
        tmp_path,
        ExtensionManifest(
            version=1,
            extensions=[
                ExtensionInstance(
                    id="command:foo",
                    type="command",
                    name="foo",
                    status="active",
                    answers_file=".repoman/extensions/command/foo.answers.yml",
                    template_id="command",
                    created_with_repoman_version="1.0.0",
                )
            ],
        ),
    )

    answers_path = tmp_path / ".repoman" / "extensions" / "command" / "foo.answers.yml"
    answers_path.parent.mkdir(parents=True, exist_ok=True)
    answers_path.write_text("_src_path: test\n", encoding="utf-8")

    with patch("repoman.copier.extension_lifecycle._command_template_dir", return_value=tmp_path / "missing-template"):
        with pytest.raises(ExtensionLifecycleError, match="Extension template not found"):
            sync_extensions(
                project_dir=tmp_path,
                force=False,
                conflict="inline",
                dry_run=False,
                extension_type=None,
                extension_name=None,
            )

    answers_path.unlink()
    with pytest.raises(ExtensionLifecycleError, match="answers file is missing"):
        sync_extensions(
            project_dir=tmp_path,
            force=False,
            conflict="inline",
            dry_run=False,
            extension_type=None,
            extension_name=None,
        )

    answers_path.write_text("_src_path: test\n", encoding="utf-8")
    with patch("repoman.copier.extension_lifecycle.Worker", side_effect=CopierError("boom")):
        with pytest.raises(ExtensionLifecycleError, match="boom"):
            sync_extensions(
                project_dir=tmp_path,
                force=False,
                conflict="inline",
                dry_run=False,
                extension_type=None,
                extension_name=None,
            )
