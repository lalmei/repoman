"""Extension lifecycle operations for Copier-managed project extensions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml
from copier import Worker
from copier.errors import CopierError

from repoman._version import get_version

MANIFEST_VERSION = 1
MANIFEST_RELATIVE_PATH = Path(".repoman/extensions.yml")
EXTENSION_ANSWERS_ROOT = Path(".repoman/extensions")
MIRROR_KEY = "_repoman_extensions"

EXTENSION_TYPE_COMMAND = "command"


@dataclass
class ExtensionInstance:
    """Single extension instance metadata."""

    id: str
    type: str
    name: str
    status: str
    answers_file: str
    template_id: str
    created_with_repoman_version: str


@dataclass
class ExtensionManifest:
    """Versioned extension manifest."""

    version: int
    extensions: list[ExtensionInstance]


@dataclass
class ExtensionSyncResult:
    """Result of syncing extension instances."""

    synced: list[ExtensionInstance]
    dry_run_options: list[dict[str, Any]]


class ExtensionLifecycleError(RuntimeError):
    """Raised when extension lifecycle operations fail."""


def _repoman_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _command_template_dir() -> Path:
    return _repoman_root() / "extentions" / "command_template" / "{{command_name}}"


def _manifest_path(project_dir: Path) -> Path:
    return project_dir / MANIFEST_RELATIVE_PATH


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def _seed_extension_answers_file(path: Path, template_dir: Path, data: dict[str, Any]) -> None:
    """Create a minimal answers file when Copier does not materialize one."""
    if path.exists():
        return
    payload: dict[str, Any] = {
        "_src_path": str(template_dir),
        "_subdirectory": "",
        **data,
    }
    _dump_yaml(path, payload)


def _answers_path_for(project_dir: Path, extension_type: str, name: str) -> Path:
    return project_dir / EXTENSION_ANSWERS_ROOT / extension_type / f"{name}.answers.yml"


def _to_instance(raw: dict[str, Any]) -> ExtensionInstance:
    try:
        return ExtensionInstance(
            id=str(raw["id"]),
            type=str(raw["type"]),
            name=str(raw["name"]),
            status=str(raw.get("status", "active")),
            answers_file=str(raw["answers_file"]),
            template_id=str(raw["template_id"]),
            created_with_repoman_version=str(raw.get("created_with_repoman_version", "unknown")),
        )
    except KeyError as e:
        raise ExtensionLifecycleError(f"Invalid extension manifest entry. Missing key: {e}") from e


def load_manifest(project_dir: Path) -> ExtensionManifest:
    """Load extension manifest from project directory.

    Missing manifest returns an empty manifest.
    """
    manifest_path = _manifest_path(project_dir)
    if not manifest_path.exists():
        return ExtensionManifest(version=MANIFEST_VERSION, extensions=[])

    payload = _load_yaml(manifest_path)
    version = int(payload.get("version", MANIFEST_VERSION))
    if version != MANIFEST_VERSION:
        raise ExtensionLifecycleError(
            f"Unsupported extension manifest version: {version}. Expected {MANIFEST_VERSION}."
        )

    raw_extensions = payload.get("extensions", [])
    if not isinstance(raw_extensions, list):
        raise ExtensionLifecycleError("Invalid extension manifest: 'extensions' must be a list")

    extensions = [_to_instance(raw) for raw in raw_extensions]
    return ExtensionManifest(version=version, extensions=extensions)


def save_manifest(project_dir: Path, manifest: ExtensionManifest) -> None:
    """Persist extension manifest to project directory."""
    payload: dict[str, Any] = {
        "version": manifest.version,
        "extensions": [asdict(ext) for ext in manifest.extensions],
    }
    _dump_yaml(_manifest_path(project_dir), payload)


def _set_copier_answers_mirror(manifest: ExtensionManifest, answers_file: Path) -> None:
    if not answers_file.exists():
        raise ExtensionLifecycleError(f"Answers file not found while updating extension mirror: {answers_file}")

    answers = _load_yaml(answers_file)
    answers[MIRROR_KEY] = {
        "version": manifest.version,
        "extensions": [
            {
                "id": ext.id,
                "type": ext.type,
                "name": ext.name,
                "status": ext.status,
                "answers_file": ext.answers_file,
                "template_id": ext.template_id,
            }
            for ext in manifest.extensions
        ],
    }
    _dump_yaml(answers_file, answers)


def _upsert_instance(manifest: ExtensionManifest, instance: ExtensionInstance) -> ExtensionManifest:
    new_extensions: list[ExtensionInstance] = []
    replaced = False
    for ext in manifest.extensions:
        if ext.id == instance.id:
            new_extensions.append(instance)
            replaced = True
        else:
            new_extensions.append(ext)

    if not replaced:
        new_extensions.append(instance)

    return ExtensionManifest(version=manifest.version, extensions=new_extensions)


def _ensure_no_conflicting_instance(
    *,
    manifest: ExtensionManifest,
    extension_type: str,
    name: str,
    force: bool,
    singleton: bool,
) -> None:
    same_type = [ext for ext in manifest.extensions if ext.type == extension_type]
    same_id = [ext for ext in same_type if ext.name == name]

    if same_id and not force:
        raise ExtensionLifecycleError(
            f"Extension instance already exists for {extension_type}:{name}. Use --force to overwrite."
        )

    if singleton and same_type and all(ext.name != name for ext in same_type) and not force:
        existing = ", ".join(f"{ext.type}:{ext.name}" for ext in same_type)
        raise ExtensionLifecycleError(
            f"Only one {extension_type} extension is supported in v1. Existing: {existing}. Use --force to replace it."
        )


def _run_copy_or_raise(copier_options: dict[str, Any]) -> None:
    try:
        with Worker(**copier_options) as worker:
            worker.run_copy()
    except CopierError as e:
        raise ExtensionLifecycleError(str(e)) from e


def _create_extension_instance(
    *,
    project_dir: Path,
    base_answers_file: Path,
    template_dir: Path,
    extension_type: str,
    name: str,
    extension_data: dict[str, Any],
    singleton: bool,
    force: bool,
    dry_run: bool,
    expected_files: tuple[Path, Path],
) -> tuple[ExtensionInstance, dict[str, Any], Path, Path]:
    if not template_dir.exists():
        raise ExtensionLifecycleError(f"Extension template not found: {template_dir}")

    manifest = load_manifest(project_dir)
    _ensure_no_conflicting_instance(
        manifest=manifest,
        extension_type=extension_type,
        name=name,
        force=force,
        singleton=singleton,
    )

    extension_answers_file = _answers_path_for(project_dir, extension_type, name)

    copier_options: dict[str, Any] = {
        "src_path": str(template_dir),
        "dst_path": str(project_dir),
        "answers_file": str(extension_answers_file),
        "data": extension_data,
        "overwrite": force,
        "quiet": True,
        "unsafe": True,
    }

    instance = ExtensionInstance(
        id=f"{extension_type}:{name}",
        type=extension_type,
        name=name,
        status="active",
        answers_file=str(extension_answers_file.relative_to(project_dir)),
        template_id=extension_type,
        created_with_repoman_version=get_version(),
    )

    if not dry_run:
        _run_copy_or_raise(copier_options)
        _seed_extension_answers_file(extension_answers_file, template_dir, extension_data)
        updated_manifest = _upsert_instance(manifest, instance)
        save_manifest(project_dir, updated_manifest)
        _set_copier_answers_mirror(updated_manifest, base_answers_file)

    return instance, copier_options, expected_files[0], expected_files[1]


def create_command_extension(
    *,
    project_dir: Path,
    base_answers_file: Path,
    answers: dict[str, Any],
    command_name: str,
    force: bool,
    dry_run: bool,
) -> tuple[ExtensionInstance, dict[str, Any], Path, Path]:
    """Create a command extension instance and persist lifecycle metadata."""
    python_package_import_name = str(answers.get("python_package_import_name", "")).strip()
    if not python_package_import_name:
        raise ExtensionLifecycleError("Missing required answer: python_package_import_name")

    python_package_command_line_name = str(answers.get("python_package_command_line_name", python_package_import_name))
    command_description = str(answers.get("command_description", f"{command_name} command"))

    command_output_file = (
        project_dir / "src" / python_package_import_name / "cli" / "commands" / command_name / "__init__.py"
    )
    test_output_file = project_dir / "tests" / "test_cli" / f"test_{command_name}.py"

    extension_data = {
        "command_name": command_name,
        "command_description": command_description,
        "python_package_import_name": python_package_import_name,
        "python_package_command_line_name": python_package_command_line_name,
    }

    return _create_extension_instance(
        project_dir=project_dir,
        base_answers_file=base_answers_file,
        template_dir=_command_template_dir(),
        extension_type=EXTENSION_TYPE_COMMAND,
        name=command_name,
        extension_data=extension_data,
        singleton=False,
        force=force,
        dry_run=dry_run,
        expected_files=(command_output_file, test_output_file),
    )


def _template_dir_for_type(extension_type: str) -> Path:
    if extension_type == EXTENSION_TYPE_COMMAND:
        return _command_template_dir()
    raise ExtensionLifecycleError(f"Unsupported extension type: {extension_type}")


def sync_extensions(
    *,
    project_dir: Path,
    force: bool,
    conflict: str,
    dry_run: bool,
    extension_type: str | None = None,
    extension_name: str | None = None,
) -> ExtensionSyncResult:
    """Sync active extension instances to current bundled templates."""
    manifest = load_manifest(project_dir)
    if not manifest.extensions:
        return ExtensionSyncResult(synced=[], dry_run_options=[])

    synced: list[ExtensionInstance] = []
    dry_run_options: list[dict[str, Any]] = []

    for instance in manifest.extensions:
        if instance.status != "active":
            continue
        if extension_type is not None and instance.type != extension_type:
            continue
        if extension_name is not None and instance.name != extension_name:
            continue

        template_dir = _template_dir_for_type(instance.type)
        if not template_dir.exists():
            raise ExtensionLifecycleError(f"Extension template not found: {template_dir}")

        answers_file = project_dir / instance.answers_file
        if not answers_file.exists():
            raise ExtensionLifecycleError(f"Extension answers file is missing for {instance.id}: {answers_file}")

        copier_options: dict[str, Any] = {
            "src_path": str(template_dir),
            "dst_path": str(project_dir),
            "answers_file": str(answers_file),
            "overwrite": force,
            "quiet": True,
            "conflict": conflict,
            "unsafe": True,
        }

        if dry_run:
            dry_run_options.append(copier_options)
            synced.append(instance)
            continue

        try:
            with Worker(**copier_options) as worker:
                worker.run_update()
        except CopierError as e:
            raise ExtensionLifecycleError(str(e)) from e

        synced.append(instance)

    return ExtensionSyncResult(synced=synced, dry_run_options=dry_run_options)
