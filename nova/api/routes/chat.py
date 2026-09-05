"""
Interactive conversational ReAct Chat API for Nova multi-agent construction system.

Enables conversational interactions, tool calling, state mutations,
and dynamic orchestration across Level 2 and Level 3 agents.
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from nova.agents.chat_tools import (
    add_material_to_state,
    calculate_cost_structure_tool,
    modify_material_quantity_in_state,
    recalculate_state,
    update_tender_in_state,
)
from nova.agents.coo.agent import calculate_kazakhstan_cost_structure
from nova.agents.level3.excel_parser import parse_excel_estimate
from nova.agents.level3.goszakup_tool import (
    analyze_tender,
    goszakup_search,
    score_tender,
)
from nova.agents.level3.order_tool import create_purchase_order
from nova.agents.level3.pdf_parser import extract_materials, extract_work_list
from nova.agents.level3.stock_tool import check_stock, find_stock_item
from nova.agents.level3.supplier_tool import find_supplier, list_suppliers
from nova.api.schemas import ChatMessageSchema, ChatRequest, ChatResponse, ToolCallRecord
from nova.config.llm import get_chat_model
from nova.db.database import get_db
from nova.graph.main_graph import run_pipeline, serialize_state_for_api
from nova.integrations.abc.models import ABCMaterial, ABCWork
from nova.integrations.goszakup.client import GoszakupClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

SYSTEM_CHAT_PROMPT = """Ты — интеллектуальный Операционный директор (COO) и координатор мульти-агентной строительной системы Nova в Казахстане.
В твоем распоряжении команда специализированных агентов и набор инструментов:
1. 🏛️ Госзакупки: поиск актуальных конкурсов на goszakup.gov.kz (`goszakup_search`), детальный анализ (`analyze_tender`), многофакторный скоринг (`score_tender`).
2. 📐 ПТО (Сметы): извлечение ВОР и материалов по СН РК, чтение спецификаций и смет.
3. 📦 Склад и Снабжение: проверка остатков на складах (`check_stock`), подбор поставщиков в городах РК (`find_supplier`, `list_suppliers`), формирование заявок (`create_purchase_order`).
4. ⚙️ Управление проектом и сметой: изменение объемов материалов (`modify_material_quantity`), добавление позиций (`add_custom_material`), переключение выбранного тендера (`update_tender_selection`), пересчет баланса (`recalculate_pipeline_costs`).

ПРАВИЛА ПОВЕДЕНИЯ:
- Когда пользователь задает точечный вопрос (например, по наличию на складе, поиску поставщиков или конкретному тендеру) — ВСЕГДА вызывай соответствующий инструмент и давай точный ответ на основе его результатов.
- Когда пользователь просит изменить объем, добавить материал или пересчитать смету — вызывай инструмент мутации состояния.
- Отвечай вежливо, четко, инженерно грамотно, на русском языке. Все суммы приводи в тенге (KZT).
"""


def _generate_smart_suggestions(user_msg: str, state: Optional[dict[str, Any]]) -> list[str]:
    """Generate contextual quick-reply prompt suggestions for the user."""
    if not state or not state.get("selected_tender"):
        return [
            "🏛️ Найди тендер на больницу в Актобе",
            "📦 Сколько бетона и арматуры на складе в Караганде?",
            "🏭 Подбери поставщиков кабеля в Астане",
            "💰 Рассчитай маржу для объекта на 120 млн тенге",
        ]

    tender = state.get("selected_tender")
    t_name = tender.get("name_ru", "объекту") if isinstance(tender, dict) else getattr(tender, "name_ru", "объекту")
    return [
        "📊 Показать подробный финансовый баланс и маржу",
        "📦 Какие позиции материалов в дефиците?",
        "✏️ Увеличить запас арматуры на 15%",
        "📑 Показать сформированные заявки на закупку (PO)",
    ]


def _build_context_summary(state: Optional[dict[str, Any]]) -> str:
    """Build structured summary of active state for LLM system prompt."""
    if not state:
        return "\n\nТЕКУЩИЙ СТАТУС: В системе пока нет активного проекта. Пользователь может начать поиск тендера или загрузить смету."

    tender = state.get("selected_tender")
    works = state.get("work_list", [])
    materials = state.get("materials_list", [])
    pos = state.get("purchase_orders", [])
    stock_sum = state.get("stock_check", {}).get("summary", {})
    fin = state.get("metadata", {}).get("financial_model", {})

    lines = ["\n\nТЕКУЩИЙ АКТИВНЫЙ ПРОЕКТ В СИСТЕМЕ:"]
    if tender:
        t_name = tender.get("name_ru") if isinstance(tender, dict) else getattr(tender, "name_ru", "")
        t_sum = float(tender.get("total_sum", 0.0) if isinstance(tender, dict) else getattr(tender, "total_sum", 0.0))
        t_num = tender.get("number") if isinstance(tender, dict) else getattr(tender, "number", "")
        lines.append(f"- Выбранный тендер: №{t_num} «{t_name}» (Бюджет: {t_sum:,.2f} KZT)")
    else:
        lines.append("- Тендер: не выбран (локальная смета или инициализация)")

    lines.append(f"- Работ в смете (ВОР): {len(works)} шт.")
    lines.append(f"- Материалов в спецификации: {len(materials)} шт.")
    if stock_sum:
        lines.append(
            f"- Складской баланс: в наличии {stock_sum.get('fully_in_stock', 0)} поз., "
            f"дефицит {stock_sum.get('full_deficit', 0)} поз."
        )
    if pos:
        total_po = sum(float(p.get("total_amount_kzt", 0.0)) for p in pos)
        lines.append(f"- Заявок на закупку (PO): {len(pos)} шт. на сумму {total_po:,.2f} KZT")
    if fin and "margin_pct" in fin:
        lines.append(f"- Сметная маржинальность: {fin.get('margin_pct', 0.0):.1f}% (Чистая прибыль: {fin.get('gross_profit', 0.0):,.2f} KZT)")

    if materials:
        lines.append("- Примеры материалов в смете:")
        for m in materials[:5]:
            m_code = m.get("code") if isinstance(m, dict) else getattr(m, "code", "")
            m_name = m.get("name") if isinstance(m, dict) else getattr(m, "name", "")
            m_qty = m.get("quantity") if isinstance(m, dict) else getattr(m, "quantity", 0)
            m_unit = m.get("unit") if isinstance(m, dict) else getattr(m, "unit", "")
            lines.append(f"  * [{m_code}] {m_name} — {m_qty} {m_unit}")

    return "\n".join(lines)


@router.post("", response_model=ChatResponse)
def handle_chat_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """
    Process an interactive chat message with Nova Multi-Agent system via ReAct Tool Calling loop.
    Supports live tools, state mutations, and dynamic pipeline invocation.
    """
    user_text = payload.message.strip()
    history = payload.history
    current_state = payload.current_state or {}
    tool_calls_recorded: list[ToolCallRecord] = []

    # 1. State Mutation & Live Tools setup
    state_ref = {"state": current_state}

    @tool
    def tool_check_stock(material_code: str = "", material_name: str = "") -> dict[str, Any]:
        """Check inventory stock level for a construction material in warehouse database."""
        res = check_stock.invoke({"material_code": material_code, "material_name": material_name})
        return res

    @tool
    def tool_find_supplier(material_name: str = "", category: str = "", city: str = "") -> dict[str, Any]:
        """Find matching verified suppliers in Kazakhstan by material name, category, or city."""
        res = find_supplier.invoke({"material_name": material_name, "category": category, "city": city})
        return res

    @tool
    def tool_list_suppliers(category: str = "") -> list[dict[str, Any]]:
        """List all registered suppliers in Kazakhstan, optionally filtered by category."""
        return list_suppliers(category=category)

    @tool
    def tool_goszakup_search(query: str = "", region: str = "", limit: int = 3) -> list[dict[str, Any]]:
        """Search government tenders on goszakup.gov.kz by keyword and region."""
        res = goszakup_search.invoke({"query": query, "region": region, "limit": limit})
        return res

    @tool
    def tool_score_tender(tender_id: int) -> dict[str, Any]:
        """Evaluate tender attractiveness and risks (0-100 score)."""
        return score_tender.invoke({"tender_id": tender_id})

    @tool
    def tool_modify_material_quantity(code: str, new_quantity: float) -> dict[str, Any]:
        """Modify the quantity of a material item in the active estimate and recalculate balance."""
        new_state, result = modify_material_quantity_in_state(state_ref["state"], code, new_quantity)
        state_ref["state"] = new_state
        return result

    @tool
    def tool_add_custom_material(name: str, unit: str, quantity: float, price: float = 0.0, code: str = "") -> dict[str, Any]:
        """Add a new material item to the active bill of materials and recalculate costs."""
        new_state, result = add_material_to_state(state_ref["state"], name, unit, quantity, price, code)
        state_ref["state"] = new_state
        return result

    @tool
    def tool_update_tender_selection(tender_id: int) -> dict[str, Any]:
        """Switch the selected tender in state to a different tender ID."""
        new_state, result = update_tender_in_state(state_ref["state"], tender_id)
        state_ref["state"] = new_state
        return result

    @tool
    def tool_recalculate_pipeline_costs() -> dict[str, Any]:
        """Recalculate warehouse deficit, purchase orders, and financial margin according to SN RK."""
        new_state = recalculate_state(state_ref["state"])
        state_ref["state"] = new_state
        fin = new_state.get("metadata", {}).get("financial_model", {})
        return {
            "success": True,
            "margin_pct": fin.get("margin_pct"),
            "gross_profit": fin.get("gross_profit"),
            "total_cost": fin.get("total_cost"),
            "total_purchase_cost": fin.get("total_purchase_cost"),
        }

    @tool
    def tool_run_full_pipeline(task: str) -> dict[str, Any]:
        """Run the complete multi-agent pipeline (Procurement -> PTO -> Supply -> COO)."""
        final_pipeline_state = run_pipeline(task)
        state_ref["state"] = serialize_state_for_api(final_pipeline_state)
        tender = state_ref["state"].get("selected_tender")
        return {
            "success": True,
            "task": task,
            "selected_tender": tender.get("name_ru") if tender else task,
            "works_count": len(state_ref["state"].get("work_list", [])),
            "materials_count": len(state_ref["state"].get("materials_list", [])),
            "pos_count": len(state_ref["state"].get("purchase_orders", [])),
        }

    chat_tools_map = {
        "check_stock": tool_check_stock,
        "find_supplier": tool_find_supplier,
        "list_suppliers": tool_list_suppliers,
        "goszakup_search": tool_goszakup_search,
        "score_tender": tool_score_tender,
        "modify_material_quantity": tool_modify_material_quantity,
        "add_custom_material": tool_add_custom_material,
        "update_tender_selection": tool_update_tender_selection,
        "recalculate_pipeline_costs": tool_recalculate_pipeline_costs,
        "run_full_pipeline": tool_run_full_pipeline,
        "calculate_cost_structure": calculate_cost_structure_tool,
    }
    chat_tools_list = list(chat_tools_map.values())

    # 2. ReAct Loop with live LLM Tool Calling (if model configured)
    llm = get_chat_model(temperature=0.2, max_tokens=2500)
    llm_with_tools = None
    if llm is not None:
        try:
            llm_with_tools = llm.bind_tools(chat_tools_list)
        except Exception as exc:
            logger.debug("Failed to bind tools to LLM: %s", exc)

    if llm_with_tools is not None:
        try:
            context_summary = _build_context_summary(state_ref["state"])
            messages = [
                SystemMessage(content=SYSTEM_CHAT_PROMPT + context_summary),
            ]
            for h in history[-6:]:
                if h.role == "user":
                    messages.append(HumanMessage(content=h.content))
                elif h.role in ("assistant", "system"):
                    messages.append(AIMessage(content=h.content))
            messages.append(HumanMessage(content=user_text))

            max_react_turns = 4
            turn = 0
            final_ai_message = None

            while turn < max_react_turns:
                turn += 1
                ai_msg = llm_with_tools.invoke(messages)
                messages.append(ai_msg)

                # If model requested tool calls, execute them
                tool_calls = getattr(ai_msg, "tool_calls", [])
                if not tool_calls:
                    final_ai_message = ai_msg
                    break

                for tc in tool_calls:
                    t_name = tc.get("name")
                    t_args = tc.get("args", {})
                    t_id = tc.get("id", str(uuid.uuid4()))

                    tool_fn = chat_tools_map.get(t_name)
                    if tool_fn:
                        try:
                            t_result = tool_fn.invoke(t_args)
                            tool_calls_recorded.append(
                                ToolCallRecord(
                                    tool=t_name,
                                    args=t_args,
                                    status="ok",
                                    title=f"Вызов инструмента: {t_name}",
                                    result_summary=str(t_result)[:120],
                                )
                            )
                            messages.append(ToolMessage(content=json.dumps(t_result, ensure_ascii=False), tool_call_id=t_id))
                        except Exception as t_err:
                            logger.error("Error executing tool %s: %s", t_name, t_err)
                            tool_calls_recorded.append(
                                ToolCallRecord(
                                    tool=t_name,
                                    args=t_args,
                                    status="error",
                                    title=f"Ошибка вызова: {t_name}",
                                    result_summary=str(t_err),
                                )
                            )
                            messages.append(ToolMessage(content=f"Error: {t_err}", tool_call_id=t_id))
                    else:
                        messages.append(ToolMessage(content=f"Tool {t_name} not recognized", tool_call_id=t_id))

            if final_ai_message:
                reply_text = str(final_ai_message.content)
                thought = (
                    f"ReAct Agent: выполнено {len(tool_calls_recorded)} действий(я) с инструментами системы. "
                    f"Состояние синхронизировано."
                )
                return ChatResponse(
                    response=reply_text,
                    sender="coo",
                    sender_title="Операционный директор (COO)",
                    thought=thought,
                    state=state_ref["state"] if state_ref["state"] else None,
                    suggestions=_generate_smart_suggestions(user_text, state_ref["state"]),
                    tool_calls=tool_calls_recorded,
                )
        except Exception as exc:
            logger.warning("LLM ReAct loop encountered an error: %s. Using deterministic dispatcher.", exc)

    # 3. Deterministic Fallback Tool-Dispatcher (Mock/offline mode)
    u_lower = user_text.lower()

    # A. Stock Check Query
    if any(k in u_lower for k in ["склад", "остатк", "наличи", "наличие", "бетон", "арматур"]) and any(
        q in u_lower for q in ["скольк", "провер", "есть ли", "дефицит", "остаток", "где", "покажи", "что на"]
    ):
        target_mat = "арматура" if "арматур" in u_lower else ("бетон" if "бетон" in u_lower else "")
        res = check_stock.invoke({"material_name": target_mat or user_text})
        tool_calls_recorded.append(
            ToolCallRecord(
                tool="check_stock",
                args={"material_name": target_mat or user_text},
                status="ok",
                title=f"📦 Проверка остатков на складе: {target_mat or 'материалы'}",
                result_summary=f"В наличии: {res.get('available', 0)} {res.get('unit', '')} на складе {res.get('location', 'Основной')}",
            )
        )

        if res.get("found"):
            in_stk = float(res.get("in_stock") or 0)
            resv = float(res.get("reserved") or 0)
            avail = float(res.get("available") or 0)
            price_val = float(res.get("price_kzt") or 0)
            resp_msg = (
                f"### 📦 Результаты проверки склада\n\n"
                f"По вашему запросу проверена позиция: **{res.get('material_name')}** (код `{res.get('material_code')}`):\n\n"
                f"- **Фактический остаток:** {in_stk:,.1f} {res.get('unit')}\n"
                f"- **В резерве:** {resv:,.1f} {res.get('unit')}\n"
                f"- **Доступно к отгрузке:** **{avail:,.1f} {res.get('unit')}**\n"
                f"- **Локация хранения:** {res.get('location', 'Склад №1 (Караганда)')}\n"
                f"- **Учетная цена:** {price_val:,.2f} ₸ / {res.get('unit')}\n\n"
                f"Данная позиция доступна для использования в сметах и покрытия дефицита без внешних закупок."
            )
        else:
            resp_msg = (
                f"Позиция **«{target_mat or user_text}»** на основном складе не числится или полностью зарезервирована. "
                f"Для покрытия потребности необходимо сформировать заявку (PO) внешнему поставщику."
            )

        return ChatResponse(
            response=resp_msg,
            sender="supply",
            sender_title="Специалист ОМТС / Снабженец",
            thought="Выполнен прямой запрос к складской базе данных через инструмент check_stock.",
            state=state_ref["state"] if state_ref["state"] else None,
            suggestions=_generate_smart_suggestions(user_text, state_ref["state"]),
            tool_calls=tool_calls_recorded,
        )

    # B. Suppliers Query
    if any(k in u_lower for k in ["поставщик", "поставк", "купить", "заказать", "снабжен", "кабел", "труб"]) and any(
        q in u_lower for q in ["найди", "подбери", "список", "кто", "покажи", "где"]
    ):
        city = "Астана" if "астан" in u_lower else ("Алматы" if "алмат" in u_lower else "")
        mat = "кабель" if "кабел" in u_lower else ("труба" if "труб" in u_lower else "")
        sup_res = find_supplier.invoke({"material_name": mat or user_text, "city": city})

        tool_calls_recorded.append(
            ToolCallRecord(
                tool="find_supplier",
                args={"material_name": mat or user_text, "city": city},
                status="ok",
                title=f"🏭 Поиск поставщиков: {mat or 'материалы'} ({city or 'РК'})",
                result_summary=f"Найден: {sup_res.get('supplier_name')} (Рейтинг: {sup_res.get('rating')})",
            )
        )

        sup_price = float(sup_res.get("unit_price_kzt") or 0)
        resp_msg = (
            f"### 🏭 Рекомендованный поставщик в Казахстане\n\n"
            f"Для поставки продукции **«{sup_res.get('item_name') or mat or user_text}»** подобран проверенный контрагент:\n\n"
            f"- **Компания:** **{sup_res.get('supplier_name')}** (БИН: `{sup_res.get('bin')}`)\n"
            f"- **Город:** {sup_res.get('city')}\n"
            f"- **Надежность / Рейтинг:** ⭐ **{sup_res.get('rating')}/5.0**\n"
            f"- **Срок поставки:** от **{sup_res.get('delivery_days')}** рабочих дней\n"
            f"- **Ориентировочная цена:** **{sup_price:,.2f} ₸**\n"
            f"- **Контакты:** 📞 {sup_res.get('phone')} | ✉️ {sup_res.get('email')}\n\n"
            f"_Сформировать проект заявки на закупку (Purchase Order) для этого поставщика?_"
        )

        return ChatResponse(
            response=resp_msg,
            sender="supply",
            sender_title="Специалист ОМТС / Снабженец",
            thought="Поиск контрагентов выполнен через реестр поставщиков РК (find_supplier).",
            state=state_ref["state"] if state_ref["state"] else None,
            suggestions=_generate_smart_suggestions(user_text, state_ref["state"]),
            tool_calls=tool_calls_recorded,
        )

    # C. Goszakup Search Query
    if any(k in u_lower for k in ["найди тендер", "поиск тендер", "госзакуп", "тендеры", "лоты"]) or (
        "тендер" in u_lower and any(q in u_lower for q in ["актобе", "алматы", "астана", "больниц", "школ", "покажи"])
    ):
        region = "г. Актобе" if "актобе" in u_lower else ("г. Астана" if "астан" in u_lower else "г. Алматы")
        kw = user_text.replace("найди", "").replace("тендер", "").replace("тендеры", "").replace("на", "").strip()
        search_res = goszakup_search.invoke({"query": kw or "строительство", "region": region, "limit": 3})

        tool_calls_recorded.append(
            ToolCallRecord(
                tool="goszakup_search",
                args={"query": kw, "region": region, "limit": 3},
                status="ok",
                title=f"🔍 Поиск конкурсов на goszakup.gov.kz ({region})",
                result_summary=f"Найдено {len(search_res)} лотов",
            )
        )

        if search_res:
            top_tenders_text = []
            for i, t in enumerate(search_res[:3], 1):
                top_tenders_text.append(
                    f"{i}. **№{t.get('number')}** — «{t.get('name_ru')}»\n"
                    f"   - Бюджет: **{float(t.get('total_sum', 0)):,.2f} ₸**\n"
                    f"   - Заказчик: {t.get('organizer_name_ru')}\n"
                    f"   - Регион: {t.get('region_name', region)}"
                )
            t_list_md = "\n\n".join(top_tenders_text)

            resp_msg = (
                f"### 🏛️ Найдено {len(search_res)} подходящих тендеров на goszakup.gov.kz\n\n"
                f"{t_list_md}\n\n"
                f"👉 **Какой из этих лотов взять в детальный инженерный расчет (ПТО и сметы)?** "
                f"Напишите номер лота или нажмите кнопку ниже."
            )
        else:
            resp_msg = (
                f"По запросу «{user_text}» в регионе **{region}** активных конкурсов не найдено. "
                f"Рекомендуется расширить поисковые критерии или уточнить предмет закупки."
            )

        return ChatResponse(
            response=resp_msg,
            sender="procurement",
            sender_title="Государственный Закупщик",
            thought="Поиск на портале госзакупок выполнен через инструмент goszakup_search.",
            state=state_ref["state"] if state_ref["state"] else None,
            suggestions=[
                f"Выбрать лот №{search_res[0].get('number')}" if search_res else "Повторить поиск",
                "Рассчитать смету для первого лота",
                "Проверить надежность заказчика",
            ],
            tool_calls=tool_calls_recorded,
        )

    # D. State Mutation: Modify Quantity (e.g. "увеличь запас арматуры на 15%", "измени объем бетона на 120")
    if any(k in u_lower for k in ["увелич", "уменьш", "измени", "скорректир", "поменяй"]) and any(
        m in u_lower for m in ["арматур", "бетон", "панел", "труб", "кабел", "запас", "объем", "количеств"]
    ):
        pct_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", user_text)
        qty_match = re.search(r"(\d+(?:[.,]\d+)?)", user_text)

        target_code = "арматур" if "арматур" in u_lower else ("бетон" if "бетон" in u_lower else ("труб" if "труб" in u_lower else ("панел" if "панел" in u_lower else "")))

        # Find existing item to determine old qty
        m_list = state_ref["state"].get("materials_list", [])
        existing = next((m for m in m_list if target_code and target_code in (m.get("name", "") if isinstance(m, dict) else m.name).lower()), None)
        if not existing and m_list:
            existing = m_list[0]

        if existing:
            cur_qty = float(existing.get("quantity", 10.0) if isinstance(existing, dict) else existing.quantity)
            if pct_match:
                pct = float(pct_match.group(1).replace(",", "."))
                new_qty = round(cur_qty * (1.0 + pct / 100.0), 2)
            elif qty_match:
                new_qty = float(qty_match.group(1).replace(",", "."))
            else:
                new_qty = round(cur_qty * 1.15, 2)

            item_code = existing.get("code") if isinstance(existing, dict) else existing.code
            new_state, mod_res = modify_material_quantity_in_state(state_ref["state"], item_code, new_qty)
            state_ref["state"] = new_state

            tool_calls_recorded.append(
                ToolCallRecord(
                    tool="modify_material_quantity",
                    args={"code": item_code, "new_quantity": new_qty},
                    status="ok",
                    title=f"✏️ Корректировка объема: {mod_res.get('name')}",
                    result_summary=f"{mod_res.get('old_quantity')} -> {new_qty} {mod_res.get('unit')}",
                )
            )
            tool_calls_recorded.append(
                ToolCallRecord(
                    tool="recalculate_pipeline_costs",
                    args={},
                    status="ok",
                    title="📊 Автоматический пересчет маржинальности и заявок",
                    result_summary=f"Маржа: {mod_res.get('margin_pct', 0.0)}%",
                )
            )

            resp_msg = (
                f"### ✅ Объем материала успешно изменен и смета пересчитана!\n\n"
                f"- **Позиция:** {mod_res.get('name')} (`{mod_res.get('code')}`)\n"
                f"- **Прежний объем:** {mod_res.get('old_quantity')} {mod_res.get('unit')}\n"
                f"- **Новый объем:** **{mod_res.get('new_quantity')} {mod_res.get('unit')}**\n"
                f"- **Обновленная прогнозная маржа:** **{mod_res.get('margin_pct', 0.0):.1f}%**\n"
                f"- **Чистая прибыль генподрядчика:** **{mod_res.get('gross_profit', 0.0):,.2f} ₸**\n\n"
                f"Все изменения синхронизированы: обновлены складской баланс, заявки на закупку (PO) и вкладка «Финансы» справа 👉."
            )
            return ChatResponse(
                response=resp_msg,
                sender="pto",
                sender_title="Инженер ПТО",
                thought="Скорректирован объем материала в смете и выполнен автоматический пересчет финмодели.",
                state=state_ref["state"],
                suggestions=_generate_smart_suggestions(user_text, state_ref["state"]),
                tool_calls=tool_calls_recorded,
            )

    # E. State Mutation: Add Custom Material
    if any(k in u_lower for k in ["добавь материал", "добавить позицию", "включи в смету", "добавь в смету"]):
        # Extract title or defaults
        clean_name = user_text
        for strip_w in ["добавь материал", "добавить позицию", "включи в смету", "добавь в смету"]:
            clean_name = clean_name.replace(strip_w, "")
        clean_name = clean_name.strip(" :,-") or "Специализированный строительный материал"

        new_state, add_res = add_material_to_state(
            state_ref["state"],
            name=clean_name,
            unit="т",
            quantity=10.0,
            price=120000.0,
        )
        state_ref["state"] = new_state

        tool_calls_recorded.append(
            ToolCallRecord(
                tool="add_custom_material",
                args={"name": clean_name, "unit": "т", "quantity": 10.0, "price": 120000.0},
                status="ok",
                title=f"➕ Добавлен материал в смету: {clean_name}",
                result_summary=f"Код: {add_res.get('code')}, 10.0 т",
            )
        )
        tool_calls_recorded.append(
            ToolCallRecord(
                tool="recalculate_pipeline_costs",
                args={},
                status="ok",
                title="📊 Пересчет финансовой модели объекта",
                result_summary=f"Маржа: {add_res.get('margin_pct', 0.0)}%",
            )
        )

        resp_msg = (
            f"### ✅ Новая позиция добавлена в ведомость материалов!\n\n"
            f"- **Наименование:** **{clean_name}**\n"
            f"- **Код позиции:** `{add_res.get('code')}`\n"
            f"- **Количество:** 10.0 т по ориентировочной цене 120,000 ₸/т\n"
            f"- **Всего материалов в проекте:** {add_res.get('total_materials_count')} позиций\n"
            f"- **Новая маржа проекта:** **{add_res.get('margin_pct', 0.0):.1f}%**\n\n"
            f"Позиция добавлена в ведомость ресурсов ПТО и отправлена в ОМТС для проверки складских запасов."
        )
        return ChatResponse(
            response=resp_msg,
            sender="pto",
            sender_title="Инженер ПТО",
            thought="В смету внесена пользовательская позиция материала, обновлен складской баланс.",
            state=state_ref["state"],
            suggestions=_generate_smart_suggestions(user_text, state_ref["state"]),
            tool_calls=tool_calls_recorded,
        )

    # F. Recalculate Costs / Margin Query
    if any(k in u_lower for k in ["пересчитай", "рассчитай марж", "маржинальност", "финмодел", "себестоимост", "баланс"]):
        budget_val = 120000000.0
        b_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:млн|миллион)", user_text.lower())
        if b_match:
            budget_val = float(b_match.group(1).replace(",", ".")) * 1_000_000.0

        if state_ref["state"] and state_ref["state"].get("materials_list"):
            new_state = recalculate_state(state_ref["state"])
            state_ref["state"] = new_state
            fin = new_state.get("metadata", {}).get("financial_model", {})
        else:
            fin = calculate_kazakhstan_cost_structure(budget_val, budget_val * 0.45, budget_val * 0.15)

        tb = float(fin.get("tender_budget") or budget_val or 0)
        gp = float(fin.get("gross_profit") or 0)
        mp = float(fin.get("margin_pct") or 0)
        vat = float(fin.get("vat_12") or 0)
        mat_c = float(fin.get("material_costs") or 0)
        lab_c = float(fin.get("labor_cost") or 0)
        mach_c = float(fin.get("machinery_cost") or 0)
        ovh_c = float(fin.get("overhead_cost") or 0)
        tot_c = float(fin.get("total_cost") or 0)

        tool_calls_recorded.append(
            ToolCallRecord(
                tool="calculate_cost_structure",
                args={"tender_budget": tb},
                status="ok",
                title="💰 Расчет себестоимости по нормативам СН РК",
                result_summary=f"Маржа: {mp:.1f}% ({gp:,.2f} ₸)",
            )
        )

        resp_msg = (
            f"### 💰 Финансовая модель и структура затрат СМР (СН РК 8.02)\n\n"
            f"Расчет выполнен с учетом строительных и налоговых нормативов Республики Казахстан:\n\n"
            f"| Статья затрат | Сумма (KZT) | Доля | Норматив РК |\n"
            f"|---|---|---|---|\n"
            f"| **Договорная цена (Выручка)** | **{tb:,.2f} ₸** | 100% | Предельная сумма тендера |\n"
            f"| _↳ НДС 12%_ | _{vat:,.2f} ₸_ | 10.7% | Ставка НК РК (12%) |\n"
            f"| Материалы (Закупка + Склад) | {mat_c:,.2f} ₸ | {(mat_c / (tb or 1) * 100):.1f}% | Ресурсная ведомость |\n"
            f"| Фонд оплаты труда (ФОТ) | {lab_c:,.2f} ₸ | 14.0% | Норматив СН РК (14%) |\n"
            f"| Эксплуатация машин и спецтехники | {mach_c:,.2f} ₸ | 8.0% | Норматив СН РК (8%) |\n"
            f"| Накладные расходы (НР и СП) | {ovh_c:,.2f} ₸ | 10.0% | 10% от прямых затрат |\n"
            f"| **Полная сметная себестоимость** | **{tot_c:,.2f} ₸** | {(tot_c / (tb or 1) * 100):.1f}% | Прямые + накладные |\n"
            f"| 🎯 **Чистая валовая прибыль** | **{gp:,.2f} ₸** | **{mp:.1f}%** | Рентабельность генподрядчика |\n"
        )

        return ChatResponse(
            response=resp_msg,
            sender="coo",
            sender_title="Операционный директор (COO)",
            thought="Структура себестоимости и маржа рассчитаны по нормам СН РК и Налоговому кодексу РК.",
            state=state_ref["state"] if state_ref["state"] else None,
            suggestions=_generate_smart_suggestions(user_text, state_ref["state"]),
            tool_calls=tool_calls_recorded,
        )

    # G. Full Turnkey Pipeline Trigger
    is_pipeline_trigger = any(
        kw in u_lower
        for kw in [
            "найди тендер и рассчитай",
            "рассчитай под ключ",
            "рассчитай проект",
            "запусти пайплайн",
            "полный анализ",
            "сквозной расчет",
        ]
    ) or (len(user_text) > 15 and any(act in u_lower for act in ["рассчитай смету на", "найди тендер на строительство"]))

    if is_pipeline_trigger:
        final_pipeline_state = run_pipeline(user_text)
        state_ref["state"] = serialize_state_for_api(final_pipeline_state)

        tender = state_ref["state"].get("selected_tender")
        tender_name = tender.get("name_ru", user_text) if tender else user_text
        tender_sum = float(tender.get("total_sum", 0.0)) if tender else 0.0
        works = state_ref["state"].get("work_list", [])
        materials = state_ref["state"].get("materials_list", [])
        pos = state_ref["state"].get("purchase_orders", [])
        stock_sum = state_ref["state"].get("stock_check", {}).get("summary", {})

        tool_calls_recorded.append(
            ToolCallRecord(
                tool="run_full_pipeline",
                args={"task": user_text},
                status="ok",
                title=f"🏗️ Сквозной мульти-агентный конвейер: «{user_text[:40]}...»",
                result_summary=f"Тендер: {tender_sum:,.2f} ₸, ВОР: {len(works)}, Материалов: {len(materials)}, Заявок PO: {len(pos)}",
            )
        )

        resp_msg = (
            f"### 🏗️ Комплексный анализ объекта завершен!\n\n"
            f"Мы провели задачу **«{user_text}»** через всех специализированных агентов Nova:\n\n"
            f"1. **🏛️ Госзакупки:** Сформирован лот **«{tender_name}»** на сумму **{tender_sum:,.2f} ₸**.\n"
            f"2. **📐 ПТО (Сметы & Нормы):** Разработано **{len(works)}** этапов СМР и **{len(materials)}** позиций материалов с технологическим буфером 5%.\n"
            f"3. **📦 Склад & Снабжение:** Покрыто со склада **{stock_sum.get('fully_in_stock', 0)}** позиций, сформировано **{len(pos)}** заявок поставщикам РК (+10% страховой запас).\n"
            f"4. **💰 Финансы:** Все документы загружены в **панель справа** 👉.\n\n"
            f"_Вы можете точечно скорректировать объем любого материала или проверить остатки на складе._"
        )
        return ChatResponse(
            response=resp_msg,
            sender="coo",
            sender_title="Операционный директор (COO)",
            thought="Запущен и успешно выполнен сквозной мульти-агентный цикл Nova.",
            state=state_ref["state"],
            suggestions=_generate_smart_suggestions(user_text, state_ref["state"]),
            tool_calls=tool_calls_recorded,
        )

    # H. General assistant response
    resp_msg = (
        f"Я готов помочь с любыми инженерными и закупочными операциями Nova:\n\n"
        f"- 🏛️ **Поиск тендеров:** *«Найди тендер на строительство больницы в Актобе»*\n"
        f"- 📦 **Проверка склада:** *«Сколько у нас бетона и арматуры на складе в Караганде?»*\n"
        f"- 🏭 **Поставщики:** *«Подбери надежных поставщиков кабеля в Астане»*\n"
        f"- ✏️ **Смета:** *«Увеличь запас арматуры на 15% и пересчитай маржу»*\n"
        f"- 💰 **Финансы:** *«Рассчитай финмодель по нормативам РК для объекта на 120 млн тенге»*"
    )
    return ChatResponse(
        response=resp_msg,
        sender="coo",
        sender_title="Операционный директор (COO)",
        thought="Предоставлен перечень доступных возможностей мульти-агентной системы Nova.",
        state=state_ref["state"] if state_ref["state"] else None,
        suggestions=_generate_smart_suggestions(user_text, state_ref["state"]),
        tool_calls=tool_calls_recorded,
    )
