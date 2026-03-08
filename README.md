# Nova — Мульти-агентная система для строительства

> Иерархическая ИИ-система на базе LangGraph для автоматизации тендерного пайплайна строительной компании в Казахстане

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green)](https://langchain.com/langgraph)
[![Claude](https://img.shields.io/badge/Claude-Sonnet_4.6-orange)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-gray)](LICENSE)

-----

## 📋 Оглавление

- [О проекте](#о-проекте)
- [Архитектура](#архитектура)
- [Стек технологий](#стек-технологий)
- [Быстрый старт](#быстрый-старт)
- [Структура проекта](#структура-проекта)
- [Агенты системы](#агенты-системы)
- [Интеграции](#интеграции)
- [Конфигурация](#конфигурация)
- [Roadmap](#roadmap)

-----

## О проекте

Construction AI — многоуровневая система ИИ-агентов для автоматизации операционных процессов строительной компании.

**MVP реализует тендерный пайплайн:**

```
Пользователь → COO Агент → Гос. Закупщик → ПТО → Снабженец → Отчёт
```

Система самостоятельно находит релевантные государственные тендеры на `goszakup.gov.kz`, анализирует техническую документацию, формирует ресурсную ведомость через АВС Сметные решения и создаёт заявки на материалы.

### Что решает система

|Проблема                                 |Решение                                    |
|-----------------------------------------|-------------------------------------------|
|Ручной мониторинг тендеров (часы)        |Автоматический поиск и скоринг за минуты   |
|Анализ ТЗ занимает дни                   |ПТО-агент парсит документацию за минуты    |
|Ручная проверка складских остатков       |Автоматическая сверка и формирование заявок|
|Потеря данных при передаче между отделами|Единый SharedState, сквозная передача      |

-----

## Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                   УРОВЕНЬ 1                             │
│              ┌─────────────────┐                        │
│              │   COO Агент     │  ← Входящая задача     │
│              │ (Supervisor)    │                        │
│              └────────┬────────┘                        │
├───────────────────────┼─────────────────────────────────┤
│                   УРОВЕНЬ 2                             │
│     ┌─────────────────┼─────────────────┐              │
│     ↓                 ↓                 ↓              │
│ ┌───────────┐  ┌─────────────┐  ┌──────────────┐      │
│ │ Гос.      │  │ ПТО Агент   │  │  Снабженец   │      │
│ │ Закупщик  │→ │             │→ │              │      │
│ └───────────┘  └─────────────┘  └──────────────┘      │
│     ↕ ↕ ↕ (агенты могут обмениваться данными)          │
├─────────────────────────────────────────────────────────┤
│                   УРОВЕНЬ 3 (Tools)                     │
│  goszakup_search │ abc_reader │ stock_checker │ ...     │
└─────────────────────────────────────────────────────────┘
```

### Поток данных

```mermaid
graph LR
    U[Пользователь] --> COO[COO Агент]
    COO --> P[Гос. Закупщик]
    P -->|Тендер + ТЗ| COO
    COO --> PTO[ПТО Агент]
    PTO -->|Ведомость материалов| COO
    COO --> S[Снабженец]
    S -->|Заявки на закупку| COO
    COO --> R[Финальный отчёт]
    R --> U
```

-----

## Стек технологий

|Категория          |Технология             |Версия|
|-------------------|-----------------------|------|
|Оркестрация агентов|LangGraph              |0.2+  |
|LLM                |Claude Sonnet 4.6      |—     |
|LLM Framework      |LangChain              |0.3+  |
|Мониторинг         |LangSmith              |—     |
|API тендеров       |goszakup.gov.kz GraphQL|v3    |
|Бэкенд             |FastAPI                |0.115+|
|БД                 |PostgreSQL             |16+   |
|Кэш/Очереди        |Redis                  |7+    |
|Векторная БД       |Qdrant                 |1.7+  |
|Python             |—                      |3.11+ |

-----

## Быстрый старт

### 1. Клонирование и установка зависимостей

```bash
git clone https://github.com/your-org/construction-ai.git
cd construction-ai

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
cp .env.example .env
```

Заполните `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
GOSZAKUP_TOKEN=your_token_here
DATABASE_URL=postgresql://user:pass@localhost:5432/construction_ai
REDIS_URL=redis://localhost:6379
LANGSMITH_API_KEY=your_key_here
```

### 3. Получение токена goszakup.gov.kz

1. Зайдите на `goszakup.gov.kz` под ЭЦП организации
1. Перейдите: Профиль → Настройки → API токен
1. Скопируйте токен в `.env`

### 4. Запуск инфраструктуры

```bash
# Docker (рекомендуется)
docker-compose up -d postgres redis qdrant

# Или вручную — PostgreSQL и Redis
```

### 5. Миграции БД

```bash
alembic upgrade head
```

### 6. Запуск системы

```bash
# API сервер
uvicorn app.main:app --reload --port 8000

# Или через CLI
python -m app.cli run --task "Найти строительные тендеры в Алматы с бюджетом до 50 млн тенге"
```

-----

## Структура проекта

```
construction_ai/
│
├── agents/                     # Агенты системы
│   ├── coo/
│   │   ├── __init__.py
│   │   ├── agent.py            # COO Supervisor агент
│   │   └── prompts.py          # Системный промпт COO
│   │
│   ├── level2/
│   │   ├── procurement/
│   │   │   ├── agent.py        # Гос. Закупщик
│   │   │   └── prompts.py
│   │   ├── pto/
│   │   │   ├── agent.py        # ПТО агент
│   │   │   └── prompts.py
│   │   └── supply/
│   │       ├── agent.py        # Снабженец
│   │       └── prompts.py
│   │
│   └── level3/                 # Tools (инструменты)
│       ├── goszakup_tool.py    # GraphQL клиент
│       ├── abc_tool.py         # ABC PDF/JSON adapter
│       ├── pdf_parser.py       # Парсинг документов
│       ├── stock_tool.py       # Склад
│       └── order_tool.py       # Заявки
│
├── graph/
│   ├── __init__.py
│   ├── main_graph.py           # Основной граф LangGraph
│   ├── state.py                # SharedState TypedDict
│   └── routers.py              # Условная маршрутизация
│
├── integrations/
│   ├── goszakup/
│   │   ├── client.py           # GraphQL клиент goszakup
│   │   ├── queries.py          # GraphQL запросы
│   │   └── models.py           # Pydantic модели
│   └── abc/
│       ├── reader.py           # Чтение PDF АВС в typed models
│       ├── writer.py           # Запись JSON statement
│       └── models.py
│
├── api/
│   ├── main.py                 # FastAPI приложение
│   ├── routes/
│   │   ├── tasks.py            # POST /tasks
│   │   └── status.py           # GET /tasks/{id}/status
│   └── schemas.py
│
├── db/
│   ├── models.py               # SQLAlchemy модели
│   └── migrations/             # Alembic миграции
│
├── config/
│   ├── settings.py             # Pydantic Settings
│   └── logging.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/
│   ├── SYSTEM_INSTRUCTION.md   # Системная инструкция
│   ├── API.md                  # API документация
│   └── ARCHITECTURE.md
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

-----

## Агенты системы

### 🎯 COO Агент (Уровень 1)

Главный оркестратор системы. Реализован через паттерн `Supervisor` из `langgraph-supervisor`.

```python
from langgraph_supervisor import create_supervisor
from langchain_anthropic import ChatAnthropic

coo = create_supervisor(
    agents=[procurement_agent, pto_agent, supply_agent],
    model=ChatAnthropic(model="claude-sonnet-4-6", temperature=0.1),
    prompt=open("agents/coo/prompts.py").read()
)
```

### 🔍 Государственный Закупщик (Уровень 2)

Интегрируется с `goszakup.gov.kz` через официальный GraphQL API v3.

**Пример запроса:**

```graphql
query FindTenders($filter: AnnouncementFilter) {
  Announcement(filter: $filter, limit: 20) {
    id
    nameRu
    totalSum
    endDate
    customerNameRu
    lots {
      nameRu
      amount
    }
  }
}
```

### 📐 ПТО Агент (Уровень 2)

Анализирует техническую документацию и работает с АВС через PDF-driven adapter.

```python
# Чтение PDF-документа АВС
@tool
def abc_document_reader(file_path: str) -> dict:
    """Читает PDF из АВС и возвращает нормализованный statement"""
    return read_abc_document(file_path).model_dump(mode="json")
```

### 📦 Снабженец (Уровень 2)

Проверяет склад и формирует заявки на материалы с учётом дефицита.

-----

## Интеграции

### goszakup.gov.kz GraphQL API

```bash
# Документация API
https://ows.goszakup.gov.kz/help/v3/schema/

# Эндпоинт
POST https://ows.goszakup.gov.kz/v3/graphql
Authorization: Bearer {YOUR_TOKEN}
```

**Доступные данные:** объявления о закупках, реестр договоров, реестр поставщиков, планы закупок.

### АВС Сметные решения

Интеграция через файловый обмен и PDF-driven adapter:

```
АВС PDF → ПТО Агент читает → нормализует statement → 
→ формирует ресурсную ведомость → JSON contract для дальнейшей обработки
```

**Поддерживаемые форматы:** PDF (основной для текущего шага), JSON statement (внутренний контракт), Excel (XLSX). XML вынесен в будущий отдельный адаптер после появления образцов.

-----

## Конфигурация

### Переменные окружения

```env
# === LLM ===
ANTHROPIC_API_KEY=sk-ant-...

# === Госзакупки КЗ ===
GOSZAKUP_TOKEN=your_api_token
GOSZAKUP_GRAPHQL_URL=https://ows.goszakup.gov.kz/v3/graphql

# === База данных ===
DATABASE_URL=postgresql://user:password@localhost:5432/construction_ai
REDIS_URL=redis://localhost:6379

# === АВС интеграция ===
ABC_EXPORT_PATH=/data/abc/exports
ABC_IMPORT_PATH=/data/abc/imports

# === Мониторинг ===
LANGSMITH_API_KEY=your_key
LANGSMITH_PROJECT=construction-ai

# === Склад API (опционально) ===
WAREHOUSE_API_URL=http://warehouse-service:8001/api
WAREHOUSE_API_KEY=your_key
```

### Конфигурация агентов (`config/settings.py`)

```python
class AgentConfig(BaseSettings):
    # COO — строгие решения
    coo_temperature: float = 0.1
    coo_max_tokens: int = 4096
    
    # ПТО — работа с большими документами
    pto_max_tokens: int = 16384
    
    # Параметры поиска тендеров
    tender_search_limit: int = 20
    tender_min_budget: float = 1_000_000  # 1 млн тенге
    tender_min_deadline_days: int = 10
    tender_score_threshold: float = 60.0  # минимальный балл для отбора
```

-----

## Roadmap

### ✅ v0.1 MVP (в разработке)

- [x] Архитектура LangGraph Supervisor
- [x] Государственный Закупщик + GraphQL goszakup.gov.kz
- [x] ПТО Агент + парсинг документов + базовый ABC PDF/JSON adapter
- [x] Снабженец + проверка склада + формирование заявок
- [x] COO оркестратор
- [ ] FastAPI эндпоинты
- [ ] Базовое логирование через LangSmith

### 🔄 v0.2 (планируется)

- [ ] Агент Логист — планирование доставки
- [ ] Агент Сметчик — автоформирование сметы для тендера
- [ ] Human-in-the-Loop подтверждение перед участием в тендере
- [ ] Telegram-бот интерфейс
- [ ] История тендеров и аналитика

### 🎯 v1.0 (цель)

- [ ] Все 5 агентов в полной интеграции
- [ ] Автоматическая подача заявок на тендер (с подтверждением)
- [ ] Полная интеграция с АВС (PDF/JSON + будущий XML adapter)
- [ ] Дашборд мониторинга
- [ ] Мобильное приложение для уведомлений

-----

## Разработка

### Запуск тестов

```bash
# Все тесты
pytest

# Только unit
pytest tests/unit/

# С покрытием
pytest --cov=agents --cov-report=html
```

### Отладка агентов

```bash
# LangSmith трассировка включена автоматически
# Просмотр: https://smith.langchain.com

# Локальный дебаг через LangGraph Studio
langgraph studio
```

### Добавление нового агента

1. Создай папку в `agents/level2/new_agent/`
1. Опиши `agent.py` и `prompts.py`
1. Добавь инструменты в `agents/level3/`
1. Подключи агента в `graph/main_graph.py`
1. Обнови `SharedState` в `graph/state.py`
1. Обнови системную инструкцию в `docs/SYSTEM_INSTRUCTION.md`

-----

## Лицензия

MIT License — см. <LICENSE>

-----

## Контакты

По вопросам разработки и интеграции обращайтесь через Issues или Pull Requests.
