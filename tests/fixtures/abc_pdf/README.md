## ABC PDF Fixtures

`sample_statement.pdf` — санитизированный synthetic PDF fixture для шага 2.4.
Он собран по структуре реального пользовательского PDF, но не содержит
оригинальных названий проекта, подрядчиков или исходных сметных данных.

Опорная структура fixture:

- страница 1 — `Q9` / `LOKALNAYA SMETA`
- страница 2 — `QM` / `Vedomost materialnyh resursov`
- страница 3 — `ID` / `ISHODNYE DANNYE`

Источник структуры:

- локальные страницы полного PDF пользователя с `Q9`, `QM` и `ID`
- содержимое намеренно упрощено до минимального набора строк, который нужен
  для воспроизводимого CI и smoke-тестов адаптера

`expected_statement.json` — snapshot нормализованного JSON contract, который
ожидается после `read_abc_document(sample_statement.pdf)`.

`no_sections.pdf` — негативный fixture без маркеров `Q9/QM/ID`.
