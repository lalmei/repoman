"""Unit tests for repoman.hotspots analysis module."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from repoman.hotspots import HotspotResult, find_hotspots, generate_report


@patch("repoman.hotspots.analysis.ContributorsCount")
@patch("repoman.hotspots.analysis.CommitsCount")
@patch("repoman.hotspots.analysis.CodeChurn")
def test_find_hotspots_merges_and_sorts(
    mock_code_churn_cls: MagicMock,
    mock_commits_cls: MagicMock,
    mock_contributors_cls: MagicMock,
    tmp_path: Path,
) -> None:
    """find_hotspots merges metrics from all three and sorts by score descending."""
    mock_code_churn_cls.return_value.count.return_value = {
        "src/foo.py": 500,
        "src/bar.py": 10,
    }
    mock_commits_cls.return_value.count.return_value = {
        "src/foo.py": 15,
        "src/bar.py": 2,
    }
    mock_contributors_cls.return_value.count.return_value = {
        "src/foo.py": 3,
        "src/bar.py": 1,
    }

    results = find_hotspots(tmp_path, file_extensions=[".py"])

    assert len(results) == 2
    # foo has higher commits, churn, contributors -> higher score
    assert results[0].file_path == "src/foo.py"
    assert results[0].commits_count == 15
    assert results[0].code_churn == 500
    assert results[0].contributors_count == 3
    assert results[1].file_path == "src/bar.py"
    assert results[0].score >= results[1].score


@patch("repoman.hotspots.analysis.ContributorsCount")
@patch("repoman.hotspots.analysis.CommitsCount")
@patch("repoman.hotspots.analysis.CodeChurn")
def test_find_hotspots_filters_by_extensions(
    mock_code_churn_cls: MagicMock,
    mock_commits_cls: MagicMock,
    mock_contributors_cls: MagicMock,
    tmp_path: Path,
) -> None:
    """find_hotspots filters files by extension when file_extensions is set."""
    mock_code_churn_cls.return_value.count.return_value = {
        "src/foo.py": 100,
        "src/bar.ts": 50,
        "README.md": 20,
    }
    mock_commits_cls.return_value.count.return_value = {
        "src/foo.py": 5,
        "src/bar.ts": 5,
        "README.md": 3,
    }
    mock_contributors_cls.return_value.count.return_value = {
        "src/foo.py": 1,
        "src/bar.ts": 1,
        "README.md": 1,
    }

    results = find_hotspots(tmp_path, file_extensions=[".py"])

    paths = [r.file_path for r in results]
    assert "src/foo.py" in paths
    assert "src/bar.ts" not in paths
    assert "README.md" not in paths


@patch("repoman.hotspots.analysis.ContributorsCount")
@patch("repoman.hotspots.analysis.CommitsCount")
@patch("repoman.hotspots.analysis.CodeChurn")
def test_find_hotspots_passes_date_range(
    mock_code_churn_cls: MagicMock,
    mock_commits_cls: MagicMock,
    mock_contributors_cls: MagicMock,
    tmp_path: Path,
) -> None:
    """find_hotspots passes since/to to PyDriller metrics."""
    mock_code_churn_cls.return_value.count.return_value = {}
    mock_commits_cls.return_value.count.return_value = {}
    mock_contributors_cls.return_value.count.return_value = {}

    since = datetime(2024, 1, 1, tzinfo=UTC)
    to = datetime(2024, 6, 1, tzinfo=UTC)
    find_hotspots(tmp_path, since=since, to=to)

    mock_code_churn_cls.assert_called_once()
    call_kwargs = mock_code_churn_cls.call_args[1]
    assert call_kwargs["since"] == since
    assert call_kwargs["to"] == to


@patch("repoman.hotspots.analysis.ContributorsCount")
@patch("repoman.hotspots.analysis.CommitsCount")
@patch("repoman.hotspots.analysis.CodeChurn")
def test_find_hotspots_skips_none_file_paths(
    mock_code_churn_cls: MagicMock,
    mock_commits_cls: MagicMock,
    mock_contributors_cls: MagicMock,
    tmp_path: Path,
) -> None:
    """find_hotspots skips None keys that PyDriller may return for deleted files."""
    mock_code_churn_cls.return_value.count.return_value = {
        "src/foo.py": 10,
        None: 5,  # type: ignore[dict-item]
    }
    mock_commits_cls.return_value.count.return_value = {
        "src/foo.py": 2,
        None: 1,  # type: ignore[dict-item]
    }
    mock_contributors_cls.return_value.count.return_value = {
        "src/foo.py": 1,
        None: 1,  # type: ignore[dict-item]
    }

    results = find_hotspots(tmp_path, file_extensions=[".py"])

    assert len(results) == 1
    assert results[0].file_path == "src/foo.py"


def test_generate_report_creates_index_and_file_pages(tmp_path: Path) -> None:
    """generate_report creates index.html and per-file HTML pages."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "foo.py").write_text("print('hello')\n")
    out = tmp_path / "report"
    results = [
        HotspotResult(
            file_path="src/foo.py",
            commits_count=10,
            code_churn=100,
            contributors_count=2,
            score=50.0,
        ),
    ]

    generate_report(results, repo, out)

    assert (out / "index.html").exists()
    index_content = (out / "index.html").read_text()
    assert "Hotspot Report" in index_content
    assert "src/foo.py" in index_content
    assert "10" in index_content
    file_page = out / "src_foo.py.html"
    assert file_page.exists()
    file_content = file_page.read_text()
    assert "src/foo.py" in file_content
    assert "hello" in file_content  # source code is HTML-escaped


def test_hotspot_result_dataclass() -> None:
    """HotspotResult has expected fields."""
    r = HotspotResult(
        file_path="a/b.py",
        commits_count=5,
        code_churn=100,
        contributors_count=2,
        score=12.5,
    )
    assert r.file_path == "a/b.py"
    assert r.commits_count == 5
    assert r.code_churn == 100
    assert r.contributors_count == 2
    assert r.score == 12.5
