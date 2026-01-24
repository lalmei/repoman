# PRD: Critical Priority Template Enhancements

## Overview

This PRD defines the critical priority enhancements needed for the repoman template to provide basic functionality for FastAPI applications. These are blocking issues that prevent the template from generating functional FastAPI projects.

## Problem Statement

The current repoman template lacks essential components for FastAPI applications:
1. Missing `config.py` module that logging system depends on
2. No FastAPI application structure or routing
3. No Docker configuration for containerization
4. Template generates broken projects that cannot run

## Goals

### Primary Goals
- Generate functional FastAPI applications that can start and serve requests
- Provide proper configuration management with environment variable support
- Include Docker containerization for development and deployment
- Ensure generated projects follow FastAPI best practices

### Success Metrics
- Generated projects start successfully with `uv run fastapi dev`
- Configuration loads from environment variables
- Docker containers build and run without errors
- Basic API endpoints respond correctly

## User Stories

### As a Developer
- I want to generate a FastAPI project that starts immediately
- I want configuration to be loaded from environment variables
- I want to run the application in Docker for consistency
- I want proper project structure following FastAPI conventions

### As a DevOps Engineer
- I want Docker images that build reliably
- I want configuration that works across environments
- I want applications that start and stop gracefully

## Requirements

### Functional Requirements

#### FR1: Configuration Management
- **FR1.1**: Generate `config.py` module with Pydantic Settings
- **FR1.2**: Support environment variable loading (.env files)
- **FR1.3**: Include common FastAPI settings (host, port, debug, etc.)
- **FR1.4**: Validate configuration on startup

#### FR2: FastAPI Application Structure
- **FR2.1**: Generate `main.py` with FastAPI app instance
- **FR2.2**: Create basic router structure (`api/v1/`)
- **FR2.3**: Include health check endpoint (`/health`)
- **FR2.4**: Add CORS middleware configuration
- **FR2.5**: Include request/response logging middleware

#### FR3: Docker Configuration
- **FR3.1**: Generate `Dockerfile` with multi-stage build
- **FR3.2**: Include `docker-compose.yml` for development
- **FR3.3**: Add `.dockerignore` file
- **FR3.4**: Support both development and production builds

### Non-Functional Requirements

#### NFR1: Performance
- Application should start within 5 seconds
- Docker build should complete within 3 minutes

#### NFR2: Reliability
- Generated projects should have 100% startup success rate
- Configuration validation should prevent runtime errors

#### NFR3: Maintainability
- Code should follow FastAPI best practices
- Configuration should be easily extensible

## Technical Specifications

### Configuration Module Structure
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "{{ project_name }}"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### FastAPI Application Structure
```
src/{{python_package_import_name}}/
├── main.py                 # FastAPI app instance
├── config.py              # Configuration management
├── api/
│   └── v1/
│       ├── __init__.py
│       ├── health.py      # Health check endpoint
│       └── router.py      # Main API router
└── middleware/
    ├── __init__.py
    └── logging.py         # Request/response logging
```

### Docker Configuration
```dockerfile
# Multi-stage Dockerfile
FROM python:3.12-slim as builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

FROM python:3.12-slim as runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
CMD ["python", "-m", "{{python_package_import_name}}"]
```

## Implementation Plan

### Phase 1: Configuration Management (Week 1)
1. Create `config.py.jinja` template
2. Add environment variable support
3. Update logging to use configuration
4. Test configuration loading

### Phase 2: FastAPI Structure (Week 2)
1. Create `main.py.jinja` template
2. Generate API router structure
3. Add health check endpoint
4. Configure middleware

### Phase 3: Docker Integration (Week 3)
1. Create `Dockerfile.jinja` template
2. Generate `docker-compose.yml.jinja`
3. Add `.dockerignore.jinja`
4. Test Docker builds

### Phase 4: Integration Testing (Week 4)
1. Test complete project generation
2. Verify FastAPI startup
3. Test Docker containerization
4. Validate configuration loading

## Acceptance Criteria

### Configuration Management
- [ ] `config.py` module generated with Pydantic Settings
- [ ] Environment variables loaded from `.env` file
- [ ] Configuration validation on startup
- [ ] Logging system uses configuration

### FastAPI Application
- [ ] `main.py` creates FastAPI app instance
- [ ] Health check endpoint responds at `/health`
- [ ] CORS middleware configured
- [ ] Request/response logging works
- [ ] Application starts with `uv run fastapi dev`

### Docker Configuration
- [ ] `Dockerfile` builds successfully
- [ ] `docker-compose.yml` starts application
- [ ] Container responds to health checks
- [ ] Multi-stage build optimizes image size

### Integration
- [ ] Generated project starts without errors
- [ ] All endpoints respond correctly
- [ ] Configuration loads from environment
- [ ] Docker container runs application

## Risks and Mitigation

### Risk 1: Configuration Complexity
- **Risk**: Too many configuration options overwhelm users
- **Mitigation**: Start with essential settings, add more gradually

### Risk 2: Docker Compatibility
- **Risk**: Docker builds fail on different platforms
- **Mitigation**: Test on multiple platforms, use multi-stage builds

### Risk 3: FastAPI Version Compatibility
- **Risk**: Template breaks with FastAPI updates
- **Mitigation**: Pin major versions, test with latest releases

## Dependencies

### Internal Dependencies
- Template system must support conditional file generation
- Jinja2 extensions for configuration templating
- Copier configuration updates

### External Dependencies
- FastAPI >= 0.115.6
- Pydantic Settings >= 2.7.1
- Docker and docker-compose
- uv for Python package management

## Timeline

- **Week 1**: Configuration management implementation
- **Week 2**: FastAPI application structure
- **Week 3**: Docker configuration
- **Week 4**: Integration testing and validation

**Total Duration**: 4 weeks

## Success Criteria

The critical priority enhancements are successful when:
1. Generated FastAPI projects start successfully
2. Configuration management works across environments
3. Docker containers build and run reliably
4. Basic API functionality is available out-of-the-box
5. Projects follow FastAPI best practices

This PRD provides the foundation for functional FastAPI applications generated by repoman.