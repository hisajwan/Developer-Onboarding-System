"""The agent's tool-calling chat model on Groq (ChatGroq supports `bind_tools` natively)."""

from langchain_core.runnables import Runnable

from app.core.config import Settings
from app.infrastructure.groq.chat import build_groq_chat


def create_groq_chat_model(settings: Settings) -> Runnable:
    return build_groq_chat(settings)
