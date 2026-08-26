"""
COO Supervisor Agent (Операционный директор).

Top-level orchestrator: decomposes user tasks, coordinates Level 2 agents,
and synthesizes the final Executive Summary report.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from langchain_core.messages import AIMessage

from nova.agents.coo.prompts import COO_SYSTEM_PROMPT
from nova.config import get_settings
from nova.graph.routers import ROUTE_END, ROUTE_PROCUREMENT
from nova.graph.state import ConstructionState

logger = logging.getLogger(__name__)


def generate_executive_summary(state: ConstructionState) -> str:
    """Generate a comprehensive Executive Summary Markdown report."""
    task = state.get("task", "Строительный тендерный анализ")
    tender = state.get("selected_tender")
    work_list = state.get("work_list", [])
    materials_list = state.get("materials_list", [])
    stock_check = state.get("stock_check", {})
    purchase_orders = state.get("purchase_orders", [])
    summary_data = stock_check.get("summary", {})

    tender_budget = float(tender.total_sum or 0.0) if tender else 0.0
    total_purchase_cost = sum(float(po.get("total_amount_kzt", 0.0)) for po in purchase_orders)
    in_stock_value = float(summary_data.get("in_stock_covered_value", 0.0))
    est_margin = max(0.0, tender_budget - total_purchase_cost - in_stock_value)
    margin_pct = (est_margin / tender_budget * 100.0) if tender_budget > 0 else 0.0
    urgent_pos = [po for po in purchase_orders if po.get("priority") == "URGENT"]

    now_str = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")

    report_lines = [
        f"# 🏗️ NOVA — ИСПОЛНИТЕЛЬНЫЙ ОТЧЁТ ОПЕРАЦИОННОГО ДИРЕКТОРА (COO)",
        f"**Дата формирования:** {now_str}",
        f"**Исходная задача:** {task}",
        "",
        "---",
        "",
        "## 1. 📌 ВЫБРАННЫЙ ТЕНДЕР (ГОСЗАКУПКИ РК)",
    ]

    if tender:
        end_str = tender.end_date.strftime("%d.%m.%Y %H:%M") if tender.end_date else "Не указан"
        report_lines.extend([
            f"- **Номер объявления:** `{tender.number}` (ID: {tender.id})",
            f"- **Наименование:** {tender.name_ru}",
            f"- **Заказчик:** {tender.organizer_name_ru} (БИН: `{tender.organizer_bin}`)",
            f"- **Бюджет конкурса:** **{tender_budget:,.2f} KZT**",
            f"- **Срок подачи заявок:** до {end_str}",
            f"- **Количество лотов:** {len(tender.lots)}",
        ])
    else:
        report_lines.append("_Подходящий тендер не выбран или конкурс завершен._")

    report_lines.extend([
        "",
        "## 2. 📋 ИНЖЕНЕРНАЯ ВЕДОМОСТЬ РАБОТ И МАТЕРИАЛОВ (ПТО)",
        f"Инженерным отделом ПТО проанализировано **{len(work_list)}** ключевых видов работ и **{len(materials_list)}** номенклатурных позиций материалов с учетом 5% технологического запаса.",
        "",
        "| № | Код | Наименование работ | Ед. изм. | Объём |",
        "|---|-----|--------------------|----------|-------|",
    ])

    for i, w in enumerate(work_list[:6], 1):
        report_lines.append(f"| {i} | `{w.code}` | {w.name} | {w.unit} | {w.quantity:,.1f} |")

    if len(work_list) > 6:
        report_lines.append(f"| ... | ... | _Ещё {len(work_list) - 6} позиций работ..._ | ... | ... |")

    report_lines.extend([
        "",
        "## 3. 📦 СКЛАДСКОЙ БАЛАНС И ДЕФИЦИТ (ОМТС)",
        f"- Позиций проверено на складах: **{summary_data.get('total_items', len(materials_list))}**",
        f"- Полностью в наличии: **{summary_data.get('fully_in_stock', 0)}** поз.",
        f"- Частично в наличии: **{summary_data.get('partial_stock', 0)}** поз.",
        f"- Требуют полной закупки (дефицит): **{summary_data.get('full_deficit', 0)}** поз.",
        f"- Оценка материалов из собственных остатков: **{in_stock_value:,.2f} KZT**",
        "",
        "## 4. 📑 СФОРМИРОВАННЫЕ ЗАЯВКИ НА ЗАКУПКУ (PURCHASE ORDERS)",
        f"Сформировано **{len(purchase_orders)}** заявок с обязательным страховым запасом **+10%**:",
        "",
        "| Заказ | Материал | Потребность | К закупке (+10%) | Сумма (KZT) | Приоритет | Поставщик РК |",
        "|-------|----------|-------------|------------------|-------------|-----------|--------------|",
    ])

    for po in purchase_orders:
        prio_badge = "🔴 URGENT" if po.get("priority") == "URGENT" else "🟢 NORMAL"
        req_q = po.get("required_quantity", po.get("quantity", 0))
        ord_q = po.get("order_quantity", po.get("quantity", 0))
        tot_kzt = po.get("total_amount_kzt", 0.0)
        sup = po.get("supplier_name", "Определяется")
        report_lines.append(
            f"| `{po.get('order_id')}` | {po.get('name')} | {req_q:,.1f} {po.get('unit')} | **{ord_q:,.1f} {po.get('unit')}** | {tot_kzt:,.2f} | {prio_badge} | {sup} |"
        )

    report_lines.extend([
        "",
        "## 5. 💰 ФИНАНСОВЫЙ БАЛАНС ПРОЕКТА",
        "| Статья бюджета | Сумма (KZT) | Доля от бюджета |",
        "|----------------|-------------|-----------------|",
        f"| **Общая сумма контракта (выручка)** | **{tender_budget:,.2f}** | 100.0% |",
        f"| Затраты на закупку недостающих материалов | {total_purchase_cost:,.2f} | {(total_purchase_cost/tender_budget*100.0) if tender_budget else 0:.1f}% |",
        f"| Себестоимость материалов со склада | {in_stock_value:,.2f} | {(in_stock_value/tender_budget*100.0) if tender_budget else 0:.1f}% |",
        f"| **Расчётная валовая прибыль (на СМР, налоги, маржу)** | **{est_margin:,.2f}** | **{margin_pct:.1f}%** |",
        "",
        "## 6. 🎯 УПРАВЛЕНЧЕСКАЯ РЕКОМЕНДАЦИЯ И СЛЕДУЮЩИЕ ШАГИ",
    ])

    if margin_pct >= 25.0 and len(urgent_pos) <= 5:
        report_lines.extend([
            "> [!TIP]",
            "> **РЕШЕНИЕ: РЕКОМЕНДОВАНО К УЧАСТИЮ (HIGH PRIORITY).**",
            "> Проект обладает высокой прогнозной маржинальностью и обеспечен складской/поставочной базой в РК.",
            "",
            "**Следующие шаги:**",
            "1. Зарезервировать имеющиеся остатки материалов на Складе №1 и Складе №2.",
            f"2. Подтвердить коммерческие предложения с ключевыми поставщиками (`{len(purchase_orders)}` заявок).",
            "3. Подать заявку на участие на портале goszakup.gov.kz до истечения срока.",
        ])
    else:
        report_lines.extend([
            "> [!NOTE]",
            "> **РЕШЕНИЕ: ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНОЕ СОГЛАСОВАНИЕ (MEDIUM PRIORITY).**",
            "> Обратить внимание на график поставок и сроки исполнения СМР.",
        ])

    return "\n".join(report_lines)


def create_coo_supervisor():
    """Create COO supervisor orchestrator when Anthropic LLM is available."""
    try:
        from langchain_anthropic import ChatAnthropic
        settings = get_settings()
        api_key = settings.anthropic_api_key.get_secret_value() if hasattr(settings.anthropic_api_key, "get_secret_value") else str(settings.anthropic_api_key)
        if not api_key or "mock" in api_key or "test" in api_key:
            return None
        return ChatAnthropic(
            model_name="claude-3-5-sonnet-20241022",
            anthropic_api_key=api_key,
            temperature=0.1,
        )
    except Exception:
        return None


def run_coo_agent(state: ConstructionState) -> dict[str, Any]:
    """Execute COO logic: task dispatching or final synthesis."""
    metadata = dict(state.get("metadata", {}))
    visited = list(metadata.get("visited_nodes", []))
    visited.append("coo")
    metadata["visited_nodes"] = visited

    # Phase A: Initial task dispatch
    if not metadata.get("supply_completed") and not state.get("selected_tender"):
        task = state.get("task", "")
        start_msg = (
            f"[COO] Задача принята в работу: «{task}». "
            f"Инициирую сквозной строительный пайплайн. "
            f"Делегирую поиск и скоринг лотов на goszakup.gov.kz Государственному Закупщику."
        )
        return {
            "current_agent": ROUTE_PROCUREMENT,
            "messages": [AIMessage(content=start_msg, name="COO")],
            "metadata": metadata,
        }

    # Phase B: Final Executive Summary compilation
    report_md = generate_executive_summary(state)
    metadata["final_report"] = report_md
    metadata["executive_summary"] = report_md

    final_msg = (
        f"[COO] Сквозной анализ строительного тендера успешно завершён. "
        f"Исполнительный отчёт (Executive Summary) сформирован."
    )

    return {
        "current_agent": ROUTE_END,
        "messages": [AIMessage(content=final_msg, name="COO")],
        "metadata": metadata,
    }


__all__ = [
    "run_coo_agent",
    "generate_executive_summary",
    "create_coo_supervisor",
]
