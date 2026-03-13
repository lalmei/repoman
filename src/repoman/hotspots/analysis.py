"""Hotspot analysis using PyDriller process metrics.

Pure logic module: no Typer, Rich, or CLI imports. Returns dataclasses.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from math import log
from pathlib import Path

from pydriller.metrics.process.code_churn import CodeChurn
from pydriller.metrics.process.commits_count import CommitsCount
from pydriller.metrics.process.contributors_count import ContributorsCount

DEFAULT_FILE_EXTENSIONS = (
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".rs",
    ".go",
    ".java",
    ".rb",
)


@dataclass
class HotspotResult:
    """A file identified as a potential refactoring hotspot."""

    file_path: str
    commits_count: int
    code_churn: int
    contributors_count: int
    score: float


def find_hotspots(
    repo_path: Path,
    *,
    since: datetime | None = None,
    to: datetime | None = None,
    from_commit: str | None = None,
    to_commit: str | None = None,
    file_extensions: list[str] | None = None,
) -> list[HotspotResult]:
    """Find code hotspots in a git repository using PyDriller process metrics.

    Hotspots are files with high change frequency, code churn, and contributor count—
    indicators of code that may benefit from refactoring.

    Parameters
    ----------
    repo_path : Path
        Path to the git repository to analyze.
    since : datetime | None
        Start of commit range (optional). Mutually exclusive with from_commit.
    to : datetime | None
        End of commit range (optional). Mutually exclusive with to_commit.
    from_commit : str | None
        Start commit hash (optional).
    to_commit : str | None
        End commit hash (optional).
    file_extensions : list[str] | None
        Only include files with these extensions (e.g. [".py"]). Default: common source extensions.

    Returns
    -------
    list[HotspotResult]
        Hotspots sorted by score descending.
    """
    path_str = str(repo_path.resolve())
    metric_kwargs = _build_metric_kwargs(since, to, from_commit, to_commit)

    code_churn_metric = CodeChurn(
        path_to_repo=path_str,
        add_deleted_lines_to_churn=True,  # sum(added + removed) for change intensity
        **metric_kwargs,
    )
    commits_metric = CommitsCount(path_to_repo=path_str, **metric_kwargs)
    contributors_metric = ContributorsCount(path_to_repo=path_str, **metric_kwargs)

    churn_by_file: dict[str, int] = code_churn_metric.count()
    commits_by_file: dict[str, int] = commits_metric.count()
    contributors_by_file: dict[str, int] = contributors_metric.count()

    extensions = tuple(file_extensions) if file_extensions is not None else DEFAULT_FILE_EXTENSIONS
    all_paths = set(churn_by_file) | set(commits_by_file) | set(contributors_by_file)

    results: list[HotspotResult] = []
    for file_path in all_paths:
        if file_path is None:
            continue
        if extensions and not file_path.lower().endswith(extensions):
            continue
        commits = commits_by_file.get(file_path, 0)
        churn = churn_by_file.get(file_path, 0)
        contributors = contributors_by_file.get(file_path, 0)
        score = _compute_score(commits, churn, contributors)
        results.append(
            HotspotResult(
                file_path=file_path,
                commits_count=commits,
                code_churn=churn,
                contributors_count=contributors,
                score=score,
            )
        )

    results.sort(key=lambda r: r.score, reverse=True)
    return results


def _build_metric_kwargs(
    since: datetime | None,
    to: datetime | None,
    from_commit: str | None,
    to_commit: str | None,
) -> dict[str, datetime | str]:
    """Build kwargs for PyDriller ProcessMetric. Full history if no range given."""
    if from_commit is not None and to_commit is not None:
        return {"from_commit": from_commit, "to_commit": to_commit}
    if since is not None or to is not None:
        return {
            "since": since if since is not None else datetime(1970, 1, 1, tzinfo=UTC),
            "to": to if to is not None else datetime.now(tz=UTC),
        }
    # Full history: use wide date range (PyDriller requires since/to or from_commit/to_commit)
    return {
        "since": datetime(1970, 1, 1, tzinfo=UTC),
        "to": datetime.now(tz=UTC),
    }


def _compute_score(commits_count: int, code_churn: int, contributors_count: int) -> float:
    """Compute a hotspot score for ranking. Higher = more likely to need refactoring."""
    churn_factor = log(1 + code_churn) if code_churn > 0 else 1.0
    contributors_factor = 1 + contributors_count / 10.0
    return commits_count * churn_factor * contributors_factor
