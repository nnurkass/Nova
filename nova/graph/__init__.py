"""LangGraph graph definitions — main graph, state, and routing logic."""
from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "ConstructionState",
    "ROUTE_COO",
    "ROUTE_COMPLETE",
    "ROUTE_END",
    "ROUTE_PROCUREMENT",
    "ROUTE_PTO",
    "ROUTE_SUPPLY",
    "build_graph",
    "is_complete",
    "route_after_coo",
    "route_after_procurement",
    "should_continue",
]


def __getattr__(name: str) -> Any:
    if name in {"ConstructionState"}:
        return getattr(import_module("nova.graph.state"), name)
    if name in {
        "ROUTE_COO",
        "ROUTE_COMPLETE",
        "ROUTE_END",
        "ROUTE_PROCUREMENT",
        "ROUTE_PTO",
        "ROUTE_SUPPLY",
        "is_complete",
        "route_after_coo",
        "route_after_procurement",
        "should_continue",
    }:
        return getattr(import_module("nova.graph.routers"), name)
    if name == "build_graph":
        return import_module("nova.graph.main_graph").build_graph
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
