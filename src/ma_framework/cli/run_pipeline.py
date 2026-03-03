import json
from ma_framework.orchestration.pipeline import run_pipeline

def main():
    user_request = (
        "Build a Python module that validates email addresses.\n"
        "Expose validate_email(email: str) -> bool.\n"
        "Handle None/empty safely.\n"
        "Prefer a reasonable regex but avoid overly strict RFC complexity.\n"
        "Include docstring and a few usage examples."
    )

    result = run_pipeline(user_request, max_iters=3)
    print(json.dumps(result.model_dump(), indent=2))
    print(f"\nSaved run artifact: generated/runs/{result.run_id}.json")

if __name__ == "__main__":
    main()