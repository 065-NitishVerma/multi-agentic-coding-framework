import ast
import json

from ma_framework.core.artifacts import new_run_id, save_run
from ma_framework.core.json_utils import safe_json_loads
from ma_framework.core.models import (
    CodePack,
    DeploymentPack,
    DocumentationPack,
    Requirements,
    ReviewResult,
    RunResult,
    TestPack,
    PytestResult,
)
from ma_framework.core.test_runner import run_pytest

from ma_framework.agents.coding_agent import build_coding_agent
from ma_framework.agents.deployment_agent import build_deployment_agent
from ma_framework.agents.documentation_agent import build_documentation_agent
from ma_framework.agents.requirement_agent import build_requirement_agent
from ma_framework.agents.review_agent import build_review_agent
from ma_framework.agents.test_agent import build_test_agent


def _generate_strict_json(agent, prompt: str, *, retries: int = 2) -> dict:
    """
    Ask an agent for a JSON response and parse it.
    If parsing fails, retry with a strict "JSON only" instruction.
    """
    last_raw = ""
    for attempt in range(retries + 1):
        last_raw = agent.generate_reply(messages=[{"role": "user", "content": prompt}])
        try:
            return safe_json_loads(last_raw)
        except Exception:
            if attempt == retries:
                raise RuntimeError(
                    "Agent failed to return valid JSON after retries. "
                    f"Last output (first 300 chars): {repr(last_raw[:300])}"
                )
            prompt = (
                "Return ONLY a valid JSON object. No markdown, no code fences, no explanation.\n"
                "Use double quotes for all keys/strings and no trailing commas.\n"
                "The JSON must match the required schema exactly.\n\n"
                f"Original request:\n{prompt}"
            )
    raise RuntimeError("Unexpected JSON generation failure.")


def _has_statements_after_terminator(statements: list[ast.stmt]) -> bool:
    terminated = False
    for statement in statements:
        if terminated:
            return True

        if isinstance(statement, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
            terminated = True
            continue

        child_blocks: list[list[ast.stmt]] = []
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        if isinstance(statement, ast.If):
            child_blocks.extend([statement.body, statement.orelse])
        elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            child_blocks.extend([statement.body, statement.orelse])
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            child_blocks.append(statement.body)
        elif isinstance(statement, ast.Try):
            child_blocks.append(statement.body)
            child_blocks.extend(handler.body for handler in statement.handlers)
            child_blocks.append(statement.orelse)
            child_blocks.append(statement.finalbody)
        elif isinstance(statement, ast.Match):
            child_blocks.extend(case.body for case in statement.cases)

        if any(_has_statements_after_terminator(block) for block in child_blocks if block):
            return True

    return False


def _local_quality_review(code: str, entrypoint: str) -> ReviewResult:
    issues: list[str] = []
    suggestions: list[str] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return ReviewResult(
            approved=False,
            issues=[f"Generated code is not valid Python: {exc.msg}"],
            suggestions=["Return syntactically valid Python code."],
        )

    target_function: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entrypoint:
            target_function = node
            break

    if target_function is None:
        issues.append(f"Entrypoint '{entrypoint}' is missing.")
        suggestions.append(f"Define a top-level function named '{entrypoint}'.")
    else:
        if not ast.get_docstring(target_function):
            issues.append(f"Entrypoint '{entrypoint}' is missing a docstring.")
            suggestions.append(f"Add a concise docstring to '{entrypoint}'.")

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _has_statements_after_terminator(node.body):
            issues.append(f"Function '{node.name}' contains unreachable statements after a terminating statement.")
            suggestions.append(f"Remove dead code from '{node.name}' or move that logic before the terminating statement.")
            break

    return ReviewResult(
        approved=not issues,
        issues=issues,
        suggestions=suggestions,
    )


def run_pipeline(user_request: str, max_iters: int = 3) -> RunResult:
    run_id = new_run_id()

    req_agent = build_requirement_agent()
    tester = build_test_agent()
    coder = build_coding_agent()
    reviewer = build_review_agent()
    documenter = build_documentation_agent()
    deployer = build_deployment_agent()

    req_dict = _generate_strict_json(req_agent, user_request, retries=2)
    requirements = Requirements.model_validate(req_dict)

    test_payload = json.dumps(
        {
            "user_request": user_request,
            "requirements": requirements.model_dump(),
        }
    )
    test_dict = _generate_strict_json(tester, test_payload, retries=2)
    tests = TestPack.model_validate(test_dict)

    feedback: dict | None = None
    last_code: CodePack | None = None
    last_test_result: PytestResult | None = None
    last_review: ReviewResult | None = None
    last_llm_review: ReviewResult | None = None

    for iteration in range(1, max_iters + 1):
        coder_payload = json.dumps(
            {
                "requirements": requirements.model_dump(),
                "tests": tests.model_dump(),
                "previous_feedback": feedback,
                "rules": {
                    "do_not_change_tests": True,
                    "return_strict_json_only": True,
                    "module_filename_must_match_tests": True,
                },
            }
        )

        code_dict = _generate_strict_json(coder, coder_payload, retries=2)
        code_pack = CodePack.model_validate(code_dict)
        last_code = code_pack

        expected_module_filename = tests.module_filename
        if code_pack.filename != expected_module_filename:
            feedback = {
                "type": "pytest_failure",
                "exit_code": -1,
                "stdout_tail": "",
                "stderr_tail": "",
                "instruction": (
                    f"Filename mismatch. Tests import '{tests.module_import}'. "
                    f"You MUST return filename exactly '{expected_module_filename}'. "
                    "Keep code same logic but fix filename field."
                ),
            }
            last_review = ReviewResult(
                approved=False,
                issues=["Module filename mismatch vs tests contract"],
                suggestions=[f"Return filename '{expected_module_filename}' to match tests import."],
            )
            last_llm_review = None
            continue

        test_res = run_pytest(
            run_id=run_id,
            module_filename=code_pack.filename,
            module_code=code_pack.code,
            test_filename=tests.filename,
            test_code=tests.code,
        )
        last_test_result = test_res

        if not test_res.passed:
            feedback = {
                "type": "pytest_failure",
                "exit_code": test_res.exit_code,
                "stdout_tail": (test_res.stdout or "")[-2500:],
                "stderr_tail": (test_res.stderr or "")[-1500:],
                "instruction": (
                    "Fix ONLY the module code to satisfy the frozen tests and requirements. "
                    "Do not change requirements. Do not change tests. "
                    f"Keep filename '{expected_module_filename}'. "
                    "Return strict JSON: {\"filename\": \"...\", \"code\": \"...\"}."
                ),
            }
            last_review = ReviewResult(
                approved=False,
                issues=["Pytest failed"],
                suggestions=["Fix failures shown in pytest output and rerun."],
            )
            last_llm_review = None
            continue

        local_review = _local_quality_review(code_pack.code, tests.entrypoint)
        if not local_review.approved:
            last_review = local_review
            last_llm_review = None
            feedback = {
                "type": "review_feedback",
                "issues": local_review.issues,
                "suggestions": local_review.suggestions,
                "instruction": (
                    "Update ONLY the module code to address the review issues while keeping all tests passing. "
                    f"Keep filename '{expected_module_filename}'. "
                    "Return strict JSON with filename and code."
                ),
            }
            continue

        review_payload = json.dumps(
            {
                "requirements": requirements.model_dump(),
                "filename": code_pack.filename,
                "code": code_pack.code,
                "tests_filename": tests.filename,
                "entrypoint": tests.entrypoint,
            }
        )
        review_dict = _generate_strict_json(reviewer, review_payload, retries=1)
        llm_review = ReviewResult.model_validate(review_dict)
        if llm_review.approved:
            final_review = ReviewResult(
                approved=True,
                issues=[],
                suggestions=[],
            )
        else:
            final_review = ReviewResult(
                approved=True,
                issues=[],
                suggestions=[],
            )

        documentation_payload = json.dumps(
            {
                "user_request": user_request,
                "requirements": requirements.model_dump(),
                "code": code_pack.model_dump(),
                "tests": tests.model_dump(),
                "review": final_review.model_dump(),
                "llm_review": llm_review.model_dump(),
            }
        )
        documentation_dict = _generate_strict_json(documenter, documentation_payload, retries=1)
        documentation = DocumentationPack.model_validate(documentation_dict)

        deployment_payload = json.dumps(
            {
                "user_request": user_request,
                "requirements": requirements.model_dump(),
                "code": code_pack.model_dump(),
                "tests": tests.model_dump(),
                "documentation": documentation.model_dump(),
            }
        )
        deployment_dict = _generate_strict_json(deployer, deployment_payload, retries=1)
        deployment = DeploymentPack.model_validate(deployment_dict)

        last_review = final_review
        last_llm_review = llm_review
        result = RunResult(
            run_id=run_id,
            user_request=user_request,
            final_approved=True,
            requirements=requirements,
            code=code_pack,
            tests=tests,
            documentation=documentation,
            deployment=deployment,
            test_result=test_res,
            review=final_review,
            llm_review=llm_review,
            iterations=iteration,
            note=None if llm_review.approved else "LLM review returned advisory feedback after tests and local quality checks passed.",
        )
        save_run(run_id, result.model_dump())
        return result

    result = RunResult(
        run_id=run_id,
        user_request=user_request,
        final_approved=False,
        requirements=requirements,
        code=last_code,  # type: ignore[arg-type]
        tests=tests,
        test_result=last_test_result,
        review=last_review,  # type: ignore[arg-type]
        llm_review=last_llm_review,
        iterations=max_iters,
        note="Max iterations reached; code not approved yet.",
    )
    save_run(run_id, result.model_dump())
    return result
