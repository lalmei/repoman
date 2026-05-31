"""Tests for the bundled C++ template."""

from pathlib import Path

from tests.template_testing import instantiate_template


def _read_text(path: Path) -> str:
    """Read a generated text file using UTF-8."""
    return path.read_text(encoding="utf-8")


def test_cpp_template_renders_spinach_style_structure(tmp_path: Path) -> None:
    """The C++ template should render the Meson/include/src/tests/examples shape."""
    template_path = Path(__file__).parent.parent.parent / "src" / "repoman" / "cpp_template"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        template_path=template_path,
        project_name="sample-cpp",
        copier_data={
            "ci": "github.com",
            "project_description": "Sample C++ library",
            "repository_provider": "github",
            "repository_namespace": "testuser",
            "repository_name": "sample-cpp",
            "author_username": "testuser",
            "author_fullname": "Test User",
            "author_email": "test@example.com",
            "copyright_holder": "Test User",
            "copyright_holder_email": "test@example.com",
            "copyright_date": "2025",
            "copyright_license": "MIT",
            "cpp_namespace": "sample_cpp",
            "cpp_library_name": "sample_cpp",
            "cpp_standard": "c++17",
            "cpp_build_cli": True,
            "cpp_build_examples": True,
            "cpp_build_tests": True,
            "cpp_build_python_bindings": True,
        },
    )

    assert (project_dir / "include" / "sample_cpp" / "sample_cpp.hpp").exists()
    assert (project_dir / "include" / "sample_cpp" / "version.hpp.in").exists()
    assert (project_dir / "src" / "sample_cpp.cpp").exists()
    assert (project_dir / "src" / "python_bindings.cpp").exists()
    assert (project_dir / "src" / "cli.cpp").exists()
    assert (project_dir / "tests" / "test_sample_cpp.cpp").exists()
    assert (project_dir / "tests" / "test_python_bindings.py").exists()
    assert (project_dir / "examples" / "basic.cpp").exists()
    assert (project_dir / "Doxyfile").exists()

    meson = _read_text(project_dir / "meson.build")
    meson_options = _read_text(project_dir / "meson_options.txt")
    makefile = _read_text(project_dir / "Makefile")
    mkdocs = _read_text(project_dir / "config" / "mkdocs.yml")
    pyproject = _read_text(project_dir / "pyproject.toml")
    github_ci = _read_text(project_dir / ".github" / "workflows" / "ci.yml")

    assert "subdir('include/sample_cpp')" in meson
    assert "'cpp_std=c++17'" in meson
    assert "python.extension_module(" in meson
    assert "dependency('pybind11')" in meson
    assert "option('build_python_bindings'" in meson_options
    assert '"pybind11>=2.13.6"' in pyproject
    assert "make check-docs" in github_ci
    assert "make check" in github_ci
    assert "make test" in github_ci
    assert 'site_url: "https://testuser.github.io/sample-cpp"' in mkdocs
    assert "MESON ?= uv run meson" in makefile
