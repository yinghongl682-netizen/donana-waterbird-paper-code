# Input schema and native meaning

Raw ground CSV02 is the survey-opportunity table, and CSV03 contains positive taxon counts. Join using the census and four native locality hierarchy levels; qualify surveyed/context/date/count states before creating a conditional zero. A missing positive row alone is insufficient. Original Spanish field names and accented literals are required by the preserved parser.

Core fields: `Censo`, `Localidad nivel 1` through `Localidad nivel 4`, `Fecha`, `Se censa`, `Nivel de agua`, `Especie`, `Individuos`. Reporting contracts define the eligible focal taxa. Counts are finite nonnegative integers. Water code 6 is unknown, not a numeric depth; unknown water does not disqualify an otherwise bird-eligible G2 visit.

A normalized ground slot has `year`, `position`, `child_id`, `parent_id`, `month`, `visit_n`, visit IDs, actual dates and thirteen species responses. A position is child locality × calendar month; a slot is a year-specific mean over qualified visits. The main complete frame repeats the same 702 positions over eleven years; the reduced frame repeats 699. Unsupported positions and unvisited opportunities are excluded states, not biological absence.

The aerial wide interface uses `unit`, `parent_id`, `actual_date`, `year`, `month` and nine exact focal taxon columns. PNC and SB remain separate. A1 has 75/113 native sector-events; departure support is 75/112 and shared departure support is 75. Reportable month references need at least three sampled years.
