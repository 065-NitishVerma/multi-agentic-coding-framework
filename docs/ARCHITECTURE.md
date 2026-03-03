# Architecture And Workflow

## Overview

The framework is organized as a linear orchestration pipeline with agent-generated artifacts flowing from one stage to the next. The pipeline is implemented in `src/ma_framework/orchestration/pipeline.py`.

## Core Components

### Agents

- `requirement_agent.py`
  Converts natural-language input into a structured requirements object.
- `test_agent.py`
  Produces a frozen pytest suite plus the module contract used by later stages.
- `coding_agent.py`
  Generates or repairs the Python module.
- `review_agent.py`
  Produces advisory review feedback about quality, edge cases, and maintainability.
- `documentation_agent.py`
  Produces Markdown documentation for the generated module.
- `deployment_agent.py`
  Produces a simple startup or deployment configuration artifact.

### Core Utilities

- `models.py`
  Defines the typed contracts exchanged between stages.
- `test_runner.py`
  Writes generated code and tests into a work directory and runs pytest.
- `artifacts.py`
  Creates run ids and saves final JSON artifacts.
- `json_utils.py`
  Parses JSON returned by agents.

### UI

- `app.py`
  A Streamlit interface for launching runs and browsing saved artifacts.

## Execution Flow

### 1. Requirements

The user request is passed to the Requirement Analysis Agent. The output is validated into a `Requirements` model.

### 2. Test Generation

The Test Case Generation Agent receives the original request and refined requirements. It returns:

- module filename
- module import name
- entrypoint
- pytest filename
- pytest source code

These tests are frozen for the rest of the run.

### 3. Code Generation Loop

The Coding Agent receives:

- requirements
- frozen tests
- previous feedback if any

The pipeline iterates until either:

- the code passes pytest and local quality checks, or
- `max_iters` is reached

### 4. Execution

The framework writes generated code and tests into `generated/work/<run_id>/` and runs pytest in that directory.

### 5. Local Quality Review

Before accepting the code, the pipeline performs a deterministic AST-based review that checks:

- the entrypoint exists
- the entrypoint has a docstring
- there is no obvious unreachable code after terminating statements

### 6. LLM Review

The Code Review Agent analyzes the accepted code and returns issues and suggestions. This stage is advisory and does not block completion once tests and local checks pass.

### 7. Documentation

The Documentation Agent receives the request, requirements, code, tests, and final review data, then generates a Markdown artifact.

### 8. Deployment Configuration

The Deployment Configuration Agent receives the validated outputs and generates a runnable deployment or startup script.

### 9. Artifact Persistence

The final run artifact is saved as JSON under `generated/runs/<run_id>.json`.

## Data Contracts

Important models in `models.py`:

- `Requirements`
- `CodePack`
- `TestPack`
- `ReviewResult`
- `DocumentationPack`
- `DeploymentPack`
- `PytestResult`
- `RunResult`

## Design Notes

- Tests are treated as the executable contract for a single run.
- Review is advisory because model reviewers can contradict passing tests.
- Documentation and deployment are generated only after code has been validated.
- The framework is artifact-driven: every major stage produces a typed output that can be rendered in the UI.

## Current Limitations

- Generated tests can still be wrong if the prompt is ambiguous.
- The Streamlit UI still needs minor polish in some labels.
- The framework has only focused tests so far, not full end-to-end coverage.
