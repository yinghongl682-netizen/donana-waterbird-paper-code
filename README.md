# Doñana waterbird monitoring analysis — paper code

Version **1.0.0** accompanies *Seasonal peaks, temporal correspondence, and local changes in Doñana waterbird records*. Original research code is released under the [MIT licence](LICENSE); external resources are excluded from that grant ([notices](THIRD_PARTY_NOTICES.md)). Software author: Yinghong Lin. See [contributions](AUTHORS.md) and [CITATION.cff](CITATION.cff).

Repository: https://github.com/yinghongl682-netizen/donana-waterbird-paper-code

## Included workflows

- Original Python analysis for aerial seasonal references/correspondence, actual-date comparisons, ground frequency/conditional-count components, local contributions, hierarchy/HHI, environmental comparisons and sensitivity diagnostics.
- Final Fig. 1 WMS acquisition/preparation, Sentinel RGB processing from qualified native windows, minimal-map input contract, rendering and calendar checks.
- Actual R production scripts for final Fig. 2–5, explicit figure-input contracts and final Fig. 4 Word SVG carrier conversion.
- Invented example, numeric-regression comparator, interface tests and observed environment records.

## Run

See [getting started](docs/getting_started.md), [analysis input contracts](docs/input_output_contracts.md), [final figure workflow](docs/final_submission_alignment_20261108.md) and [methods mapping](docs/scientific_methods_mapping.md). Scripts require explicit external inputs and new external output directories. There is no implicit download of monitoring observations.

The observed analysis environment was Python 3.12.14, pandas 3.0.1, NumPy 2.3.5 and R 4.6.1. Fig. 1 rendering used Python 3.14.0/Matplotlib 3.11.2; geospatial preparation used Python 3.11.9/Shapely 2.2.0/rasterio 1.4.4. Exact observed versions are under `environment/`. No packages or fonts are bundled, and this is not a newly provisioned environment lock.

## Reproducibility and data limits

The validated technical baseline completed all 14 original stages, passed 335 frozen numeric checks, and reproduced final Fig. 1–5 images on the original Windows machine. See [validation scope](VALIDATION.md). These are bounded regression results, not independent ecological validation.

**Fig. 2 retains an explicit historical RDS dependency.** Its original exact-artifact guard, four file-identity checks and plot-semantic comparison are preserved. **Whole-paper complete reproduction in a fresh environment has not been established.** Native-source reacquisition, restoration of every dependency and complete OR1/OR2 assembly are not claimed.

Restricted raw observations, unapproved derived data, geodata/image pixels, fonts, private audit logs and private Git history are excluded. Only a clearly invented synthetic CSV is supplied. External data access and redistribution permissions must be obtained separately; see [data access](docs/data_access.md).
