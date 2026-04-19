"""Built-in compliance profile definitions."""

from __future__ import annotations

from repoman.compliance.models import ControlDefinition, ControlProfile, DetectorSpec


def _manual(prompt: str) -> DetectorSpec:
    return DetectorSpec("manual_only", {"prompt": prompt})


SOC2_SOFTWARE = ControlProfile(
    profile_id="soc2-software",
    title="SOC 2 Software Readiness",
    description="Software-only SOC 2 style controls for product engineering, platform, and DevOps teams.",
    disclaimer="This report is an engineering readiness check, not a SOC 2 certification or audit opinion.",
    controls=(
        ControlDefinition(
            "soc2.architecture.docs",
            "scope-and-architecture",
            "Document system architecture",
            "Document in-scope services, dependencies, and data flows.",
            "bronze",
            DetectorSpec(
                "glob_exists",
                {
                    "patterns": [
                        "ARCHITECTURE.md",
                        "docs/architecture.md",
                        "docs/reference/architecture.md",
                        "docs/**/*architecture*.md",
                        "docs/**/*system-design*.md",
                        "docs/**/*data-flow*.md",
                    ]
                },
            ),
            "Architecture or system design documentation.",
        ),
        ControlDefinition(
            "soc2.environments.separation",
            "scope-and-architecture",
            "Define environment separation",
            "Development, staging, and production separation should be documented.",
            "bronze",
            _manual("Document environment separation in compliance.yml."),
            "Manual confirmation of environment boundaries.",
        ),
        ControlDefinition(
            "soc2.sdlc.pull_requests",
            "secure-development",
            "Require pull requests or peer review",
            "Significant software changes should be reviewed before merge.",
            "bronze",
            DetectorSpec("text_match", {"path": "CONTRIBUTING.md", "pattern": "pull request"}),
            "Contribution guidance or review policy.",
        ),
        ControlDefinition(
            "soc2.sdlc.ci-before-merge",
            "secure-development",
            "Require CI checks before merge",
            "Protected branches should rely on automated CI before change integration.",
            "bronze",
            DetectorSpec("glob_exists", {"pattern": ".github/workflows/*.y*ml"}),
            "CI workflow definition.",
        ),
        ControlDefinition(
            "soc2.dependencies.visibility",
            "code-security",
            "Maintain visibility into dependencies",
            "The repo should declare its primary libraries or runtime components.",
            "bronze",
            DetectorSpec("pyproject_field_exists", {"field_path": ["project", "dependencies"]}),
            "Dependency manifest.",
        ),
        ControlDefinition(
            "soc2.cicd.secrets-manager",
            "build-and-cicd-security",
            "Store deploy secrets in approved secret storage",
            "Build and deploy secrets should not be committed or stored in plaintext configs.",
            "silver",
            _manual("Declare the approved secrets manager and owner in compliance.yml."),
            "Manual evidence of secrets manager and ownership.",
        ),
        ControlDefinition(
            "soc2.cicd.deploy-logging",
            "build-and-cicd-security",
            "Log build and deployment activity",
            "Release activity should leave auditable traces.",
            "silver",
            DetectorSpec("glob_exists", {"pattern": ".github/workflows/*.y*ml"}),
            "Deployment workflow or release automation.",
        ),
        ControlDefinition(
            "soc2.app.rate-limiting",
            "application-security",
            "Protect exposed endpoints from abuse",
            "Rate limiting or other abuse protections should exist for exposed services.",
            "silver",
            _manual("Document endpoint abuse protections or explain why they are not applicable."),
            "Manual evidence of rate limiting or compensating controls.",
        ),
        ControlDefinition(
            "soc2.logging.security-events",
            "logging-monitoring-and-detection",
            "Log security-relevant events",
            "Authentication, authorization failures, admin actions, and config changes should be logged.",
            "silver",
            _manual("Document which security-relevant events are logged and where."),
            "Manual logging evidence.",
        ),
        ControlDefinition(
            "soc2.operations.rollback",
            "change-management",
            "Maintain rollback procedures",
            "Risky releases should have rollback or mitigation guidance.",
            "gold",
            DetectorSpec(
                "glob_exists",
                {
                    "patterns": [
                        "RUNBOOK.md",
                        "docs/**/*rollback*.md",
                        "docs/**/*runbook*.md",
                        "docs/**/*incident*.md",
                    ]
                },
            ),
            "Runbook or release rollback docs.",
        ),
        ControlDefinition(
            "soc2.incident.response",
            "incident-handling",
            "Maintain security incident process",
            "Software and security incidents should follow a documented response path.",
            "gold",
            DetectorSpec("glob_exists", {"patterns": ["SECURITY.md", "docs/**/*incident*.md"]}),
            "Incident response or security documentation.",
        ),
        ControlDefinition(
            "soc2.vuln.remediation-slas",
            "vulnerability-handling",
            "Define vulnerability remediation SLAs",
            "Severity-based remediation timeframes should be documented.",
            "gold",
            _manual("Record remediation SLAs or justified exceptions in compliance.yml."),
            "Manual vulnerability SLA evidence.",
        ),
    ),
)


OSS_BEST_PRACTICES = ControlProfile(
    profile_id="oss-best-practices",
    title="OSS Best Practices",
    description="Open source repository signals inspired by OpenSSF best practices and badge-style maturity tiers.",
    disclaimer="This report is best-practices inspired and intentionally narrower than the full bestpractices.dev criteria set.",
    controls=(
        ControlDefinition(
            "oss.docs.readme",
            "basics",
            "Project description is documented",
            "A user-facing README should explain what the project does.",
            "bronze",
            DetectorSpec("file_exists", {"path": "README.md"}),
            "README.md",
        ),
        ControlDefinition(
            "oss.docs.contributing",
            "basics",
            "Contribution process is documented",
            "The repo should explain how contributors submit changes.",
            "bronze",
            DetectorSpec("file_exists", {"path": "CONTRIBUTING.md"}),
            "CONTRIBUTING.md",
        ),
        ControlDefinition(
            "oss.license.present",
            "basics",
            "License file exists",
            "A project license should be present.",
            "bronze",
            DetectorSpec("glob_exists", {"patterns": ["LICENSE", "LICENSE.*"]}),
            "License file.",
        ),
        ControlDefinition(
            "oss.ci.automation",
            "quality",
            "CI automation exists",
            "The project should run automated checks in CI.",
            "bronze",
            DetectorSpec("glob_exists", {"pattern": ".github/workflows/*.y*ml"}),
            "Workflow files.",
        ),
        ControlDefinition(
            "oss.tests.documented",
            "quality",
            "Automated tests are present",
            "A test suite or documented test command should exist.",
            "bronze",
            DetectorSpec("make_target_exists", {"target": "test"}),
            "Makefile test target.",
        ),
        ControlDefinition(
            "oss.security.policy",
            "security",
            "Security reporting path exists",
            "The repo should publish a security contact or reporting policy.",
            "silver",
            DetectorSpec("glob_exists", {"patterns": ["SECURITY.md", ".github/SECURITY.md"]}),
            "Security policy file.",
        ),
        ControlDefinition(
            "oss.releases.changelog",
            "release-hygiene",
            "Release history or changelog exists",
            "Users should be able to see what changed between releases.",
            "silver",
            DetectorSpec("glob_exists", {"patterns": ["CHANGELOG.md", "docs/**/*changelog*.md"]}),
            "Changelog or release notes.",
        ),
        ControlDefinition(
            "oss.security.scanning",
            "security",
            "Repository scans dependencies or code",
            "At least one automated security or dependency scan should be configured.",
            "silver",
            DetectorSpec(
                "glob_exists",
                {
                    "patterns": [
                        ".github/workflows/*codeql*.y*ml",
                        ".github/workflows/*dependabot*.y*ml",
                        ".github/workflows/*dependency-review*.y*ml",
                        ".github/workflows/*trivy*.y*ml",
                        ".github/workflows/*sast*.y*ml",
                    ]
                },
            ),
            "Security scanning workflow.",
        ),
        ControlDefinition(
            "oss.security.scanning-declared",
            "security",
            "Security scanning declared",
            "Document the active scanning tool and workflow if auto-detection is not yet specific enough.",
            "silver",
            _manual("Declare the scanning workflow or tool in compliance.yml."),
            "Manual scanning evidence.",
        ),
        ControlDefinition(
            "oss.community.code-of-conduct",
            "community",
            "Code of conduct exists",
            "Contributor expectations should be documented.",
            "gold",
            DetectorSpec("file_exists", {"path": "CODE_OF_CONDUCT.md"}),
            "Code of conduct file.",
        ),
        ControlDefinition(
            "oss.release.provenance",
            "release-hygiene",
            "Release provenance is documented",
            "Projects should document how consumers verify release integrity or provenance.",
            "gold",
            _manual("Document release provenance, signing, or verification instructions."),
            "Manual provenance evidence.",
        ),
        ControlDefinition(
            "oss.release.verification-docs",
            "release-hygiene",
            "Verification instructions are published",
            "Users should be told how to verify release artifacts when applicable.",
            "gold",
            _manual("Provide verification instructions or justify why not applicable."),
            "Manual verification guidance evidence.",
        ),
    ),
)

BUILTIN_PROFILES: dict[str, ControlProfile] = {
    SOC2_SOFTWARE.profile_id: SOC2_SOFTWARE,
    OSS_BEST_PRACTICES.profile_id: OSS_BEST_PRACTICES,
}
