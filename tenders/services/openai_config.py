import os
from urllib.parse import urlparse


DEFAULT_OPENAI_API_BASE = "https://api.openai.com/v1"
DEFAULT_OPENAI_USER_AGENT = "Mozilla/5.0 (compatible; Cebiao/1.0)"


def openai_responses_url():
    """Return the Responses API URL for OpenAI or a compatible relay."""
    base_url = os.getenv("OPENAI_API_BASE", DEFAULT_OPENAI_API_BASE).strip().rstrip("/")
    base_url = validated_https_api_base(base_url or DEFAULT_OPENAI_API_BASE, 'OPENAI_API_BASE')
    if base_url.endswith("/responses"):
        return base_url
    return f"{base_url}/responses"


def validated_https_api_base(value, setting_name='API base URL'):
    """Reject non-HTTPS, credential-bearing, or malformed outbound API endpoints."""
    parsed = urlparse(str(value or '').strip())
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError(f'{setting_name} must be a valid HTTPS URL without embedded credentials.')
    return str(value).strip().rstrip('/')


def openai_user_agent():
    return os.getenv("OPENAI_USER_AGENT", DEFAULT_OPENAI_USER_AGENT).strip() or DEFAULT_OPENAI_USER_AGENT
