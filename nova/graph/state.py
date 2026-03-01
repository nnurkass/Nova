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

# TODO: Step 1.3.1 — implement ConstructionState TypedDict
