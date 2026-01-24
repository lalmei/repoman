# Product Requirements Document: Repoman Project Generator

## Introduction/Overview

Repoman is a Python-based project template generator that leverages the copier library to create new projects from a comprehensive, customizable Jinja2 template. The system solves the problem of repetitive project setup by providing a standardized, feature-rich template that can generate complete Python project structures with modern development tooling, CI/CD pipelines, and documentation frameworks.

**Goal**: Create a robust, user-friendly CLI tool that generates production-ready Python projects with minimal user input, reducing setup time from hours to minutes while ensuring best practices and consistency across projects.

## Goals

1. **Automate Project Generation**: Reduce manual project setup time from 2-4 hours to under 5 minutes
2. **Ensure Consistency**: Provide standardized project structures that follow Python best practices
3. **Support Multiple Platforms**: Generate projects compatible with GitHub, GitLab, and Azure DevOps
4. **Modern Tooling Integration**: Include contemporary Python development tools (ruff, mypy, pytest, mkdocs)
5. **User Experience**: Create an intuitive CLI interface that guides users through project creation

## User Stories

**As a Python developer**, I want to quickly generate new projects with modern tooling so that I can focus on writing code instead of configuring build systems.

**As a team lead**, I want consistent project structures across our organization so that new team members can easily understand and contribute to any project.

**As an open-source maintainer**, I want to generate projects with proper CI/CD, documentation, and testing setup so that I can maintain high code quality standards.

**As a consultant**, I want to rapidly scaffold client projects with professional-grade tooling so that I can deliver value faster.

## Functional Requirements

1. **CLI Interface**: The system must provide a command-line interface accessible via `repoman` command
2. **Template Selection**: The system must use the main template located in `repoman/src/repoman/main_template/`
3. **Configuration Management**: The system must read and apply settings from `repoman/src/repoman/copier.yml`
4. **Project Customization**: The system must allow users to customize project name, description, author, and license
5. **CI/CD Generation**: The system must generate appropriate CI/CD configuration files based on selected platform (GitHub/GitLab/Azure)
6. **Python Package Setup**: The system must create proper `pyproject.toml` with modern Python tooling
7. **Documentation Framework**: The system must set up MkDocs with proper configuration and structure
8. **Testing Framework**: The system must configure pytest with coverage and quality tools
9. **Code Quality Tools**: The system must include ruff, mypy, and other linting/formatting tools
10. **Git Integration**: The system must initialize git repository with proper `.gitignore` and commit templates
11. **License Generation**: The system must generate appropriate license files from 30+ available options
12. **Template Extensions**: The system must support custom Jinja2 extensions for Git integration and slugification

## Non-Goals (Out of Scope)

- **Web Interface**: This will not include a web-based project generator
- **Non-Python Projects**: This will not generate projects for other programming languages
- **Database Integration**: This will not include database setup or configuration
- **Deployment Automation**: This will not handle actual deployment to cloud platforms
- **Real-time Collaboration**: This will not support multiple users editing the same project simultaneously
- **Version Control History**: This will not preserve or migrate existing project history

## Design Considerations

- **CLI Design**: Follow modern CLI design principles with clear prompts and help text
- **Template Structure**: Maintain the existing comprehensive template structure in `main_template/`
- **Configuration**: Use the existing `copier.yml` configuration format for consistency
- **Error Handling**: Provide clear error messages and recovery suggestions
- **Progress Indication**: Show progress during project generation for long operations

## Technical Considerations

- **Dependencies**: Must integrate with existing copier library and Jinja2 extensions
- **Python Version**: Target Python 3.12+ compatibility
- **Template Extensions**: Leverage existing custom extensions in `extensions.py`
- **File Generation**: Ensure proper file permissions and ownership for generated projects
- **Cross-platform**: Support Windows, macOS, and Linux environments
- **Git Integration**: Handle cases where git is not configured or available

## Success Metrics

- **Setup Time Reduction**: New projects can be generated in under 5 minutes (vs. 2-4 hours manually)
- **User Adoption**: At least 80% of generated projects follow the intended structure
- **Error Rate**: Less than 5% of project generations fail due to system issues
- **User Satisfaction**: Positive feedback from developers using the tool
- **Template Coverage**: 100% of template features are accessible through the CLI

## Open Questions

1. **Template Versioning**: How should we handle updates to the main template? Should users be able to update existing projects?
2. **Custom Templates**: Should users be able to create and use their own templates beyond the main one?
3. **Template Validation**: How should we validate that generated projects are functional and follow best practices?
4. **Integration Testing**: How should we test the template generation process to ensure quality?
5. **User Feedback**: What mechanism should we use to collect feedback and improve the template over time?
6. **Template Customization**: Should users be able to modify the template during generation, or only use predefined options?

## Implementation Priority

**Phase 1**: Core CLI functionality and basic project generation
**Phase 2**: Enhanced customization options and error handling
**Phase 3**: Template validation and quality assurance features
**Phase 4**: Advanced features and user experience improvements

