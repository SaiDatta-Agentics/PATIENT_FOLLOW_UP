import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def azure_ai_reply(system_prompt: str, user_prompt: str):
    """Return an Azure OpenAI reply when available; fail open to deterministic clinic-safe logic."""
    if not settings.AZURE_OPENAI_ENDPOINT or not settings.AZURE_OPENAI_KEY:
        return None
    try:
        from openai import AsyncAzureOpenAI
        client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            timeout=12.0,
            max_retries=1,
        )
        response = await client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = response.choices[0].message.content if response.choices else None
        return text.strip() if text else None
    except Exception as exc:
        logger.warning("Azure OpenAI unavailable; using deterministic fallback: %s", exc)
        return None
