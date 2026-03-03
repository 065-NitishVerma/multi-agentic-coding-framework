import json

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


def test_local_quality_review_rejects_missing_docstring():
    review = pipeline._local_quality_review(
        "def solve(a, b):\n    return a + b\n",
        "solve",
    )

    assert review.approved is False
    assert any("docstring" in issue.lower() for issue in review.issues)


def test_local_quality_review_rejects_unreachable_code():
    review = pipeline._local_quality_review(
        (
            "def solve(x):\n"
            '    """Return x."""\n'
            "    return x\n"
            "    x += 1\n"
        ),
        "solve",
    )

    assert review.approved is False
    assert any("unreachable" in issue.lower() for issue in review.issues)


def test_pipeline_keeps_llm_review_feedback_as_advisory(monkeypatch):
    monkeypatch.setattr(pipeline, "new_run_id", lambda: "advisory-run-id")
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
                        "approved": False,
                        "issues": ["Use a more explicit parameter validation strategy."],
                        "suggestions": ["Add input validation if the requirements demand it."],
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
                        "content": "#!/usr/bin/env bash\npython -m pytest -q\n",
                    }
                )
            ]
        ),
    )
    monkeypatch.setattr(
        pipeline,
        "run_pytest",
        lambda **kwargs: pipeline.PytestResult(
            passed=True,
            exit_code=0,
            stdout="1 passed",
            stderr="",
        ),
    )
    monkeypatch.setattr(pipeline, "save_run", lambda run_id, payload: payload)

    result = pipeline.run_pipeline("Add two integers.", max_iters=2)

    assert result.final_approved is True
    assert result.review.approved is True
    assert result.review.issues == []
    assert result.llm_review is not None
    assert result.llm_review.approved is False
    assert result.llm_review.issues == ["Use a more explicit parameter validation strategy."]
    assert result.note is not None
    assert "advisory" in result.note.lower()
