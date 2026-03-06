# NOVA — Прогресс разработки

**Последнее обновление:** 2026-03-06 (Шаг 1.5)
**Ветка:** main
**Python:** 3.11.x
**Стек:** LangGraph 1.0.10 + Claude Sonnet 4.6 + FastAPI + PostgreSQL + Redis

---

## ЭТАП 1 — Фундамент проекта

- [x] Шаг 1.1 — Инициализация репозитория и структуры проекта (2026-02-28)
- [x] Шаг 1.2 — Конфигурация и настройки (Pydantic BaseSettings) (2026-03-01)
- [x] Шаг 1.3 — SharedState и модели данных (2026-03-03)
- [x] Шаг 1.4 — База данных и миграции (PostgreSQL + Alembic) (2026-03-03)
- [x] Шаг 1.5 — Инфраструктура Redis и скелет основного графа (2026-03-06)

## ЭТАП 2 — Интеграции и инструменты

- [ ] Шаг 2.1 — Web-скрейпер goszakup.gov.kz (httpx + BeautifulSoup)
- [ ] Шаг 2.2 — Инструменты поиска и оценки тендеров
- [ ] Шаг 2.3 — Парсер документов (PDF/DOCX)
- [ ] Шаг 2.4 — Интеграция с АВС Сметные решения (XML)
- [ ] Шаг 2.5 — Инструменты склада и заявок (заглушки MVP)

## ЭТАП 3 — Агенты уровня 2

- [ ] Шаг 3.1 — Агент Закупщик (Procurement Agent)
- [ ] Шаг 3.2 — Агент ПТО (PTO Agent)
- [ ] Шаг 3.3 — Агент Снабженец (Supply Agent)
- [ ] Шаг 3.4 — Коммуникация между агентами и валидация данных
- [ ] Шаг 3.5 — Prompt engineering и оптимизация агентов

## ЭТАП 4 — COO Оркестратор и граф

- [ ] Шаг 4.1 — COO Agent (Supervisor)
- [ ] Шаг 4.2 — Основной LangGraph граф
- [ ] Шаг 4.3 — Обработка ошибок и отказоустойчивость
- [ ] Шаг 4.4 — Полный сквозной тест пайплайна
- [ ] Шаг 4.5 — CLI интерфейс

## ЭТАП 5 — API, тесты и деплой

- [ ] Шаг 5.1 — FastAPI сервер
- [ ] Шаг 5.2 — WebSocket стриминг
- [ ] Шаг 5.3 — Полное тестовое покрытие
- [ ] Шаг 5.4 — Мониторинг и логирование
- [ ] Шаг 5.5 — Деплой и финальная документация

---

## Заметки

### 2026-02-28 — Шаг 1.1

**Выполнено:**
- Репозиторий git уже инициализирован на ветке `claude/init-project-structure-v6niF`
- README.md и PLAN.md существовали в корне
- Создан `.gitignore` для Python проекта
- Создана полная структура пакета `nova/` со всеми подпакетами (16 `__init__.py` файлов)
- Созданы заглушки `.py` для всех модулей с маркерами TODO
- Создан `requirements.txt` с версиями на 2026-02-28
- Создано виртуальное окружение `venv/`, установлены все зависимости
- Создан `.env.example` с документацией всех переменных окружения
- Создан `.env` с placeholder-значениями (нужно заменить реальными ключами)
- Создан `pyproject.toml` для корректного импорта пакета в тестах
- Создан `progress.md` (этот файл)

**Установленные версии ключевых пакетов:**
- langgraph 1.0.10
- langchain-anthropic 1.3.4
- langgraph-supervisor 0.0.31
- fastapi 0.134.0
- sqlalchemy 2.0.47
- pytest 8.4.2

**Проверка:**
```
✅ python -c "import langgraph; import langchain_anthropic; print('OK')"  →  OK
✅ python -c "import nova; print('nova package OK')"  →  nova package OK
✅ pytest --collect-only  →  no tests collected (ожидаемо, тесты пишутся в шагах 1.2–5.3)
```

**Следующий шаг:** Шаг 1.2 — Реализовать `nova/config/settings.py` с Pydantic BaseSettings

---

### 2026-03-01 — Шаг 1.2

**Выполнено:**
- Реализован `nova/config/settings.py`: класс `Settings` на базе `pydantic_settings.BaseSettings`
  - Все переменные окружения из `.env.example` типизированы (SecretStr для секретов)
  - Singleton `settings` экспортируется для использования по всему приложению
  - Свойство `is_production` для проверки среды выполнения
- Реализован `nova/config/logging.py`: функция `setup_logging(level=None)`
  - Структурированный формат лога: `дата | уровень | модуль | сообщение`
  - Явная установка уровня корневого логгера (работает даже при уже настроенных handlers)
  - Подавление шумных логгеров (httpx, httpcore) до WARNING
  - Автоматическая активация LangSmith-трейсинга при `LANGCHAIN_TRACING_V2=true`
- Обновлён `nova/config/__init__.py`: re-export `settings` и `setup_logging`
- Создан `tests/unit/test_settings.py`: 12 unit-тестов

**Проверка:**
```
✅ python -m pytest tests/unit/test_settings.py -v  →  12 passed
✅ from nova.config import settings, setup_logging  →  импорт без ошибок
✅ settings.app_env  →  'development'
✅ settings.is_production  →  False
```

**Следующий шаг:** Шаг 1.3 — SharedState и модели данных

---

### 2026-03-03 — Шаг 1.3

**Выполнено:**
- Реализован `nova/graph/state.py`: класс `ConstructionState(TypedDict)` с 11 полями
  - `messages: Annotated[list[AnyMessage], add_messages]` — накопительный редьюсер LangGraph
  - Поля типизированы Pydantic-моделями (Tender, ABCWork, ABCMaterial)
- Реализованы `nova/integrations/goszakup/models.py`: Tender, TenderLot, TenderSearchFilter, TenderScore
- Реализованы `nova/integrations/abc/models.py`: ABCWork, ABCMaterial, ResourceStatement, EstimatePosition
- Реализованы `nova/api/schemas.py`: TaskRequest, TaskResponse, TaskStatus, AgentReport, TaskStatusEnum
- Создан `tests/unit/test_state.py`: 17 unit-тестов (4 классов)
- Создан `.env` с тестовыми значениями (требуется для загрузки `nova.config.settings`)

**Проверка:**
```
✅ python -m pytest tests/unit/test_state.py -v  →  17 passed
✅ python -m pytest tests/ -v  →  29 passed
✅ All imports OK
```

**Следующий шаг:** Шаг 1.4 — База данных и миграции (PostgreSQL + Alembic)

---

### 2026-03-03 — Шаг 1.4

**Выполнено:**
- Создан `docker-compose.yml` с сервисами `postgres:16-alpine`, `redis:7-alpine`, `qdrant/qdrant:latest`
  - Credentials выровнены с `.env`: `nova_user:nova_pass@localhost:5432/nova_db`
  - Именованные volumes для персистентности данных
  - Healthcheck-и для postgres и redis
- Реализован `nova/db/models.py`: SQLAlchemy 2.0 ORM-модели
  - `Task` — жизненный цикл задачи (UUID PK, status indexed, JSON output, timestamps)
  - `TenderRecord` — история найденных тендеров (FK→tasks CASCADE)
  - `AgentLog` — логи выполнения агентов (FK→tasks CASCADE)
  - `JSON().with_variant(JSONB(), "postgresql")` — JSONB на PostgreSQL, JSON на SQLite для тестов
  - `onupdate=_now` на `updated_at` для авто-обновления временной метки
- Реализован `nova/db/database.py`: управление движком и сессиями
  - `get_engine(url)` — публичная фабрика с авто-настройкой для SQLite
  - `get_session(eng)` — контекст-менеджер с явным rollback при исключениях
  - `get_db()` — FastAPI dependency с авто-commit/rollback
  - Ленивые синглтоны — импорт settings откладывается до первого вызова
- Инициализирован Alembic: `alembic init migrations`
  - `migrations/env.py` читает DATABASE_URL из settings (с fallback через os.environ)
  - `compare_type=True` для корректного autogenerate типов колонок
  - Импорт всех моделей через `from nova.db.models import Base`
- Создана первая миграция `e0f0d7fe3562_init.py`
  - Создаёт `tasks`, `tender_records`, `agent_logs` с корректными FK и индексами
  - `downgrade()` удаляет таблицы в обратном порядке зависимостей
  - Верифицирована в offline-режиме: `alembic upgrade head --sql` генерирует корректный DDL
- Создан `tests/unit/test_db.py`: 15 unit-тестов (TDD подход)
  - SQLite in-memory — без зависимости от живого PostgreSQL
  - TestModelsExist, TestTaskCRUD, TestTenderRecordCRUD, TestAgentLogCRUD, TestDatabaseHelpers

**Проверка:**
```
✅ python -m pytest tests/unit/test_db.py -v  →  15 passed
✅ python -m pytest tests/unit/ -v  →  44 passed (29 старых + 15 новых)
✅ python -c "from nova.db.models import Base; print(list(Base.metadata.tables.keys()))"
   → ['tasks', 'tender_records', 'agent_logs']
✅ DATABASE_URL=... alembic upgrade head --sql  →  корректный PostgreSQL DDL
⚠️  alembic upgrade head (применение к БД) — требует Docker/PostgreSQL, выполнить при наличии
```

**Следующий шаг:** Шаг 1.5 — Инфраструктура Redis и скелет основного графа

---

### 2026-03-06 — Шаг 1.5

**Выполнено:**
- Создан `nova/config/redis.py`: lazy Redis client, `check_redis_connection()`, JSON cache helpers `get_cache()`, `set_cache()`, `delete_cache()` с TTL по умолчанию 1800 секунд
- Обновлён `nova/config/__init__.py`: lazy re-export `settings`, `setup_logging` и Redis helpers без побочных эффектов при импорте
- Реализован `nova/graph/routers.py`: условные роутеры `route_after_coo`, `route_after_procurement`, `should_continue`, `is_complete` и стабильные route keys
- Реализован `nova/graph/main_graph.py`: skeleton LangGraph с нодами-заглушками `coo`, `procurement`, `pto`, `supply`, условными переходами и `build_graph()`
- Обновлён `nova/graph/__init__.py`: экспорт `build_graph`, `ConstructionState` и router helpers
- Обновлён `tests/conftest.py`: тестовые env defaults и общая фикстура `initial_construction_state`
- Созданы `tests/unit/test_redis.py`, `tests/unit/test_graph_routers.py`, `tests/e2e/test_graph_smoke.py`
  - Redis unit-тесты покрывают singleton, cache hit/miss, TTL, delete и ошибку сериализации
  - Router unit-тесты покрывают happy path, отсутствие тендера, ошибки и завершение графа
  - Smoke e2e тест проверяет прохождение пути `coo -> procurement -> pto -> supply`

**Проверка:**
```
✅ ./venv/bin/python -m pytest tests/ -v --tb=short  →  63 passed
✅ ./venv/bin/python -c "from nova.graph.main_graph import build_graph; g = build_graph(); print('Graph OK')"  →  Graph OK
✅ ./venv/bin/python -c "from nova.graph.main_graph import *; print('Import OK')"  →  Import OK
⚠️  При Python 3.14 остаётся внешнее предупреждение `langchain_core` о Pydantic v1 compatibility, но проверки проходят успешно
```

**Следующий шаг:** Шаг 2.1 — Web-скрейпер goszakup.gov.kz (httpx + BeautifulSoup)
