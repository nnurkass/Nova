"""Unit tests for the Nova CLI interface."""
from click.testing import CliRunner

from nova.cli import cli


class TestCLI:
    def test_cli_config_check(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "check"])
        assert result.exit_code == 0
        assert "NOVA — ДИАГНОСТИКА КОНФИГУРАЦИИ" in result.output
        assert "Среда (APP_ENV)" in result.output

    def test_cli_run_markdown(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--task", "Поиск тендеров на капремонт школ в г. Алматы", "--output", "markdown"])
        assert result.exit_code == 0
        assert "NOVA — Мульти-агентная система строительных закупок" in result.output
        assert "ИСПОЛНИТЕЛЬНЫЙ ОТЧЁТ" in result.output
        assert "Результаты сохранены в БД" in result.output

    def test_cli_run_json(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--task", "Благоустройство парка в Шымкенте", "--output", "json"])
        assert result.exit_code == 0
        assert "selected_tender" in result.output
        assert "purchase_orders" in result.output

    def test_cli_history(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["history", "--limit", "5"])
        assert result.exit_code == 0
        assert "ID" in result.output or "История задач пуста" in result.output
