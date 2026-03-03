import os
from dotenv import load_dotenv

load_dotenv()

def get_str(name: str, default: str | None = None) -> str:
    v = os.getenv(name, default)
    if v is None or v.strip() == "":
        raise ValueError(f"Missing required env var: {name}")
    return v

def llm_config():
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        api_key = get_str("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return {
            "config_list": [
                {
                    "model": model,
                    "api_key": api_key,
                }
            ],
            "temperature": 0.2,
        }

    if provider == "groq":
        api_key = get_str("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        print(f"[llm_config] provider={provider} model={model}")
        return {
            "config_list": [
                {
                    "model": model,
                    "api_key": api_key,
                    "base_url": "https://api.groq.com/openai/v1",
                }
            ],
            "temperature": 0.2,
        }

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")