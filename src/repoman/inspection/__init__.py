"""Repository inspection exports."""

from repoman.inspection.analysis import InspectionError, inspect_repository
from repoman.inspection.models import (
    AnswersFileState,
    ExtensionState,
    ExtensionSummary,
    FeatureFlags,
    InspectionReport,
    TemplateMetadata,
    UpdateReadiness,
)

__all__ = [
    "AnswersFileState",
    "ExtensionState",
    "ExtensionSummary",
    "FeatureFlags",
    "InspectionError",
    "InspectionReport",
    "TemplateMetadata",
    "UpdateReadiness",
    "inspect_repository",
]
