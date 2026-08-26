"""
Centralized LLM model factory for Nova multi-agent system.
Supports OpenRouter, Anthropic Claude, OpenAI, and graceful mock fallback.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel

from nova.config import get_settings

logger = logging.getLogger(__name__)


def get_chat_model(
    temperature: float = 0.1,
    max_tokens: int = 4096,
    model_override: Optional[str] = None,
) -> Optional[BaseChatModel]:
    """
    Instantiate and return a configured ChatModel instance.
    Checks OpenRouter -> Anthropic -> OpenAI in priority order.
    Returns None if only mock/dummy keys are configured.
    """
    settings = get_settings()

    # 1. Check OpenRouter
    or_key_raw = getattr(settings, "openrouter_api_key", None)
    if or_key_raw:
        or_key = (
            or_key_raw.get_secret_value()
            if hasattr(or_key_raw, "get_secret_value")
            else str(or_key_raw)
        ).strip()
        if or_key and "mock" not in or_key and "test" not in or_key:
            try:
                from langchain_openai import ChatOpenAI

                model_name = (
                    model_override
                    or getattr(settings, "openrouter_model", "")
                    or "openai/gpt-4o-mini"
                )
                base_url = getattr(settings, "openrouter_base_url", "https://openrouter.ai/api/v1")

                logger.info("Initializing LLM via OpenRouter (model=%s)", model_name)
                return ChatOpenAI(
                    model=model_name,
                    api_key=or_key,
                    base_url=base_url,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    request_timeout=25.0,
                )
            except Exception as exc:
                logger.warning("Failed to initialize OpenRouter LLM: %s", exc)

    # 2. Check Anthropic
    ant_key_raw = getattr(settings, "anthropic_api_key", None)
    if ant_key_raw:
        ant_key = (
            ant_key_raw.get_secret_value()
            if hasattr(ant_key_raw, "get_secret_value")
            else str(ant_key_raw)
        ).strip()
        if ant_key and "mock" not in ant_key and "test" not in ant_key:
            try:
                from langchain_anthropic import ChatAnthropic

                logger.info("Initializing LLM via Anthropic Claude")
                return ChatAnthropic(
                    model_name="claude-3-5-sonnet-20241022",
                    anthropic_api_key=ant_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as exc:
                logger.warning("Failed to initialize Anthropic LLM: %s", exc)

    # 3. Check OpenAI
    oai_key_raw = getattr(settings, "openai_api_key", None)
    if oai_key_raw:
        oai_key = (
            oai_key_raw.get_secret_value()
            if hasattr(oai_key_raw, "get_secret_value")
            else str(oai_key_raw)
        ).strip()
        if oai_key and "mock" not in oai_key and "test" not in oai_key:
            try:
                from langchain_openai import ChatOpenAI

                logger.info("Initializing LLM via OpenAI")
                return ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=oai_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as exc:
                logger.warning("Failed to initialize OpenAI LLM: %s", exc)

    logger.debug("No live LLM provider configured; using deterministic mock fallback.")
    return None
