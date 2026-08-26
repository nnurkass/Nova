"""
Government Procurement Agent (Гос. Закупщик).

Searches goszakup.gov.kz, scores tenders, selects the optimal tender lot,
and delegates technical specification analysis to the PTO agent.
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage

from nova.agents.level2.procurement.prompts import PROCUREMENT_SYSTEM_PROMPT
from nova.agents.level3.goszakup_tool import (
    analyze_tender,
    download_tender_docs,
    goszakup_search,
    score_tender,
)
from nova.agents.level3.tender_scorer import score_tender as calculate_score
from nova.config import get_settings
from nova.graph.routers import ROUTE_PTO
from nova.graph.state import ConstructionState
from nova.integrations.goszakup.client import GoszakupClient

logger = logging.getLogger(__name__)

PROCUREMENT_TOOLS = [
    goszakup_search,
    analyze_tender,
    score_tender,
    download_tender_docs,
]


def create_procurement_agent():
    """Create a LangChain ReAct agent for Procurement when Anthropic LLM is available."""
    try:
        from langchain_anthropic import ChatAnthropic
        from langgraph.prebuilt import create_react_agent

        settings = get_settings()
        api_key = settings.anthropic_api_key.get_secret_value() if hasattr(settings.anthropic_api_key, "get_secret_value") else str(settings.anthropic_api_key)
        if not api_key or "mock" in api_key or "test" in api_key:
            return None

        llm = ChatAnthropic(
            model_name="claude-3-5-sonnet-20241022",
            anthropic_api_key=api_key,
            temperature=0.1,
            max_tokens=4096,
        )
        return create_react_agent(llm, PROCUREMENT_TOOLS, prompt=PROCUREMENT_SYSTEM_PROMPT)
    except Exception as exc:
        logger.debug("Live LLM agent initialization skipped: %s", exc)
        return None


def run_procurement_agent(state: ConstructionState) -> dict[str, Any]:
    """Execute Procurement agent logic with Graceful Fallback / Mock-first."""
    task = state.get("task", "")
    metadata = dict(state.get("metadata", {}))
    visited = list(metadata.get("visited_nodes", []))
    visited.append("procurement")
    metadata["visited_nodes"] = visited

    # If live agent is configured, try executing it
    agent = create_procurement_agent()
    if agent is not None:
        try:
            result = agent.invoke({"messages": state.get("messages", [])})
            logger.info("Procurement agent executed via live LLM")
            # Extract state changes if available
        except Exception as exc:
            logger.warning("Procurement LLM call failed, falling back to deterministic mode: %s", exc)

    # Deterministic / Mock-First Execution
    task_lower = task.lower()
    target_region_name = None
    region_stems = {
        "алмат": "Алматы",
        "астан": "Астана",
        "нур-султан": "Астана",
        "шымкент": "Шымкент",
        "караганд": "Караганда",
        "актобе": "Актобе",
        "атырау": "Атырау",
        "актау": "Актау",
    }
    for stem, reg_val in region_stems.items():
        if stem in task_lower:
            target_region_name = reg_val
            break

    client = GoszakupClient()
    tenders = client.search_tenders(query=task, region_name=target_region_name, limit=5)

    if not tenders:
        tenders = client.search_tenders(query="", limit=3)

    # Score all candidate tenders
    scored_tenders = []
    for t in tenders:
        s = calculate_score(t, target_region_name=target_region_name)
        scored_tenders.append((t, s))

    # Sort by total score descending
    scored_tenders.sort(key=lambda item: item[1].total_score, reverse=True)
    best_tender, best_score = scored_tenders[0] if scored_tenders else (None, None)

    summary_msg = (
        f"[ЗАКУПЩИК] Найдено {len(tenders)} тендеров на goszakup.gov.kz. "
        f"Выбран наиболее перспективный лот: №{best_tender.number} "
        f"«{best_tender.name_ru}» на сумму {best_tender.total_sum:,.2f} KZT "
        f"(Оценка: {best_score.total_score}/100, рекомендация: {best_score.recommendation}). "
        f"Передаю в ПТО для анализа объемов работ и спецификаций."
    ) if best_tender and best_score else "[ЗАКУПЩИК] Подходящих тендеров не найдено."

    return {
        "tenders": [st[0] for st in scored_tenders],
        "selected_tender": best_tender,
        "current_agent": ROUTE_PTO,
        "messages": [AIMessage(content=summary_msg, name="ProcurementAgent")],
        "metadata": metadata,
    }


__all__ = [
    "create_procurement_agent",
    "run_procurement_agent",
    "PROCUREMENT_TOOLS",
]
