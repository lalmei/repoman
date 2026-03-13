"""Hotspot analysis for identifying refactoring candidates in git repositories."""

from repoman.hotspots.analysis import HotspotResult, find_hotspots
from repoman.hotspots.report import generate_report

__all__ = ["HotspotResult", "find_hotspots", "generate_report"]
