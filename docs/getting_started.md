# Running the code

Use separately installed qualified Python/R environments. Observed versions are in `environment/`; no package installation is performed automatically. Windows is the tested platform. Do not install into shared scientific environments merely to bypass a failed dependency check.

```powershell
& $PythonExe -B scripts/run_all/demo.py --output $NewDemoOutput
& $PythonExe -B tests/reproducibility/check_demo.py $NewDemoOutput
& $PythonExe -B scripts/run_all/run.py --input-root $AuthorizedInputPack --output $NewScientificRun --rscript $RscriptExe --r-library $RLibrary
& $PythonExe -B tests/scientific_regression/compare_numeric.py --output-root $NewScientificRun --expectations $AuthorizedFrozenExpectations --report $NewNumericReport
```

All variables are caller-supplied external paths. The real pack includes raw records, source/eligibility contracts, locked protocols and authorized oracles; none is distributed. An arbitrary current portal export cannot silently replace it. Positive-record frequency is not occupancy, and missing survey support is not zero birds.

For final Fig. 1–5, follow [the exact figure workflow](final_submission_alignment_20261108.md). Use `-B` for adjacent-module figure entries. Outputs must be new and outside source/input directories. Keep caches/temp outputs in the caller's run workspace. Full OR1/OR2 packaging is outside these entry points.
