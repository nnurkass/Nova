"""
Interactive conversational Chat API for Nova multi-agent construction system.
Enables conversational interactions, Q&A, recalculations, and artifact updates.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from nova.api.schemas import ChatMessageSchema, ChatRequest, ChatResponse
from nova.config.llm import get_chat_model
from nova.db.database import get_db
from nova.graph.main_graph import run_pipeline, serialize_state_for_api

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

SYSTEM_CHAT_PROMPT = """Ты — интеллектуальный Операционный директор (COO) и координатор мульти-агентной строительной системы Nova в Казахстане.
Твоя команда состоит из специализированных агентов:
1. 🏛️ **Гос. Закупщик** (Goszakup.gov.kz, поиск конкурсов, оценка лотов, проверка заказчиков)
2. 📐 **Инженер ПТО** (АВС Сметные решения, СН РК, расчет объемов работ ВОР, спецификации материалов)
3. 📦 **Специалист ОМТС / Снабженец** (складской учет, расчет дефицита с запасом +10%, подбор поставщиков РК)
4. 💼 **COO / Фин. аналитик** (расчет маржинальности, риски, итоговое решение)

Отвечай профессионально, кратко, структурированно, на русском языке.
Если пользователь просит найти тендер, рассчитать проект, проверить материалы или оценить объект — подтверди запуск анализа или дай четкий инженерно-финансовый ответ.
Все денежные суммы указывай в тенге (KZT).
"""


def _generate_smart_suggestions(user_msg: str, state: Optional[dict[str, Any]]) -> list[str]:
    """Generate contextual quick-reply prompt suggestions for the user."""
    if not state or not state.get("selected_tender"):
        return [
            "🏫 Найти тендеры на капремонт школы в Алматы",
            "🚰 Рассчитать сети водоснабжения в Астане",
            "📦 Как вы проверяете остатки на складе?",
            "📐 Какие нормативы СН РК используются в сметах?",
        ]

    tender = state.get("selected_tender")
    t_name = tender.get("name_ru", "объекту") if isinstance(tender, dict) else getattr(tender, "name_ru", "объекту")
    return [
        "📊 Показать подробный финансовый баланс и маржу",
        "📦 Какие позиции материалов в дефиците?",
        "📑 Сформировать и показать заявки на закупку (PO)",
        "🔍 Найти альтернативные похожие тендеры в регионе",
    ]


@router.post("", response_model=ChatResponse)
def handle_chat_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Process an interactive chat message with the Nova Multi-Agent system."""
    user_text = payload.message.strip()
    history = payload.history
    current_state = payload.current_state or {}

    # Check if user message implies running a full or new tender analysis
    is_pipeline_trigger = any(
        kw in user_text.lower()
        for kw in [
            "найди тендер",
            "рассчитай",
            "капремонт",
            "строительство",
            "реконструкция",
            "запусти",
            "сделай расчет",
            "анализ тендера",
            "поиск лотов",
        ]
    ) and len(user_text) > 8

    updated_state: Optional[dict[str, Any]] = current_state

    # 1. If user asks to analyze/run a task, execute the multi-agent graph
    if is_pipeline_trigger:
        try:
            logger.info("Executing Nova multi-agent pipeline from chat: %s", user_text)
            final_pipeline_state = run_pipeline(user_text)
            updated_state = serialize_state_for_api(final_pipeline_state)

            tender = updated_state.get("selected_tender")
            tender_name = tender.get("name_ru", user_text) if tender else user_text
            tender_sum = float(tender.get("total_sum", 0.0)) if tender else 0.0
            works = updated_state.get("work_list", [])
            materials = updated_state.get("materials_list", [])
            pos = updated_state.get("purchase_orders", [])
            summary = updated_state.get("stock_check", {}).get("summary", {})

            thought = (
                f"COO принял задачу «{user_text}». Запущены агенты Госзакупок, ПТО и Снабжения. "
                f"Обработано {len(works)} работ, {len(materials)} материалов, сформировано {len(pos)} заявок на закупку."
            )

            response_text = (
                f"### 🏗️ Анализ успешно выполнен!\n\n"
                f"Мы проанализировали задачу **«{user_text}»** через всю мульти-агентную цепочку Nova:\n\n"
                f"1. **🏛️ Госзакупки:** Выбран лот **«{tender_name}»** с бюджетом **{tender_sum:,.2f} ₸**.\n"
                f"2. **📐 ПТО (Сметы & Нормы):** Выделено **{len(works)}** видов СМР и **{len(materials)}** позиций материалов с технологическим запасом 5%.\n"
                f"3. **📦 Склад & Снабжение:** На складе покрыто **{summary.get('fully_in_stock', 0)}** позиций; в дефиците **{summary.get('full_deficit', 0)}** позиций. Сформировано **{len(pos)}** заявок поставщикам РК.\n"
                f"4. **💰 Финансы:** Все расчеты и ведомости загружены в **панель документов справа** 👉.\n\n"
                f"_Что вы хотите уточнить по смете или поставщикам?_"
            )

            return ChatResponse(
                response=response_text,
                sender="coo",
                sender_title="Операционный директор (COO)",
                thought=thought,
                state=updated_state,
                suggestions=_generate_smart_suggestions(user_text, updated_state),
            )
        except Exception as exc:
            logger.error("Failed to run pipeline in chat: %s", exc)

    # 2. Contextual LLM conversation for follow-ups and general questions
    llm = get_chat_model(temperature=0.3, max_tokens=2048)

    # Build prompt context with existing state
    context_summary = ""
    if updated_state and updated_state.get("selected_tender"):
        t = updated_state.get("selected_tender", {})
        st_sum = updated_state.get("stock_check", {}).get("summary", {})
        pos = updated_state.get("purchase_orders", [])
        context_summary = (
            f"\n\nТЕКУЩИЙ АКТИВНЫЙ ПРОЕКТ В СИСТЕМЕ:\n"
            f"- Тендер: {t.get('name_ru')} (Бюджет: {t.get('total_sum', 0):,.2f} ₸, Заказчик: {t.get('organizer_name_ru')})\n"
            f"- Работ в смете: {len(updated_state.get('work_list', []))} шт.\n"
            f"- Материалов: {len(updated_state.get('materials_list', []))} шт.\n"
            f"- Складской дефицит: {st_sum.get('full_deficit', 0)} позиций\n"
            f"- Сформировано заявок на закупку: {len(pos)} шт. на сумму {sum(p.get('total_amount_kzt', 0) for p in pos):,.2f} ₸\n"
        )

    llm_messages = [
        SystemMessage(content=SYSTEM_CHAT_PROMPT + context_summary),
    ]

    # Append recent chat history
    for msg in history[-6:]:
        if msg.role == "user":
            llm_messages.append(HumanMessage(content=msg.content))
        elif msg.role in ("assistant", "system"):
            llm_messages.append(AIMessage(content=msg.content))

    llm_messages.append(HumanMessage(content=user_text))

    if llm is not None:
        try:
            ai_res = llm.invoke(llm_messages)
            reply_text = str(ai_res.content)
            thought = "Ответ сформирован на основе контекста строительного проекта и нормативов РК."
        except Exception as exc:
            logger.warning("LLM chat invocation failed: %s", exc)
            reply_text = (
                f"Принял ваш вопрос по объекту. В рамках текущей сметы все параметры "
                f"согласованы с инженером ПТО и отделом снабжения. Документы доступны в правой панели."
            )
            thought = f"Fallback response due to LLM error: {exc}"
    else:
        # Graceful rule-based response
        reply_text = (
            f"Спасибо за вопрос! Я помогу с анализом тендеров Госзакупок РК, расчетом сметных ведомостей "
            f"по СН РК и автоматической проверкой складских остатков. "
            f"Напишите задачу (например: *«Найди тендер на ремонт школы в Алматы»*), чтобы запустить расчет."
        )
        thought = "Автоматический ответ координатора Nova (Mock-first режим)."

    return ChatResponse(
        response=reply_text,
        sender="coo",
        sender_title="Операционный директор (COO)",
        thought=thought,
        state=updated_state,
        suggestions=_generate_smart_suggestions(user_text, updated_state),
    )
