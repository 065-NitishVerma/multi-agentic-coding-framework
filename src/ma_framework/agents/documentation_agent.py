from autogen import AssistantAgent

from ma_framework.config.settings import llm_config

SYSTEM_MESSAGE = """You are a Documentation Agent in a deterministic multi-agent pipeline.

Your job is to produce concise, structured Markdown documentation for the generated Python module.

INPUT (JSON):
{
  "user_request": "string",
  "requirements": { ... },
  "code": {
    "filename": "string",
    "code": "string"
  },
  "tests": {
    "filename": "string",
    "entrypoint": "string",
    "code": "string"
  } | null,
  "review": {
    "approved": true/false,
    "issues": ["string"],
    "suggestions": ["string"]
  }
}

OUTPUT (STRICT JSON ONLY):
{
  "filename": "string",
  "content": "string"
}

CRITICAL RULES:
- Return ONLY valid JSON. No markdown fences. No extra prose.
- The "content" value must be valid JSON string content with escaped newlines.
- Output Markdown in "content".
- Default filename: "DOCUMENTATION.md".

DOCUMENTATION MUST INCLUDE:
- Title
- Problem overview
- Module/API summary
- Function definitions / entrypoint
- Approach summary
- Usage example
- Testing summary
- Review notes if any suggestions exist

Keep the documentation clear and compact.
"""


def build_documentation_agent() -> AssistantAgent:
    return AssistantAgent(
        name="documentation_agent",
        llm_config=llm_config(),
        system_message=SYSTEM_MESSAGE,
    )
