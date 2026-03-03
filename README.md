# Multi-Agent Framework

A Python multi-agent coding framework built with AutoGen. The system takes a natural-language software task, refines it into structured requirements, generates tests, writes Python code, validates the result with pytest, produces review feedback, generates documentation, and emits a deployment script.

Primary submission documentation:

- [Project Documentation](C:/Users/Lenovo/Desktop/multi_agent_framework/docs/PROJECT_DOCUMENTATION.md)
- [Architecture](C:/Users/Lenovo/Desktop/multi_agent_framework/docs/ARCHITECTURE.md)

## Implemented Agents

- Requirement Analysis Agent
- Test Case Generation Agent
- Coding Agent
- Code Review Agent
- Documentation Agent
- Deployment Configuration Agent

## Workflow

1. The user enters a natural-language request.
2. The Requirement Analysis Agent converts the prompt into a structured requirement object.
3. The Test Case Generation Agent produces a frozen pytest suite and module contract.
4. The Coding Agent generates Python code to satisfy the requirements and tests.
5. The framework runs pytest against the generated code.
6. A local structural quality check validates the entrypoint and catches dead code patterns.
7. The Code Review Agent produces advisory review feedback.
8. The Documentation Agent generates Markdown documentation for the code artifact.
9. The Deployment Configuration Agent generates a runnable deployment or startup script.
10. The framework saves the final run artifact under `generated/runs/`.

## Project Structure

```text
src/ma_framework/
  agents/          Agent builders and prompts
  cli/             CLI entrypoints
  config/          LLM provider configuration
  core/            Shared models, artifact helpers, pytest runner
  orchestration/   Pipeline orchestration
  ui/              Streamlit application
tests/             Framework-level tests
generated/         Run artifacts and generated work directories
```

## Setup

### Prerequisites

- Python 3.11
- An API key for a supported provider
- Windows PowerShell or another shell that can run Python and Streamlit

### Install

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file in the repository root.

OpenAI example:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o-mini
```

Groq example:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your-key
GROQ_MODEL=llama-3.1-8b-instant
```

## Running the Project

### Run the CLI demo

```powershell
$env:PYTHONPATH='src'
.\venv\Scripts\python.exe -m ma_framework.cli.run_pipeline
```

### Run the Streamlit UI

```powershell
$env:PYTHONPATH='src'
.\venv\Scripts\streamlit.exe run src\ma_framework\ui\app.py
```

## Running Tests

Run framework tests:

```powershell
$env:PYTHONPATH='src'
.\venv\Scripts\python.exe -m pytest tests -q
```

Generated solution tests are executed automatically by the pipeline inside `generated/work/<run_id>/`.

## Artifacts

Each successful run can produce:

- structured requirements
- generated code
- generated tests
- pytest execution result
- review feedback
- generated documentation
- generated deployment configuration

Saved artifacts are written to:

- `generated/runs/<run_id>.json`
- `generated/work/<run_id>/`

## Notes

- LLM review is currently advisory after tests and local quality checks pass.
- Generated tests are frozen during a run and act as the main executable contract.
- The Streamlit UI shows artifacts for previous runs and allows downloads.

## Additional Documentation

- [Project Documentation](C:/Users/Lenovo/Desktop/multi_agent_framework/docs/PROJECT_DOCUMENTATION.md)
- [Architecture](C:/Users/Lenovo/Desktop/multi_agent_framework/docs/ARCHITECTURE.md)
