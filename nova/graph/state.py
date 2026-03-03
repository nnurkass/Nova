"""
Shared state definition for the Nova LangGraph pipeline.

ConstructionState is the single TypedDict passed between all graph nodes.
The `messages` field uses `add_messages` reducer so messages accumulate
rather than being replaced on each state update.
"""
from __future__ import annotations
from typing import Annotated, Any, Optional, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from nova.integrations.goszakup.models import Tender
from nova.integrations.abc.models import ABCWork, ABCMaterial


class ConstructionState(TypedDict):
    """LangGraph state for the construction procurement pipeline."""
    # User input
    task: str
    # Procurement agent: found and selected tenders
    tenders: list[Tender]
    selected_tender: Optional[Tender]
    # PTO agent: extracted work and materials
    work_list: list[ABCWork]
    materials_list: list[ABCMaterial]
    # Supply agent: stock check results and orders
    stock_check: dict[str, Any]
    purchase_orders: list[dict[str, Any]]
    # Pipeline control
    current_agent: str
    messages: Annotated[list[AnyMessage], add_messages]
    errors: list[str]
    metadata: dict[str, Any]
