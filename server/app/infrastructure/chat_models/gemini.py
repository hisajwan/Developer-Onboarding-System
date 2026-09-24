"""The agent's tool-calling chat model on Gemini (main model + rate-limit fallback)."""

from langchain_core.runnables import Runnable

from app.core.config import Settings
from app.infrastructure.gemini.chat import build_gemini_chat


def create_gemini_chat_model(settings: Settings) -> Runnable:
    return build_gemini_chat(settings)
