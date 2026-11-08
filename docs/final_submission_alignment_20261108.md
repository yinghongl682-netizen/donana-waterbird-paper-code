# Final manuscript figure production

Version 1.0.0 production instructions. Original software is MIT; external resources retain their own rights. See README and VALIDATION.md.

## Fig. 1

The final entry is `scripts/figures/fig1/render_fig1_final.py`. The former master-candidate entry redirects to it. Only S1 (the final same-date Sentinel/WMS design) is accepted. The archived WFS candidate and event-locator variants remain retrievable at the base commit, not current production alternatives.

Inputs are externally supplied. `data/schema/fig1_final_contract.json` binds the exact WMS response, union, minimal map and calendar, and the exact Sentinel PNG. Sentinel QA must match all qualified semantic fields; only `created_utc` may vary after actual regeneration. Its actual SHA-256 is logged. A successful `--validate-inputs-only` performs no output creation.

`prepare_wms_reference.py` consumes the exact approved WMS GetFeatureInfo response acquired on 8 November: 58 unique valid MultiPolygons, EPSG:25829. It records the original 34 text encoding repairs and dissolves exact native LOC_4 assignments (30 PNC, two SB), with no geometry repair, snapping or simplification. The final union retains its production bytes and hash. `fetch_reference_wms.py` exposes the original full-resolution public request explicitly; rendering never downloads. A changed future HTTP response is retained as unqualified, not silently substituted. The current-service acquisition was not rerun in this alignment.

`prepare_final_map_layers.py` projects an authorized archived map bundle to unchanged geometry and only consumed fields. Output keeps the mainland mask, coast, selected Guadalquivir river, Natural Earth inset, extent/north/locator metadata. It removes old sector geometry, all event-derived locators and unused native properties. The final render does not require the old union or PNOA image. The retained Spain/Doñana geographic locator is distinct from the removed event-derived child locators.

`process_sentinel2_rgb.py` ports the original selected Sentinel branch. It requires `S2_SELECTED_ITEMS.json` and 16 native windows, in the fixed four-item order in `data/schema/sentinel2_processing_contract.json`. All inputs are byte-locked. B4/B3/B2, SCL 2/4/5/6/7, DN > 0, scale 0.0001, zero additional offset, nearest-neighbour registration, first-valid-pixel order, 0–0.30 display interval and gamma 1.6 are retained. The imagery is contextual, not a new water estimate or evidence of ecological mechanism. Acquisition itself is not reproduced by this window-processing entry.

The map retains 396 calendar states (PNC 75, SB 113, ground 110 included months), 174 × 200 mm dimensions, original extent, solid/dashed parent outlines and the qualification that reference geography is not verified individual-flight footprints. Blank calendar cells are not zero birds.

## Fig. 2–5

`data/schema/figures_2_5_contract.json` lists all 16 required interfaces and exact CSV columns; the driver records actual input hashes and row counts before execution. This preflight is structural, not a substitute for the original scientific locks.

| Figure | Source role and retained guard |
|---|---|
| 2 | Nine species' calendar medians and tied peaks; August gap and December offset leader preserved. Qualified plot RDS, SVG and three source CSVs required. |
| 3 | Native-support departure correlations; original plot object and exact display table, 36 lower-triangle pairs per sector. |
| 4 | Global f/q components, signed-position accounting, weighted seasonal contributions; original render source, three display CSVs, annual summary and frozen legend SVG. These are separate decompositions, not causes. |
| 5 | Parent locality contributions, shares and distinct endpoint/period/annual-HHI objects; four CSVs and adjacent original renderer. |

Fig. 2's adapter still enforces its frozen-RDS hash. With `--fig2-reference-run`, four scientific/display files must be byte-identical and the existing R semantic bridge compares plot data, mappings, built layers and axes before using that RDS. A new RDS with a different serialization is not silently blessed. Fig. 3–5 use the supplied completed run directly. Outputs must be new and outside the repository, primary input run and optional Fig. 2 reference run.

The final Word Fig. 4 carrier uses `outline_existing_pdf_svg.py INPUT_PDF NEW_EXTERNAL_SVG`. It converts the existing final PDF to outlined glyphs through PyMuPDF, records version/page-size/hashes, rejects existing outputs and retains the original editable R SVG. It does not patch a manuscript or alter data. This Python conversion is a preserved final carrier step, not a replacement R plot implementation.

## Windows execution

Use existing qualified runtimes; no installation is implicit. All paths below are placeholders for separately authorized inputs. Use `-B` for the adjacent-module figure entries; set task-local cache/temp directories. Outputs must not already exist.

```powershell
& $GeoPython -B scripts/figures/fig1/prepare_wms_reference.py --raw-geojson $RawWms --output-root $NewUnionDir
& $GeoPython -B scripts/figures/fig1/process_sentinel2_rgb.py --input-root $NativeWindowRoot --output-root $NewRgbDir
& $FigurePython -B scripts/figures/fig1/prepare_final_map_layers.py --map-layers $ArchivedMapJson --output $NewMinimalMapJson
& $FigurePython -B scripts/figures/fig1/render_fig1_final.py --input-root $FinalMapInputRoot --reference-union $NewUnionFile --output-root $NewMapOutput --validate-inputs-only
& $FigurePython -B scripts/figures/fig1/render_fig1_final.py --input-root $FinalMapInputRoot --reference-union $NewUnionFile --output-root $NewMapOutput
& $FigurePython -B workflows/main_results/render_submission_figures.py --input-run $CompletedRun --fig2-reference-run $QualifiedFig2Run --output $NewFigureOutput --rscript $RscriptExe --r-library $RLibrary
& $FigurePython -B scripts/figures/outline_existing_pdf_svg.py $RenderedFig4Pdf $NewWordSvg
```

For map staging, place the new PNG and its new QA JSON at the input-root top level, the minimized JSON at `F1/support/plot_data/MAP_LAYERS_FINAL.json`, and the unchanged calendar beside it. Do not substitute a legacy QA file for a new processing receipt. Neither staging nor a hash contract grants redistribution rights.

## Rights and untested scope

Final map provenance uses the specifically qualified WMS copy and no event-derived locators, following the final manuscript's resolved source route. This does not retroactively establish the old WFS licence or grant software licensing. Exact provenance of other cartographic components and historical metadata qualifications remain as recorded with the final manuscript. No private map/input pixels, observations, fonts or private audit reports are included here.

See VALIDATION.md for the executed baseline checks. Native portal reacquisition, new-machine dependency restoration, full OR1/OR2 assembly, legal/software-author acceptance and publication are outside the demonstrated scope.
