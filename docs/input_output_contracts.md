Final graphic interfaces are additionally defined by `data/schema/fig1_final_contract.json`, `sentinel2_processing_contract.json` and `figures_2_5_contract.json`. See [exact figure inputs and commands](final_submission_alignment_20261108.md). These contracts contain identities/schema, not distributed observations or geodata.

# External input and output contracts

`DONANA_INPUT_ROOT` and `DONANA_OUTPUT_ROOT` are set by the public entries, not discovered from a home directory. The input root is read-only and must be separately authorized.

| Input | Role |
|---|---|
| `raw_aerial.zip` | Native aerial records and event/locality metadata |
| `raw_ground/CT_YYYYMM/` | Native monthly CSV02 opportunities, CSV03 counts and original notices |
| `contracts/` | Taxon set, reporting contract, parent display keys, original water dictionary and native identities |
| `protocols/bridge/`, `protocols/temporal/` | Locked specifications and archived prerequisite gates; copied into a fresh run, never invented |
| `oracles/` | Authorized frozen scientific/plot comparisons; not replacements for raw analytical input |

The private P1 input-manifest receipt gives the exact file set, byte sizes and hashes. This repository intentionally does not ship that pack; an external user needs lawful access and authorized contract preparation. See `data/schema/input_fields.md` for field semantics.

| Output | Scientific role |
|---|---|
| `aerial/A1_WIDE_COUNTS.csv`, `aerial/m9/native_data/` | Qualified count interface and seasonal/correspondence tables |
| `bridge/sources/` | Native eligibility and fixed panels |
| `bridge/results/ground/` | Frequency/positive-count components; signed contribution and hierarchy distributions |
| `bridge/results/cross_source/` | Actual-date matching, support and correspondence |
| `bridge/results/environment/` | Category projections, support and sensitivities |
| `temporal/02_TEMPORAL_TREND_DIAGNOSTICS/` | Annual treatment, within-year and reference-support comparisons |
| `tables/` | Table 1 and Table 2A/B display CSVs |
| `f23/`, `fig4/`, `fig5/`, `r2/` | Inherited R graphic outputs and QA (inspect actual run manifest) |
| `execution/RUN_RECORD.json` | Commands, input/source hashes, return codes and execution scope |

Survey-supported zero differs from no survey. Positive-record frequency is not occupancy; conditional positive-record count is not observed flock size. Shared events, sector-specific support and fixed-support temporal comparisons remain separate. Native parent–child identifiers are retained; cross-source matching does not establish equivalent spatial footprints.
