# NOVA — Прогресс разработки

**Последнее обновление:** 2026-03-10 (MVP Этапы 2, 3, 4, 5.1)
**Ветка:** main
**Python:** 3.11.x
**Стек:** LangGraph + LangChain + Claude Sonnet 4.6 + FastAPI + SQLAlchemy 2.0 + SQLite/PostgreSQL + Redis

---

## 📊 ОБЩИЙ ПРОГРЕСС

| Этап | Название | Статус |
|------|----------|--------|
| 1 | Фундамент проекта | ✅ Завершён |
| 2 | Интеграции и инструменты | ✅ Завершён |
| 3 | Агенты уровня 2 | ✅ Завершён |
| 4 | COO Оркестратор и граф | ✅ Завершён |
| 5.1 | FastAPI REST API | ✅ Завершён |

---

## Чеклист реализации

### ЭТАП 1 — Фундамент проекта
- [x] Шаг 1.1 — Инициализация репозитория и структуры проекта (2026-02-28)
- [x] Шаг 1.2 — Конфигурация и настройки (Pydantic BaseSettings) (2026-03-01)
- [x] Шаг 1.3 — SharedState и модели данных (2026-03-03)
- [x] Шаг 1.4 — База данных и миграции (PostgreSQL + Alembic) (2026-03-03)
- [x] Шаг 1.5 — Инфраструктура Redis и скелет основного графа (2026-03-06)

### ЭТАП 2 — Интеграции и инструменты (Level 3 Tools)
- [x] Шаг 2.1 — GraphQL клиент goszakup.gov.kz с Graceful Fallback на `data/sample_tenders.json`
- [x] Шаг 2.2 — Инструменты поиска и оценки тендеров (`goszakup_tool.py`, `tender_scorer.py`)
- [x] Шаг 2.3 — Парсер документов PDF/DOCX (`pdf_parser.py`)
- [x] Шаг 2.4 — PDF-driven ABC adapter + JSON contract (`abc_tool.py`, reader/writer)
- [x] Шаг 2.5 — Инструменты склада, поставщиков и заявок (`stock_tool.py`, `order_tool.py`, `supplier_tool.py`)

### ЭТАП 3 — Агенты уровня 2
- [x] Шаг 3.1 — Агент Закупщик (Procurement Agent) — поиск, скоринг лотов РК, выбор топ-тендера
- [x] Шаг 3.2 — Агент ПТО (PTO Agent) — извлечение ведомости работ и материалов, нормативы РК / АВС (+5% запас)
- [x] Шаг 3.3 — Агент Снабженец (Supply Agent) — складская сверка, расчет дефицита (+10% буфер), подбор поставщиков, URGENT флаги
- [x] Шаг 3.4 — Межагентная передача контекста через `ConstructionState`
- [x] Шаг 3.5 — Системные промпты и детерминированный fallback

### ЭТАП 4 — COO Оркестратор и граф
- [x] Шаг 4.1 — COO Agent — декомпозиция задач и генерация структурированного Executive Summary
- [x] Шаг 4.2 — Основной граф LangGraph `StateGraph(ConstructionState)`
- [x] Шаг 4.3 — Обработка ошибок и отказоустойчивость
- [x] Шаг 4.4 — Сквозной пайплайн `run_pipeline(...)`
- [x] Шаг 4.5 — Полнофункциональный CLI интерфейс (`nova/cli.py`, `app/cli.py`)

### ЭТАП 5 — API, тесты и деплой
- [x] Шаг 5.1 — FastAPI сервер (`nova/api/main.py`, `/health`, `/api/v1/tasks`, `/api/v1/tasks/{id}`, `/report`)
- [ ] Шаг 5.2 — WebSocket стриминг
- [x] Шаг 5.3 — Тестовое покрытие (129 тестов, 82% coverage)
- [ ] Шаг 5.4 — Мониторинг и логирование (LangSmith)
- [ ] Шаг 5.5 — Деплой в production

---

## Заметки по этапам 2, 3, 4, 5.1 (2026-03-10)

### 1. Данные и фикстуры (Data Fixtures)
- `data/sample_tenders.json`: 4 реалистичных строительных тендера РК (капремонт школы в Алматы, сети водоснабжения в Астане, благоустройство парка в Шымкенте, детский сад в Караганде).
- `data/warehouse_mock.json`: 35 позиций строительных материалов (арматура, бетон, кирпич, ПНД трубы, минвата, сухие смеси, кабель, светильники, МАФ и др.) с ценами в KZT, остатками и резервами.
- `data/suppliers_mock.json`: каталог ведущих поставщиков стройматериалов РК (ТОО «КазАрматура Трейд», ТОО «АзияБетон Плюс», ТОО «Астана СтройКомплект», ТОО «ТехноНиколь Казахстан» и др.).

### 2. Инструменты 3 Уровня (Level 3 Tools)
- `nova/integrations/goszakup/client.py` & `queries.py`: GraphQL клиент для goszakup.gov.kz с прозрачным mock-first fallback режимом.
- `nova/agents/level3/tender_scorer.py`: алгоритм скоринга лотов (бюджет 30%, сроки 20%, регион 20%, способ закупки 15%, репутация заказчика 15%).
- `nova/agents/level3/goszakup_tool.py`: LangChain tools `goszakup_search`, `analyze_tender`, `score_tender`, `download_tender_docs`.
- `nova/agents/level3/stock_tool.py`: `check_stock`, `batch_check_stock`.
- `nova/agents/level3/order_tool.py`: `create_purchase_order`, `build_purchase_orders_from_stock_check` с обязательным страховым запасом +10% и выделением URGENT-позиций (>80% дефицита).
- `nova/agents/level3/supplier_tool.py`: `find_supplier`, `list_suppliers`.
- `nova/agents/level3/pdf_parser.py`: парсинг PDF/DOCX и интеграция с ABC-адаптером.

### 3. Агенты 2 Уровня (Level 2 Agents)
- **Гос. Закупщик** (`nova/agents/level2/procurement/`): поиск, скоринг лотов, отбор оптимального тендера, передача в ПТО.
- **Инженер ПТО** (`nova/agents/level2/pto/`): анализ ТЗ и сметных нормативов, формирование ВОР и ресурсной ведомости (+5% технологический запас).
- **Снабженец** (`nova/agents/level2/supply/`): сверка со складом, расчет чистого дефицита (+10% страховой буфер), подбор поставщиков, формирование Purchase Orders.

### 4. COO Оркестратор и Граф LangGraph (Level 1)
- **COO** (`nova/agents/coo/`): декомпозиция задач, контроль передачи контекста, генерация подробного Исполнительного Отчета (Executive Summary) с финансовым балансом (выручка, затраты, валовая прибыль) и управленческой рекомендацией.
- `nova/graph/main_graph.py`: полнофункциональный `StateGraph(ConstructionState)` с функцией `run_pipeline(task)`.

### 5. Интерфейсы запуска: CLI и FastAPI
- **CLI** (`nova/cli.py`, `app/cli.py`):
  - `python -m nova.cli run --task "..." [--output markdown|json|text]`
  - `python -m nova.cli status --task-id <UUID>`
  - `python -m nova.cli history`
  - `python -m nova.cli config check`
- **FastAPI** (`nova/api/main.py`, `routes/health.py`, `routes/tasks.py`):
  - `GET /health` — статус базы данных, Redis, Goszakup и LLM
  - `POST /api/v1/tasks` — запуск пайплайна с записью в `tasks`, `tender_records`, `agent_logs`
  - `GET /api/v1/tasks/{id}` — статус и результат выполнения
  - `GET /api/v1/tasks` — история задач
  - `GET /api/v1/tasks/{id}/report` — структурированный отчет `AgentReport`

### 6. Результаты тестирования
```bash
./venv/bin/pytest --cov=nova
```
- **129 passed** (93 существующих + 36 новых тестов)
- **82% тестовое покрытие**
- Все unit, integration и e2e тесты проходят успешно.
