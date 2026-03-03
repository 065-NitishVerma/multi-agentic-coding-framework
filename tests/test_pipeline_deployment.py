import json

from ma_framework.core.models import RunResult
from ma_framework.orchestration import pipeline


class StubAgent:
    def __init__(self, responses):
        self._responses = list(responses)
        self._index = 0

    def generate_reply(self, messages):
        if self._index < len(self._responses):
            response = self._responses[self._index]
            self._index += 1
            return response
        return self._responses[-1]


def test_run_pipeline_generates_deployment_configuration(monkeypatch):
    monkeypatch.setattr(pipeline, "new_run_id", lambda: "test-run-id")
    monkeypatch.setattr(
        pipeline,
        "build_requirement_agent",
        lambda: StubAgent(
            [
                json.dumps(
                    {
                        "problem": "Add two numbers.",
                        "inputs": ["a", "b"],
                        "outputs": ["integer"],
                        "constraints": [],
                        "edge_cases": [],
                        "acceptance_criteria": ["Returns the sum."],
                        "non_functional_requirements": [],
                    }
                )
            ]
        ),
    )
    monkeypatch.setattr(
        pipeline,
        "build_test_agent",
        lambda: StubAgent(
            [
                json.dumps(
                    {
                        "module_filename": "solution.py",
                        "module_import": "solution",
                        "entrypoint": "solve",
                        "filename": "test_solution.py",
                        "code": (
                            "import solution as s\n\n"
                            "def test_sum():\n"
                            "    assert s.solve(2, 3) == 5\n"
                        ),
                    }
                )
            ]
        ),
    )
    monkeypatch.setattr(
        pipeline,
        "build_coding_agent",
        lambda: StubAgent(
            [
                json.dumps(
                    {
                        "filename": "solution.py",
                        "code": (
                            "def solve(a, b):\n"
                            '    """Return the sum of two integers."""\n'
                            "    return a + b\n"
                        ),
                    }
                )
            ]
        ),
    )
    monkeypatch.setattr(
        pipeline,
        "build_review_agent",
        lambda: StubAgent(
            [
                json.dumps(
                    {
                        "approved": True,
                        "issues": [],
                        "suggestions": [],
                    }
                )
            ]
        ),
    )
    monkeypatch.setattr(
        pipeline,
        "build_documentation_agent",
        lambda: StubAgent(
            [
                json.dumps(
                    {
                        "filename": "DOCUMENTATION.md",
                        "content": "# Sum Module\n",
                    }
                )
            ]
        ),
    )
    monkeypatch.setattr(
        pipeline,
        "build_deployment_agent",
        lambda: StubAgent(
            [
                json.dumps(
                    {
                        "filename": "run.sh",
                        "content": (
                            "#!/usr/bin/env bash\n"
                            "set -euo pipefail\n"
                            "python -m pytest -q\n"
                            "python -c \"import solution; print(solution.solve(2, 3))\"\n"
                        ),
                    }
                )
            ]
        ),
    )

    def fake_run_pytest(**kwargs):
        return pipeline.PytestResult(
            passed=True,
            exit_code=0,
            stdout="1 passed",
            stderr="",
        )

    saved = {}

    monkeypatch.setattr(pipeline, "run_pytest", fake_run_pytest)
    monkeypatch.setattr(pipeline, "save_run", lambda run_id, payload: saved.setdefault(run_id, payload))

    result = pipeline.run_pipeline("Add two integers.", max_iters=2)

    assert isinstance(result, RunResult)
    assert result.deployment is not None
    assert result.deployment.filename == "run.sh"
    assert "pytest" in result.deployment.content
    assert saved["test-run-id"]["deployment"]["filename"] == "run.sh"
