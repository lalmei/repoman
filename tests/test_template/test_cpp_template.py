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
    python_bindings = _read_text(project_dir / "src" / "python_bindings.cpp")
    python_bindings_test = _read_text(project_dir / "tests" / "test_python_bindings.py")
    readme = _read_text(project_dir / "README.md")
    github_ci = _read_text(project_dir / ".github" / "workflows" / "ci.yml")

    assert "subdir('include/sample_cpp')" in meson
    assert "'cpp_std=c++17'" in meson
    assert "python.extension_module(" in meson
    assert "dependency('pybind11')" in meson
    assert "install_tag: 'runtime'" in meson
    assert "install_tag: 'bin'" in meson
    assert "install_tag: 'python-runtime'" in meson
    assert "option('build_python_bindings'" in meson_options
    assert 'build-backend = "mesonpy"' in pyproject
    assert 'name = "sample-cpp"' in pyproject
    assert 'description = "Sample C++ library"' in pyproject
    assert '"meson-python>=0.17.0"' in pyproject
    assert '"pybind11>=2.13.6"' in pyproject
    assert 'install = ["--tags=runtime,python-runtime"]' in pyproject
    assert 'module.attr("__version__") = sample_cpp::version();' in python_bindings
    assert "module.add(2, 3) == 5" in python_bindings_test
    assert 'module.version() == "0.1.0"' in python_bindings_test
    assert 'module.__version__ == "0.1.0"' in python_bindings_test
    assert "assert module.__doc__" in python_bindings_test
    assert "except TypeError:" in python_bindings_test
    assert "PYTHONPATH=build uv run python" in readme
    assert "make check-wheel" in readme
    assert "uv build --wheel" in makefile
    assert "uv pip install --python" in makefile
    assert "make check-docs" in github_ci
    assert "make check" in github_ci
    assert "make test" in github_ci
    assert 'site_url: "https://testuser.github.io/sample-cpp"' in mkdocs
    assert "MESON ?= uv run meson" in makefile
