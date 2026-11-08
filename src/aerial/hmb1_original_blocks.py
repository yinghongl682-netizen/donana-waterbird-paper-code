from __future__ import annotations

import csv

import hashlib

import io

import json

import os

import platform

import re

import sys

import zipfile

from collections import Counter, defaultdict

from datetime import date, datetime, timezone

from pathlib import Path

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def read_zip_csv(z: zipfile.ZipFile, member: str) -> list[dict[str, str]]:
    with z.open(member) as raw:
        with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as txt:
            return list(csv.DictReader(txt))

def month_spine(start: str, end: str) -> list[str]:
    y, m = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return out

def is_ancestor(a: tuple[str, str], b: tuple[str, str]) -> bool:
    a2, a3 = a
    b2, b3 = b
    return (not a2 and bool(b2 or b3)) or (a2 == b2 and bool(a2) and not a3 and bool(b3))

def fingerprint(paths: list[Path], output: Path) -> None:
    rows = []
    for p in sorted(set(paths), key=lambda x: str(x).lower()):
        st = p.stat()
        rows.append({
            "path": str(p),
            "size_bytes": st.st_size,
            "mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
            "sha256": sha256(p),
        })
    write_csv(output, rows)

def reconstruct(ZIP,OUT,taxa):
    with zipfile.ZipFile(ZIP) as z:
        events = read_zip_csv(z, "aerial/01-aerial_counts.csv")
        roster = read_zip_csv(z, "aerial/02-aerial_counts_localities.csv")
        counts = read_zip_csv(z, "aerial/03-aerial_counts_data.csv")

    event_date = {r["Censo"]: r["Fecha"] for r in events}
    event_notes = {r["Censo"]: r["Observaciones"] for r in events}
    event_months = defaultdict(list)
    for e, d in event_date.items():
        if "2013-01-01" <= d <= "2026-06-30":
            event_months[d[:7]].append(e)

    set_r = [r["current_archive_taxon"] for r in taxa if r["role"] == "STRICT_RESPONSE_TAXON"]
    anatidae = {
        "Anser anser", "Tadorna tadorna", "Mareca penelope", "Mareca strepera", "Anas crecca",
        "Anas platyrhynchos", "Anas acuta", "Spatula clypeata", "Netta rufina", "Aythya ferina",
    }
    candidate_taxa = [t for t in set_r if t not in anatidae]
    sectors = [
        ("PNC", "Parque Nacional De Doñana"),
        ("PNT", "Parque Natural Norte"),
        ("SB", "Salinas De Bonanza"),
        ("VLP", "Veta La Palma"),
    ]

    roster_by = defaultdict(list)
    for r in roster:
        d = event_date.get(r["Censo"], "")
        if "2013-01-01" <= d <= "2026-06-30":
            roster_by[(r["Censo"], r["Localidad nivel 1"])].append(r)

    counts_by = defaultdict(list)
    count_row_id = {}
    for row_number, r in enumerate(counts, start=2):
        count_row_id[id(r)] = row_number
        if r["Especie"] in set_r:
            counts_by[(r["Censo"], r["Localidad nivel 1"], r["Especie"])].append(r)

    # All-archive collision assessment, independently recomputed.
    full_conflict_keys = set()
    for k, rows in counts_by.items():
        supports = [(r["Localidad nivel 2"], r["Localidad nivel 3"]) for r in rows]
        if any(is_ancestor(a, b) or is_ancestor(b, a) for i, a in enumerate(supports) for b in supports[i + 1:]):
            full_conflict_keys.add(k)

    unlocated_event_taxon = {(r["Censo"], r["Especie"]) for r in counts
                             if r["Especie"] in set_r and not r["Localidad nivel 1"]}
    spine = month_spine("2013-01", "2026-06")
    candidate_rows = []
    blocker_rows = []
    support_summary = Counter()
    for month in spine:
        evs = sorted(event_months.get(month, []))
        for sector_code, sector in sectors:
            for taxon in candidate_taxa:
                base = {
                    "calendar_year_month": month,
                    "sector_code": sector_code,
                    "sector": sector,
                    "taxon": taxon,
                    "candidate_period_rule": "2013_DATABASE_STRUCTURE_ONWARD_THROUGH_FROZEN_SNAPSHOT",
                    "taxon_rule": "SET_R_NON_ANATIDAE_ONLY",
                    "response_estimand": "observer_estimated_recorded_count_on_documented_complete_operational_sector_support",
                }
                if len(evs) == 0:
                    state, response, event_id, actual_date, source_rows = "NO_PROVIDER_EVENT", "", "", "", ""
                    reason = "No official event in frozen archive for this calendar month"
                elif len(evs) > 1:
                    state, response, event_id, actual_date, source_rows = "REPEATED_MONTH_PRIMARY_EVENT_UNRESOLVED", "", ";".join(evs), "", ""
                    reason = "More than one official event; no primary-event rule applied"
                else:
                    event_id = evs[0]
                    actual_date = event_date[event_id]
                    rr = roster_by.get((event_id, sector), [])
                    cr = counts_by.get((event_id, sector, taxon), [])
                    source_rows = ";".join(str(count_row_id[id(r)]) for r in cr)
                    if not rr:
                        state, response = "SUPPORT_ROSTER_ABSENT", ""
                        reason = "No locality-support rows for sector-event"
                    elif any(r["Se censa"] != "True" for r in rr):
                        state, response = "PARTIAL_OR_NOT_SURVEYED_SECTOR", ""
                        reason = f"{sum(r['Se censa']=='True' for r in rr)}/{len(rr)} listed locality rows surveyed"
                    elif (event_id, taxon) in unlocated_event_taxon:
                        state, response = "UNLOCATED_POSITIVE_AFFECTS_EVENT_TAXON", ""
                        reason = "At least one same-taxon positive lacks Level-1 assignment"
                    elif (event_id, sector, taxon) in full_conflict_keys:
                        state, response = "PARENT_CHILD_RECORD_SEMANTICS_UNRESOLVED", ""
                        reason = "Ancestor and descendant records coexist for same event-sector-taxon"
                    else:
                        response = str(sum(int(r["Individuos"]) for r in cr))
                        state = "ELIGIBLE_RECORDED_POSITIVE" if cr else "ELIGIBLE_CONDITIONAL_ZERO"
                        reason = "All listed locality rows surveyed; Set-R non-anatid scope; no hierarchy conflict or unlocated same-taxon positive"
                support_summary[(sector_code, state)] += 1
                row = dict(base)
                row.update({
                    "archive_event_id": event_id,
                    "actual_census_date": actual_date,
                    "provider_nominal_date": actual_date,
                    "monitoring_round_label": event_id,
                    "support_state": state,
                    "recorded_count": response,
                    "source_count_csv_row_numbers": source_rows,
                    "inclusion_or_exclusion_reason": reason,
                    "fixed_hydrological_domain_status": "NOT_MATCHED; Level-1 geometry effective interval unresolved; D7A is AERIAL57_UNION",
                })
                candidate_rows.append(row)
                if not state.startswith("ELIGIBLE_"):
                    blocker_rows.append({k: row[k] for k in (
                        "calendar_year_month", "sector_code", "sector", "taxon", "archive_event_id",
                        "actual_census_date", "support_state", "inclusion_or_exclusion_reason",
                        "fixed_hydrological_domain_status")})

    write_csv(OUT / "03A_RESTRICTED_MONTHLY_BIRD_ONLY_CANDIDATE.csv", candidate_rows)
    write_csv(OUT / "03B_RESTRICTED_MONTHLY_BLOCKERS.csv", blocker_rows)
    summary_rows = [{"sector_code": k[0], "support_state": k[1], "cell_count": v} for k, v in sorted(support_summary.items())]
    write_csv(OUT / "03C_RESTRICTED_MONTHLY_SUPPORT_SUMMARY.csv", summary_rows)
    return candidate_rows
