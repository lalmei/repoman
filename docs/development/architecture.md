# Create and config architecture

This page describes how the **create** command and **config validate** flow are structured: the CLI layer delegates to two core modules, `repoman.copier` (template and copy operations) and `repoman.config` (project configuration and answers loading).

## Summary diagram

The diagram shows how the create group, its subcommands, and config validate use the shared modules.

```mermaid
flowchart LR
  subgraph CLI
    create_init[create/__init__.py]
    create_shared[_shared run_create]
    create_sub[create cli/docs/library/...]
    config_validate[config validate]
  end
  subgraph repoman_copier[repoman.copier]
    validate_name[validate_project_name]
    presets[PRESETS build_preset_data]
    build_opts[build_copier_options]
    schema[load_prompt_schema validate_answers]
  end
  subgraph repoman_config[repoman.config]
    load_answers[load_answers]
    validate_file[validate_answers_file]
  end
  create_init -->|"if no subcommand"| create_shared
  create_init -->|"if subcommand"| create_sub
  create_shared --> validate_name
  create_shared --> presets
  create_shared --> build_opts
  create_sub --> create_shared
  config_validate --> load_answers
  config_validate --> validate_file
  validate_file --> load_answers
  validate_file --> schema
```

- **repoman.copier**: Template schema, validation (answers vs schema), presets, and options for running Copier (`validate_project_name`, `build_preset_data`, `build_copier_options`, `load_prompt_schema`, `validate_answers`).
- **repoman.config**: Loading the project’s answers file (`load_answers`) and optional orchestration such as `validate_answers_file` (load + schema + validate).
- **Create**: When no subcommand is given, the create callback runs the default flow via `run_create`; when a subcommand is used (e.g. `create cli`), only that subcommand runs, and it calls `run_create` with the right preset.
