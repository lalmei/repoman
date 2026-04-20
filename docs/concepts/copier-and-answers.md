# Copier and answers

Repoman uses **Copier** to generate projects. Copier asks questions, stores your answers, and renders the template files with those answers.

## Prompts and answers

When you run `repoman create` or `repoman update`, the prompts you see come from the template configuration: project metadata, CI choice, optional FastAPI support, optional dataset support, and related settings. Your responses are the **answers**.

## Where answers are stored

Answers are saved in `.copier-answers.yml` in the generated project. That file is reused by `repoman update` and can also be edited for non-interactive runs.

## Internal Copier keys

Besides prompt answers, `.copier-answers.yml` may contain Copier metadata such as:

- `_src_path`
- `_commit`
- `_vcs_ref`

Those values let Copier understand which template revision was previously used.
