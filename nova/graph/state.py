"""
Shared state definition for the Nova LangGraph pipeline.

ConstructionState is a TypedDict that carries all data between agents:
- task: original user task description
- tenders: list of found tenders from goszakup
- selected_tender: tender chosen for processing
- work_list: list of works from tender documentation
- materials_list: list of required materials
- stock_check: inventory check results
- purchase_orders: generated purchase orders
- current_agent: name of currently active agent
- messages: conversation history (LangGraph messages format)
- errors: accumulated errors during pipeline execution
- metadata: timestamps, trace IDs, etc.

Implemented in Step 1.3.
"""

from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from nova.integrations.abc.models import ABCMaterial, ABCWork
from nova.integrations.goszakup.models import Tender


class ConstructionState(TypedDict, total=False):
    # Original user task description
    task: str
    # List of tenders found from goszakup.gov.kz
    tenders: list[Tender]
    # Tender selected for full processing
    selected_tender: Tender | None
    # Extracted work items from tender documentation
    work_list: list[ABCWork]
    # Required materials derived from work list
    materials_list: list[ABCMaterial]
    # Inventory check results: {material_code: qty_available}
    stock_check: dict[str, Any]
    # Generated purchase order records
    purchase_orders: list[dict[str, Any]]
    # Name of currently active agent
    current_agent: str
    # Conversation history with LangGraph add_messages reducer
    messages: Annotated[list[BaseMessage], add_messages]
    # Accumulated error messages during pipeline execution
    errors: list[str]
    # Pipeline metadata: timestamps, trace_id, task_id, etc.
    metadata: dict[str, Any]
