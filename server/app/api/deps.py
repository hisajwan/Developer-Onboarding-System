"""Composition root: the only place concrete classes are chosen and wired together."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from app.agent.placeholder_agent import PlaceholderAgent
from app.agent.tools.registry import ToolRegistry
from app.core.config import Settings
from app.domain.ports import Agent
from app.services.chat_service import ChatService


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]


@lru_cache
def get_tool_registry() -> ToolRegistry:
    return ToolRegistry()


def get_agent(tools: Annotated[ToolRegistry, Depends(get_tool_registry)]) -> Agent:
    return PlaceholderAgent(tools)


def get_chat_service(agent: Annotated[Agent, Depends(get_agent)]) -> ChatService:
    return ChatService(agent)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
