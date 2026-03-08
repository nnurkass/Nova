## ABC PDF Adapter

Источник правды для шага 2.4 — PDF-файлы, выпущенные АВС-4. До появления
реальных XML-образцов проект использует нормализованный JSON statement как
внутренний контракт между парсером, тестами и ПТО-агентом.

### Опорные секции

- `Q9` — локальная смета с позициями работ, единицами измерения, количеством и
  стоимостными полями.
- `QМ` — ведомость материальных ресурсов и оборудования.
- `ИД` — исходные данные АВС; используются для трассировки и контекста, но не
  как основной источник бизнес-данных.

### Канонический контракт

`read_abc_document(file_path)` возвращает `ResourceStatement` со следующими
слоями данных:

- `meta` — документные метаданные (`source_format`, `source_file`,
  `project_name`, `construction_cipher`, `estimate_code`, `document_kind`,
  `page_ranges`)
- `positions` — нормализованные позиции из `Q9` и `QМ`
- `works` — агрегированные работы
- `materials` — агрегированные материалы
- `totals` — суммарные стоимости работ и материалов

`write_abc_statement(statement, output_path)` пишет UTF-8 JSON с теми же
логическими разделами.

### Fixture strategy

- В репозиторий попадает санитизированный PDF fixture, собранный по структуре
  реального документа пользователя.
- Для CI fixture должен быть маленьким и воспроизводимым.
- Локальный полный PDF из `Downloads` используется только для ручного
  smoke-check.

### Compatibility layer

До появления реального XML-адаптера сохраняются временные alias:

- `read_abc_xml -> read_abc_document`
- `write_abc_xml -> write_abc_statement`
- `abc_xml_reader -> abc_document_reader`
- `abc_xml_writer -> abc_statement_writer`
