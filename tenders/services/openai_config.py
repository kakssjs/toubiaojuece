import os


DEFAULT_OPENAI_API_BASE = "https://api.openai.com/v1"


def openai_responses_url():
    """Return the Responses API URL for OpenAI or a compatible relay."""
    base_url = os.getenv("OPENAI_API_BASE", DEFAULT_OPENAI_API_BASE).strip().rstrip("/")
    if not base_url:
        base_url = DEFAULT_OPENAI_API_BASE
    if base_url.endswith("/responses"):
        return base_url
    return f"{base_url}/responses"
