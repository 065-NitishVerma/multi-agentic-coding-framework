# Multi-Agent Framework Documentation

## Overview

This project implements a multi-agent coding framework in Python using AutoGen. The system accepts a natural-language software request and processes it through a structured pipeline that generates requirements, tests, code, review feedback, documentation, and deployment configuration.

The framework is designed around typed artifacts and a sequential orchestration flow. Each major stage produces structured output that feeds into the next stage.

## Implemented Agents

### Requirement Analysis Agent

- Input: natural-language user request
- Output: structured software requirements
- Responsibility: convert the prompt into a normalized requirement object with problem summary, inputs, outputs, constraints, edge cases, and acceptance criteria

### Test Case Generation Agent

- Input: user request and structured requirements
- Output: frozen pytest suite plus module contract
- Responsibility: define the expected entrypoint, module filename, and executable tests for the generated code

### Coding Agent

- Input: structured requirements, frozen tests, and prior feedback
- Output: Python module
- Responsibility: generate or repair code until it satisfies the executable contract

### Code Review Agent

- Input: generated code and requirements
- Output: structured review result
- Responsibility: provide quality feedback on correctness, readability, edge cases, and maintainability
- Note: the raw LLM review is currently advisory after tests and local quality checks pass

### Documentation Agent

- Input: request, requirements, code, tests, and review context
- Output: markdown documentation artifact
- Responsibility: describe the generated module, API, approach, usage, and testing summary

### Deployment Configuration Agent

- Input: request, requirements, code, tests, and documentation
- Output: deployment or startup script artifact
- Responsibility: produce a simple, reproducible run/deployment configuration for the generated code

## Workflow And Architecture

## High-Level Flow

1. The user submits a natural-language request.
2. The Requirement Analysis Agent produces structured requirements.
3. The Test Case Generation Agent creates a frozen pytest suite and module contract.
4. The Coding Agent generates code.
5. The framework runs pytest against the generated code.
6. A deterministic local AST quality check validates structural quality.
7. The Code Review Agent produces advisory review feedback.
8. The Documentation Agent generates markdown documentation.
9. The Deployment Configuration Agent generates a runnable deployment/startup artifact.
10. The final run artifact is saved to disk and displayed in the Streamlit UI.

## Runtime Architecture

### Orchestration Layer

- File: `src/ma_framework/orchestration/pipeline.py`
- Role: coordinates agents, validation, retries, pytest execution, and artifact creation

### Core Layer

- `src/ma_framework/core/models.py`
  Defines the typed contracts exchanged between stages
- `src/ma_framework/core/test_runner.py`
  Writes generated code and tests into a work directory and runs pytest
- `src/ma_framework/core/artifacts.py`
  Creates run ids and saves final run artifacts
- `src/ma_framework/core/json_utils.py`
  Parses strict JSON returned by agents

### Agent Layer

- `src/ma_framework/agents/requirement_agent.py`
- `src/ma_framework/agents/test_agent.py`
- `src/ma_framework/agents/coding_agent.py`
- `src/ma_framework/agents/review_agent.py`
- `src/ma_framework/agents/documentation_agent.py`
- `src/ma_framework/agents/deployment_agent.py`

Each agent is implemented as an AutoGen `AssistantAgent` with a strict system prompt and JSON-based contract.

### UI Layer

- File: `src/ma_framework/ui/app.py`
- Role: lets users run the pipeline and inspect generated artifacts including code, tests, documentation, deployment config, and review output

## Artifact Model

The pipeline persists a final JSON artifact for each run containing:

- user request
- final approval state
- requirements
- generated code
- generated tests
- generated documentation
- generated deployment configuration
- pytest result
- final review summary
- raw LLM review output
- iteration count

Artifacts are stored under:

- `generated/runs/<run_id>.json`
- `generated/work/<run_id>/`

## How To Set Up And Run The System

## Prerequisites

- Python 3.11
- A valid API key for a supported LLM provider
- PowerShell or another shell environment capable of running Python and Streamlit

## Installation

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file in the repository root.

### OpenAI Example

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o-mini
```

### Groq Example

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your-key
GROQ_MODEL=llama-3.1-8b-instant
```

## Run The CLI Pipeline

```powershell
$env:PYTHONPATH='src'
.\venv\Scripts\python.exe -m ma_framework.cli.run_pipeline
```

This runs the pipeline against the sample request in the CLI entrypoint and writes a run artifact to `generated/runs/`.

## Run The Streamlit UI

```powershell
$env:PYTHONPATH='src'
.\venv\Scripts\streamlit.exe run src\ma_framework\ui\app.py
```

The UI allows you to:

- submit a new request
- choose max iterations
- inspect prior runs
- view generated code, tests, documentation, deployment configuration, and review output

## Run Framework Tests

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='src'
.\venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
```

## Current Notes

- Tests are the main executable contract within a run.
- The LLM review is stored separately from final framework approval.
- Documentation and deployment artifacts are generated only after the code passes execution and local quality checks.
