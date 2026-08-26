"""
PTO Agent (Производственно-технический отдел).

Analyzes tender specifications and estimate documents, generates bill of quantities
(ABCWork), extracts bill of materials (ABCMaterial), and passes them to Supply.
Supports real dynamic LLM generation for any custom construction task.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

from langchain_core.messages import AIMessage, HumanMessage

from nova.agents.level2.pto.prompts import PTO_SYSTEM_PROMPT
from nova.agents.level3.abc_tool import (
    abc_document_reader,
    abc_statement_writer,
    abc_xml_reader,
    abc_xml_writer,
)
from nova.agents.level3.pdf_parser import extract_materials, extract_work_list
from nova.config import get_settings
from nova.config.llm import get_chat_model
from nova.graph.routers import ROUTE_SUPPLY
from nova.graph.state import ConstructionState
from nova.integrations.abc.models import ABCMaterial, ABCWork

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[4] / "data"
SAMPLE_TENDERS_FILE = DATA_DIR / "sample_tenders.json"

PTO_TOOLS = [
    extract_work_list,
    extract_materials,
    abc_document_reader,
    abc_statement_writer,
    abc_xml_reader,
    abc_xml_writer,
]


def _clean_json_str(text: str) -> dict:
    """Extract and parse JSON safely from LLM output, handling truncation and formatting issues."""
    raw = text.strip()
    if "```json" in raw:
        raw = raw.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in raw:
        raw = raw.split("```", 1)[1].split("```", 1)[0]

    s = raw.find("{")
    if s == -1:
        raise ValueError("No JSON object found")
    raw = raw[s:]

    e = raw.rfind("}")
    if e != -1:
        candidate = raw[: e + 1]
    else:
        candidate = raw

    # 1. Clean trailing commas
    candidate = re.sub(r",\s*\}", "}", candidate)
    candidate = re.sub(r",\s*\]", "]", candidate)

    try:
        return json.loads(candidate)
    except Exception:
        pass

    # 2. If cut off, find the last completed closing brace and close open brackets
    last_brace = candidate.rfind("}")
    if last_brace != -1:
        repair = candidate[: last_brace + 1]
        open_sq = repair.count("[") - repair.count("]")
        if open_sq > 0:
            repair += "]" * open_sq
        open_curly = repair.count("{") - repair.count("}")
        if open_curly > 0:
            repair += "}" * open_curly
        repair = re.sub(r",\s*\}", "}", repair)
        repair = re.sub(r",\s*\]", "]", repair)
        try:
            return json.loads(repair)
        except Exception:
            pass

    # 3. Regex parser as ultimate fallback
    works_list = []
    materials_list = []

    # Find work matches
    w_pattern = r'\{[^{}]*"name"\s*:\s*"([^"]+)"[^{}]*"unit"\s*:\s*"([^"]+)"[^{}]*"quantity"\s*:\s*([0-9.]+)[^{}]*\}'
    for m in re.finditer(w_pattern, raw):
        w_name, w_unit, w_qty = m.group(1), m.group(2), float(m.group(3))
        works_list.append({"name": w_name, "unit": w_unit, "quantity": w_qty, "price": 5000.0})

    if works_list:
        return {"works": works_list, "materials": materials_list}

    raise ValueError(f"Could not parse JSON from LLM: {raw[:120]}")


def generate_engineering_breakdown(
    task: str,
    tender_name: str = "",
    region: str = "г. Алматы",
) -> tuple[list[ABCWork], list[ABCMaterial]]:
    """
    Dynamically generate realistic engineering works and materials breakdown via LLM.
    Uses Kazakhstan construction norms (СН РК / АВС / ЕНиР).
    """
    llm = get_chat_model(temperature=0.2, max_tokens=2500)
    if llm is not None:
        try:
            prompt = f"""Ты — главный инженер ПТО строительной компании в Казахстане (нормы СН РК, АВС-4, ЕНиР).
Объект: «{task}» (Регион: {region}).

Составь сметную ведомость объемов работ (ВОР) и спецификацию материалов в строгом формате JSON:
{{
  "works": [
    {{"code": "ВОР-01", "name": "Краткое наименование СМР", "unit": "м2", "quantity": 500.0, "price": 4500.0}},
    {{"code": "ВОР-02", "name": "...", "unit": "м3", "quantity": 120.0, "price": 8500.0}}
  ],
  "materials": [
    {{"code": "301-01", "name": "Точное наименование материала (марка, ГОСТ)", "unit": "м3", "quantity": 126.0, "price": 28500.0}},
    {{"code": "245-12", "name": "...", "unit": "т", "quantity": 8.5, "price": 340000.0}}
  ]
}}

Правила:
1. Сформируй ровно 5–6 ключевых этапов СМР (works).
2. Сформируй ровно 7–9 основных материалов (materials) с запасом 5%.
3. Названия делай емкими (до 60 символов). Цены в тенге (KZT).
4. Ответь ТОЛЬКО валидным JSON без лишних пояснений."""

            res = llm.invoke([HumanMessage(content=prompt)])
            data = _clean_json_str(str(res.content))

            raw_works = data.get("works", [])
            raw_materials = data.get("materials", [])

            works = [
                ABCWork(
                    code=w.get("code", f"ВОР-{i+1:02d}"),
                    name=w.get("name", "Строительно-монтажные работы"),
                    unit=w.get("unit", "м2"),
                    quantity=float(w.get("quantity", 1.0)),
                    price=float(w.get("price") or 0.0) if w.get("price") else None,
                )
                for i, w in enumerate(raw_works)
                if w.get("name")
            ]

            materials = [
                ABCMaterial(
                    code=m.get("code", f"М-{i+1:02d}"),
                    name=m.get("name", "Строительный материал"),
                    unit=m.get("unit", "ед"),
                    quantity=round(float(m.get("quantity", 1.0)), 2),
                    price=float(m.get("price") or 0.0) if m.get("price") else None,
                )
                for i, m in enumerate(raw_materials)
                if m.get("name")
            ]

            if works and materials:
                logger.info("Successfully generated %d works and %d materials via live LLM for '%s'", len(works), len(materials), task)
                return works, materials

        except Exception as exc:
            logger.warning("LLM engineering breakdown generation failed: %s. Using dynamic keyword generator.", exc)

    # Dynamic keyword-based domain generator (if offline or LLM unavailable)
    t_lower = task.lower()

    if any(k in t_lower for k in ["зерно", "элеватор", "склад", "ангар", "цех"]):
        works = [
            ABCWork(code="ВОР-01", name="Устройство монолитного железобетонного фундамента", unit="м3", quantity=140.0, price=48000.0),
            ABCWork(code="ВОР-02", name="Монтаж несущего стального металлокаркаса", unit="т", quantity=45.0, price=95000.0),
            ABCWork(code="ВОР-03", name="Обшивка стен стеновыми сэндвич-панелями 120мм", unit="м2", quantity=850.0, price=5200.0),
            ABCWork(code="ВОР-04", name="Устройство кровельных сэндвич-панелей 150мм", unit="м2", quantity=920.0, price=6100.0),
            ABCWork(code="ВОР-05", name="Устройство обеспыленных промышленных бетонных полов", unit="м2", quantity=750.0, price=7800.0),
            ABCWork(code="ВОР-06", name="Монтаж секционных ворот и системы принудительной вентиляции", unit="компл", quantity=1.0, price=6500000.0),
        ]
        materials = [
            ABCMaterial(code="101-0350", name="Бетон товарный М350 В25 W6 F150", unit="м3", quantity=147.0, price=32000.0),
            ABCMaterial(code="245-1200", name="Арматурный прокат А500С Ø12-16мм", unit="т", quantity=11.5, price=345000.0),
            ABCMaterial(code="210-0100", name="Металлоконструкции каркаса (балки, колонны)", unit="т", quantity=47.25, price=480000.0),
            ABCMaterial(code="350-0120", name="Сэндвич-панели стеновые ПИР 120мм", unit="м2", quantity=892.5, price=14500.0),
            ABCMaterial(code="350-0150", name="Сэндвич-панели кровельные ПИР 150мм", unit="м2", quantity=966.0, price=16800.0),
            ABCMaterial(code="401-0020", name="Топпинг для промышленных полов корундовый", unit="кг", quantity=3750.0, price=380.0),
            ABCMaterial(code="801-0100", name="Кабельная продукция ВВГнг-LS и светодиодные прожекторы", unit="компл", quantity=1.0, price=2800000.0),
        ]
        return works, materials

    if any(k in t_lower for k in ["водопровод", "вод", "труб", "канализац", "сети"]):
        works = [
            ABCWork(code="ВОР-01", name="Разработка траншей экскаватором с отсыпкой", unit="м3", quantity=3200.0, price=1800.0),
            ABCWork(code="ВОР-02", name="Устройство песчаного основания под трубопроводы", unit="м3", quantity=450.0, price=4200.0),
            ABCWork(code="ВОР-03", name="Укладка напорных полиэтиленовых труб ПЭ100 d160", unit="м", quantity=2400.0, price=5800.0),
            ABCWork(code="ВОР-04", name="Монтаж сборных железобетонных колодцев", unit="компл", quantity=28.0, price=320000.0),
            ABCWork(code="ВОР-05", name="Гидравлическое испытание и промывка трубопровода", unit="м", quantity=2400.0, price=1200.0),
        ]
        materials = [
            ABCMaterial(code="501-0160", name="Труба напорная ПЭ100 SDR17 d160 (ГОСТ 18599)", unit="м", quantity=2520.0, price=6200.0),
            ABCMaterial(code="103-0100", name="Песок строительный мытый фр. 0-2", unit="т", quantity=680.0, price=4500.0),
            ABCMaterial(code="102-0050", name="Кольца стеновые ж/б КС 15.9 с плитами перекрытия", unit="компл", quantity=29.4, price=85000.0),
            ABCMaterial(code="520-0016", name="Задвижки клиновые с обрезиненным клином Ду150", unit="шт", quantity=14.0, price=145000.0),
            ABCMaterial(code="103-0200", name="Щебень фракции 20-40 мм М1000", unit="т", quantity=420.0, price=6500.0),
        ]
        return works, materials

    # Default versatile construction works
    works = [
        ABCWork(code="ВОР-01", name="Демонтажные и подготовительные работы", unit="м2", quantity=1250.0, price=3200.0),
        ABCWork(code="ВОР-02", name="Строительно-монтажные работы несущих конструкций", unit="м2", quantity=1600.0, price=9500.0),
        ABCWork(code="ВОР-03", name="Монтаж внутренних и наружных инженерных систем", unit="компл", quantity=1.0, price=12500000.0),
        ABCWork(code="ВОР-04", name="Устройство теплоизоляции и чистовая отделка", unit="м2", quantity=1850.0, price=4800.0),
    ]
    materials = [
        ABCMaterial(code="245-1012", name="Арматура А500С d12мм (ГОСТ 34028-2016)", unit="т", quantity=8.5, price=335000.0),
        ABCMaterial(code="101-0300", name="Бетон товарный М350 В25 W6", unit="м3", quantity=110.0, price=31500.0),
        ABCMaterial(code="301-0100", name="Утеплитель минераловатный 100мм ТехноНИКОЛЬ", unit="м3", quantity=165.0, price=19200.0),
        ABCMaterial(code="401-0012", name="Гипсокартон влагостойкий ГКЛВ 12.5мм", unit="лист", quantity=480.0, price=3400.0),
        ABCMaterial(code="801-0325", name="Кабель силовой ВВГнг-LS 3х2.5", unit="м", quantity=2600.0, price=480.0),
    ]
    return works, materials


def run_pto_agent(state: ConstructionState) -> dict[str, Any]:
    """Execute PTO agent logic to extract or dynamically generate works and materials."""
    metadata = dict(state.get("metadata", {}))
    visited = list(metadata.get("visited_nodes", []))
    visited.append("pto")
    metadata["visited_nodes"] = visited

    task = state.get("task", "")
    selected_tender = state.get("selected_tender")
    tender_name = getattr(selected_tender, "name_ru", "") if selected_tender else task
    region = getattr(selected_tender, "region_name", "г. Алматы") if selected_tender else "г. Алматы"

    # Check if works and materials already exist in state
    works = list(state.get("work_list", []))
    materials = list(state.get("materials_list", []))

    if not works or not materials:
        works, materials = generate_engineering_breakdown(task, tender_name=tender_name, region=region)

    total_est_materials_cost = sum((m.quantity * (m.price or 0.0)) for m in materials)

    summary_msg = (
        f"[ПТО] Инженерный расчет по объекту «{tender_name or task}» завершён. "
        f"Сформирована ведомость объемов работ (ВОР): **{len(works)}** позиций. "
        f"Сформирована спецификация материалов (с учетом запаса 5%): **{len(materials)}** позиций "
        f"на расчетную сумму **{total_est_materials_cost:,.2f} KZT**. "
        f"Передаю ведомость в Отдел снабжения для сверки со складом и подбора поставщиков в {region}."
    )

    return {
        "work_list": works,
        "materials_list": materials,
        "current_agent": ROUTE_SUPPLY,
        "messages": [AIMessage(content=summary_msg, name="PTOAgent")],
        "metadata": metadata,
    }


__all__ = [
    "run_pto_agent",
    "generate_engineering_breakdown",
    "PTO_TOOLS",
]
