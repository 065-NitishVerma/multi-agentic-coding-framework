from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from ma_framework.orchestration.pipeline import run_pipeline

RUNS_DIR = Path("generated") / "runs"


def _artifact_path(run_id: str) -> Path:
    return RUNS_DIR / f"{run_id}.json"


def _work_dir(run_id: str) -> Path:
    return Path("generated") / "work" / run_id


def _list_runs() -> list[str]:
    if not RUNS_DIR.exists():
        return []
    run_files = sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.stem for p in run_files]


def _load_run(run_id: str) -> dict[str, Any]:
    path = _artifact_path(run_id)
    return json.loads(path.read_text(encoding="utf-8"))


def _pretty_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def _safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _parse_run_time(run_id: str) -> str:
    try:
        dt = datetime.strptime(run_id, "%Y%m%dT%H%M%SZ")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return run_id


def _load_run_summary(run_id: str) -> dict[str, Any]:
    data = _load_run(run_id)

    approved = bool(data.get("final_approved", _safe_get(data, "review", "approved", default=False)))
    tests_obj = data.get("test_result")
    tests_passed = None if tests_obj is None else bool(tests_obj.get("passed", False))
    iterations = data.get("iterations", None)

    user_request = data.get("user_request")
    problem = _safe_get(data, "requirements", "problem", default="")
    prompt_text = (user_request or problem or "").strip()

    preview = " ".join(prompt_text.split())
    preview = (preview[:80] + "...") if len(preview) > 80 else preview

    test_status = "[tests ok]" if tests_passed is True else ("[tests failed]" if tests_passed is False else "[tests n/a]")
    review_status = "[review ok]" if approved else "[review not ok]"

    label = f"{test_status} {review_status}  {_parse_run_time(run_id)}  |  iters={iterations}  |  {preview}"

    return {
        "run_id": run_id,
        "label": label,
        "approved": approved,
        "tests_passed": tests_passed,
        "iterations": iterations,
        "preview": preview.lower(),
    }


def _load_all_summaries() -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for rid in _list_runs():
        try:
            summaries.append(_load_run_summary(rid))
        except Exception:
            continue
    return summaries


def _render_run(run_data: dict[str, Any]) -> None:
    run_id = run_data.get("run_id", "unknown")

    approved = bool(run_data.get("final_approved", _safe_get(run_data, "review", "approved", default=False)))
    tr = run_data.get("test_result", None)
    tests_passed = None if tr is None else bool(tr.get("passed", False))
    llm_review_obj = run_data.get("llm_review", None)
    llm_review_approved = None if not llm_review_obj else bool(llm_review_obj.get("approved", False))

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Run ID", run_id)
    c2.metric("Iterations", str(run_data.get("iterations", "")))
    c3.metric("Tests", "passed" if tests_passed is True else ("failed" if tests_passed is False else "n/a"))
    c4.metric("Final", "approved" if approved else "not approved")
    c5.metric(
        "LLM review",
        "approved" if llm_review_approved is True else ("not approved" if llm_review_approved is False else "n/a"),
    )

    st.caption(f"Work directory (code/tests executed here): `{_work_dir(run_id)}`")
    st.divider()

    tabs = st.tabs(["Requirements", "Code", "Documentation", "Deployment", "Tests", "Pytest output", "Review", "Raw artifact"])

    with tabs[0]:
        st.subheader("Requirements (JSON)")
        st.code(_pretty_json(run_data.get("requirements", {})), language="json")

    with tabs[1]:
        st.subheader("Generated code")
        code_obj = run_data.get("code", {}) or {}
        module_filename = code_obj.get("filename", "module.py")
        module_code = code_obj.get("code", "")

        st.caption(module_filename)
        st.code(module_code, language="python")

        if module_code:
            st.download_button(
                label="Download module",
                data=module_code.encode("utf-8"),
                file_name=module_filename,
                mime="text/x-python",
                key=f"dl_module_{run_id}_{module_filename}",
            )

    with tabs[2]:
        st.subheader("Generated documentation")
        documentation_obj = run_data.get("documentation", None)

        if not documentation_obj:
            st.info("No documentation found in this run.")
        else:
            doc_filename = documentation_obj.get("filename", "DOCUMENTATION.md")
            doc_content = documentation_obj.get("content", "")

            st.caption(doc_filename)
            st.code(doc_content, language="markdown")

            if doc_content:
                st.download_button(
                    label="Download documentation",
                    data=doc_content.encode("utf-8"),
                    file_name=doc_filename,
                    mime="text/markdown",
                    key=f"dl_docs_{run_id}_{doc_filename}",
                )

    with tabs[3]:
        st.subheader("Deployment configuration")
        deployment_obj = run_data.get("deployment", None)

        if not deployment_obj:
            st.info("No deployment configuration found in this run.")
        else:
            deploy_filename = deployment_obj.get("filename", "run.sh")
            deploy_content = deployment_obj.get("content", "")

            st.caption(deploy_filename)
            st.code(deploy_content, language="bash")

            if deploy_content:
                st.download_button(
                    label="Download deployment config",
                    data=deploy_content.encode("utf-8"),
                    file_name=deploy_filename,
                    mime="text/x-shellscript",
                    key=f"dl_deploy_{run_id}_{deploy_filename}",
                )

    with tabs[4]:
        st.subheader("Generated tests")
        tests_obj = run_data.get("tests", None)

        if not tests_obj:
            st.info("No tests found in this run.")
        else:
            test_filename = tests_obj.get("filename", "test_module.py")
            test_code = tests_obj.get("code", "")

            st.caption(test_filename)
            st.code(test_code, language="python")

            if test_code:
                st.download_button(
                    label="Download tests",
                    data=test_code.encode("utf-8"),
                    file_name=test_filename,
                    mime="text/x-python",
                    key=f"dl_tests_{run_id}_{test_filename}",
                )

    with tabs[5]:
        st.subheader("Pytest output")
        if not tr:
            st.info("No pytest result found in this run.")
        else:
            st.write(f"Passed: **{tr.get('passed')}** | Exit code: `{tr.get('exit_code')}`")
            st.text_area("stdout", value=tr.get("stdout", ""), height=180, key=f"stdout_{run_id}")
            st.text_area("stderr", value=tr.get("stderr", ""), height=120, key=f"stderr_{run_id}")

    with tabs[6]:
        st.subheader("Review")
        rev = run_data.get("review", {}) or {}
        st.write(f"Final approved: **{run_data.get('final_approved', rev.get('approved', False))}**")

        st.write("Final review issues:")
        st.code(_pretty_json(rev.get("issues", [])), language="json")

        st.write("Final review suggestions:")
        st.code(_pretty_json(rev.get("suggestions", [])), language="json")

        llm_rev = run_data.get("llm_review", None)
        if llm_rev:
            st.write(f"LLM review approved: **{llm_rev.get('approved', False)}**")
            st.write("LLM review issues:")
            st.code(_pretty_json(llm_rev.get("issues", [])), language="json")
            st.write("LLM review suggestions:")
            st.code(_pretty_json(llm_rev.get("suggestions", [])), language="json")

    with tabs[7]:
        st.subheader("Raw artifact JSON")
        st.code(_pretty_json(run_data), language="json")

        st.download_button(
            label="Download run artifact JSON",
            data=_pretty_json(run_data).encode("utf-8"),
            file_name=f"{run_id}.json",
            mime="application/json",
            key=f"dl_artifact_{run_id}",
        )


def main() -> None:
    st.set_page_config(page_title="Multi-Agent Framework Demo", layout="wide")
    st.title("Multi-Agent Framework (Requirements -> Code -> Tests -> Review)")

    with st.sidebar:
        st.header("Run History")

        q = st.text_input("Search", placeholder="type a keyword from your prompt...").strip().lower()

        status_filter = st.multiselect(
            "Filter",
            options=["Approved", "Not approved", "Tests passed", "Tests failed", "No tests"],
            default=[],
        )

        sort_mode = st.selectbox(
            "Sort",
            options=["Newest first", "Oldest first", "Most iterations"],
            index=0,
        )

        if st.button("Refresh"):
            st.rerun()

        st.divider()
        st.caption("Artifacts directory:")
        st.code(str(RUNS_DIR), language="text")

        summaries = _load_all_summaries()

        if q:
            summaries = [s for s in summaries if q in s["preview"]]

        def _match_filters(s: dict[str, Any]) -> bool:
            if not status_filter:
                return True
            approved = s["approved"]
            tests_passed = s["tests_passed"]

            ok = True
            for f in status_filter:
                if f == "Approved":
                    ok = ok and approved is True
                elif f == "Not approved":
                    ok = ok and approved is False
                elif f == "Tests passed":
                    ok = ok and tests_passed is True
                elif f == "Tests failed":
                    ok = ok and tests_passed is False
                elif f == "No tests":
                    ok = ok and tests_passed is None
            return ok

        summaries = [s for s in summaries if _match_filters(s)]

        if sort_mode == "Oldest first":
            summaries = list(reversed(summaries))
        elif sort_mode == "Most iterations":
            summaries.sort(key=lambda s: (s["iterations"] or 0), reverse=True)

        st.subheader("Runs")

        selected_run_id = None
        if not summaries:
            st.info("No runs found (or none match your filters).")
        else:
            label_to_id = {s["label"]: s["run_id"] for s in summaries}
            selected_label = st.radio(
                "Select a run",
                options=list(label_to_id.keys()),
                index=0,
                label_visibility="collapsed",
            )
            selected_run_id = label_to_id[selected_label]

            if st.button("Open selected run", type="secondary"):
                st.session_state["current_run_id"] = selected_run_id
                st.rerun()

    st.subheader("User request")
    default_prompt = (
        "Build a Python module that validates email addresses.\n"
        "Expose validate_email(email: str) -> bool.\n"
        "Handle None/empty safely.\n"
        "Prefer a reasonable regex but avoid overly strict RFC complexity.\n"
        "Include docstring and a few usage examples."
    )
    user_request = st.text_area("Prompt", value=default_prompt, height=160)

    max_iters = st.slider("Max iterations", min_value=1, max_value=10, value=3)

    run_btn = st.button("Run pipeline", type="primary")

    if run_btn:
        if not user_request.strip():
            st.error("Please enter a request.")
            st.stop()

        with st.spinner("Running pipeline... (agents + pytest)"):
            result = run_pipeline(user_request, max_iters=max_iters)

        st.session_state["current_run_id"] = result.run_id
        st.success(f"Done. Run ID: {result.run_id}")
        st.rerun()

    current = st.session_state.get("current_run_id")
    if current:
        try:
            run_data = _load_run(current)
            st.info(f"Showing run: {current}")
            _render_run(run_data)
            st.caption(f"Saved: {_artifact_path(current)}")
        except Exception as e:
            st.error(f"Failed to load run artifact: {e}")


if __name__ == "__main__":
    main()
