"""Regression tests for lazy imports and import-time safety."""
from __future__ import annotations

import importlib
import sys


def test_importing_graph_routers_does_not_import_main_graph():
    sys.modules.pop("nova.graph", None)
    sys.modules.pop("nova.graph.routers", None)
    sys.modules.pop("nova.graph.main_graph", None)

    importlib.import_module("nova.graph.routers")

    assert "nova.graph.main_graph" not in sys.modules
