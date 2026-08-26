"""
Command Line Interface (CLI) for the Nova multi-agent construction system.

Usage:
  python -m nova.cli run --task "Поиск тендеров на капремонт школ в г. Алматы"
  python -m nova.cli status --task-id <UUID>
  python -m nova.cli history --limit 10
  python -m nova.cli config check
"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone

import click
from sqlalchemy import select

from nova.config import get_settings
from nova.config.redis import check_redis_connection
from nova.db.database import _get_app_engine, get_session
from nova.db.models import Base, Task
from nova.graph.main_graph import run_pipeline
from nova.integrations.goszakup.client import GoszakupClient


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


@click.group()
def cli():
    """Nova Multi-Agent Construction AI CLI."""
    pass


@cli.command("run")
@click.option("--task", "-t", required=True, help="Task description for the construction pipeline.")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["markdown", "json", "text"]),
    default="markdown",
    help="Format of the output report.",
)
def run_command(task: str, output: str):
    """Run full end-to-end tender procurement pipeline."""
    click.echo("=" * 70)
    click.echo("🏗️  NOVA — Мульти-агентная система строительных закупок (Казахстан)")
    click.echo("=" * 70)
    click.echo(f"[{_ts()}] 👔 [COO] Задача принята: «{task}»")

    # Step 1: Initialize DB tables if needed
    try:
        engine = _get_app_engine()
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    # Step 2: Run pipeline
    click.echo(f"[{_ts()}] 🚀 Запуск сквозного мульти-агентного пайплайна...")
    final_state = run_pipeline(task)

    # Step 3: Print agent intermediate logs
    messages = final_state.get("messages", [])
    for msg in messages:
        content = getattr(msg, "content", str(msg))
        if "[ЗАКУПЩИК]" in content:
            click.echo(f"[{_ts()}] 🔍 {content}")
        elif "[ПТО]" in content:
            click.echo(f"[{_ts()}] 📐 {content}")
        elif "[СНАБЖЕНИЕ]" in content:
            click.echo(f"[{_ts()}] 📦 {content}")
        elif "[COO]" in content:
            click.echo(f"[{_ts()}] 📊 {content}")

    # Save to database
    try:
        engine = _get_app_engine()
        with get_session(engine) as session:
            tender_dump = (
                final_state.get("selected_tender").model_dump(mode="json")
                if final_state.get("selected_tender")
                else None
            )
            db_task = Task(
                id=uuid.uuid4(),
                status="completed",
                input_text=task,
                output_json={
                    "task": task,
                    "selected_tender": tender_dump,
                    "purchase_orders": final_state.get("purchase_orders", []),
                    "executive_summary": final_state.get("metadata", {}).get("final_report", ""),
                },
            )
            session.add(db_task)
            session.commit()
            click.echo(f"[{_ts()}] 💾 Результаты сохранены в БД (Task ID: {db_task.id})")
    except Exception as exc:
        click.echo(f"[{_ts()}] ⚠️ Не удалось сохранить в БД: {exc}", err=True)

    click.echo("=" * 70)
    click.echo("📄 ИТОГОВЫЙ ИСПОЛНИТЕЛЬНЫЙ ОТЧЁТ (EXECUTIVE SUMMARY):")
    click.echo("=" * 70)

    if output == "markdown":
        click.echo(final_state.get("metadata", {}).get("final_report", "Отчёт пуст."))
    elif output == "json":
        payload = {
            "task": task,
            "selected_tender": final_state.get("selected_tender").model_dump() if final_state.get("selected_tender") else None,
            "work_list": [w.model_dump() for w in final_state.get("work_list", [])],
            "materials_list": [m.model_dump() for m in final_state.get("materials_list", [])],
            "purchase_orders": final_state.get("purchase_orders", []),
            "stock_check": final_state.get("stock_check", {}),
        }
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        click.echo(final_state.get("metadata", {}).get("final_report", "Отчёт пуст."))

    click.echo("=" * 70)


@cli.command("status")
@click.option("--task-id", "-i", required=True, help="UUID of the task.")
def status_command(task_id: str):
    """Check task status from the database."""
    try:
        uid = uuid.UUID(task_id)
    except ValueError:
        click.echo(f"Неверный UUID формат: {task_id}", err=True)
        sys.exit(1)

    engine = _get_app_engine()
    with get_session(engine) as session:
        t = session.scalar(select(Task).where(Task.id == uid))
        if not t:
            click.echo(f"Задача с ID {task_id} не найдена в БД.", err=True)
            sys.exit(1)

        click.echo(f"Task ID:     {t.id}")
        click.echo(f"Status:      {t.status.upper()}")
        click.echo(f"Created at:  {t.created_at}")
        click.echo(f"Updated at:  {t.updated_at}")
        click.echo(f"Input task:  {t.input_text}")
        if t.output_json:
            click.echo("\nOutput summary:")
            click.echo(t.output_json.get("executive_summary", json.dumps(t.output_json, ensure_ascii=False, indent=2)))


@cli.command("history")
@click.option("--limit", "-n", default=10, help="Number of recent tasks to list.")
def history_command(limit: int):
    """Display history of recent procurement tasks."""
    engine = _get_app_engine()
    Base.metadata.create_all(bind=engine)
    with get_session(engine) as session:
        tasks = session.scalars(select(Task).order_by(Task.created_at.desc()).limit(limit)).all()
        if not tasks:
            click.echo("История задач пуста.")
            return

        click.echo(f"{'ID':<38} | {'Статус':<10} | {'Дата':<20} | {'Задача'}")
        click.echo("-" * 90)
        for t in tasks:
            d_str = t.created_at.strftime("%Y-%m-%d %H:%M")
            click.echo(f"{str(t.id):<38} | {t.status.upper():<10} | {d_str:<20} | {t.input_text[:40]}")


@cli.group("config")
def config_group():
    """Configuration commands."""
    pass


@config_group.command("check")
def config_check():
    """Check configuration and service availability."""
    settings = get_settings()
    client = GoszakupClient()
    redis_ok = check_redis_connection()

    api_key = settings.anthropic_api_key.get_secret_value() if hasattr(settings.anthropic_api_key, "get_secret_value") else str(settings.anthropic_api_key)
    is_live_llm = bool(api_key and "mock" not in api_key and "test" not in api_key)

    click.echo("=" * 60)
    click.echo("🔧 NOVA — ДИАГНОСТИКА КОНФИГУРАЦИИ")
    click.echo("=" * 60)
    click.echo(f"Среда (APP_ENV):             {settings.app_env}")
    click.echo(f"База данных (DATABASE_URL):  {settings.database_url}")
    click.echo(f"Redis (REDIS_URL):           {'✅ Подключен' if redis_ok else '⚠️ Недоступен (Mock Fallback)'}")
    click.echo(f"Goszakup API Token:          {'✅ Реальный токен' if not client.is_mock_mode else '🔄 Mock / Fallback Mode (Синтетические данные РК)'}")
    click.echo(f"Anthropic LLM Key:           {'✅ Live Claude API' if is_live_llm else '🔄 Mock / Deterministic Fallback Mode'}")
    click.echo("=" * 60)


if __name__ == "__main__":
    cli()
