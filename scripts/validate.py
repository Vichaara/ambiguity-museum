"""Validate exhibits against exhibit.schema.json.

Normalises YAML date scalars to ISO strings before validating. YAML parses an
unquoted 2006-10-31 into a datetime.date, which is not a JSON string and fails
"format": "date" — so a contributor writing the natural thing would otherwise get
a confusing type error. Normalising here means both spellings are accepted.
"""
import sys, json, datetime, pathlib
import yaml
from jsonschema import Draft202012Validator

def norm(o):
    if isinstance(o, dict):  return {k: norm(v) for k, v in o.items()}
    if isinstance(o, list):  return [norm(v) for v in o]
    if isinstance(o, (datetime.date, datetime.datetime)): return o.isoformat()
    return o

root   = pathlib.Path(__file__).resolve().parent
schema = json.loads((root.parent / "schema" / "exhibit.schema.json").read_text())
v      = Draft202012Validator(schema)

paths = [pathlib.Path(p) for p in sys.argv[1:]] or sorted((root.parent / "exhibits").glob("*.yml"))
ids, fail = {}, 0
for p in paths:
    doc  = norm(yaml.safe_load(p.read_text()))
    errs = sorted(v.iter_errors(doc), key=lambda e: list(e.path))
    if errs:
        fail += 1
        print(f"FAIL {p.name}")
        for e in errs:
            print(f"     {'.'.join(map(str, e.path)) or '(root)'}: {e.message}")
        continue
    # cross-file invariants the schema cannot express on its own
    if doc["id"] in ids:
        fail += 1; print(f"FAIL {p.name}: duplicate id '{doc['id']}' (also {ids[doc['id']]})")
        continue
    ids[doc["id"]] = p.name
    if doc["id"] != p.stem:
        fail += 1; print(f"FAIL {p.name}: id '{doc['id']}' does not match filename"); continue
    if not any(r.get("adopted") for r in doc["readings"]) and not any(k in doc["resolution"]["outcome"] for k in ("unresolved", "no-contract", "Split by instrument")):
        print(f"WARN {p.name}: no reading marked adopted, and outcome is not 'unresolved'")
    if doc["inclusion_test"].get("boundary") and not doc["inclusion_test"].get("notes"):
        fail += 1; print(f"FAIL {p.name}: boundary exhibits must explain themselves in inclusion_test.notes"); continue
    # Codex review, #2: recording only the edit that produces the litigated outcome makes
    # that outcome the drafting baseline. Every reading must be shown to be draftable.
    r_ids = {r["id"] for r in doc["readings"]}
    e_ids = [e["forces"] for e in doc["preventive_edits"]]
    if set(e_ids) != r_ids:
        fail += 1
        print(f"FAIL {p.name}: preventive_edits cover {sorted(set(e_ids))}, readings are {sorted(r_ids)}")
        continue
    if len(e_ids) != len(set(e_ids)):
        fail += 1; print(f"FAIL {p.name}: two preventive_edits force the same reading"); continue
    if not any(e["plausible_intent"] for e in doc["preventive_edits"]):
        fail += 1
        print(f"FAIL {p.name}: no reading is marked plausible_intent, so nobody wanted either outcome")
        continue

    hard = {"citation", "disputed_text", "resolution"}
    covered = {c for s in doc["sources"] if s["kind"] in ("primary", "near-primary") for c in s["confirms"]}
    if doc["verification"]["status"] == "confirmed" and not hard <= covered:
        fail += 1
        print(f"FAIL {p.name}: status 'confirmed' but {sorted(hard - covered)} lack a primary/near-primary source")
        continue
    print(f"ok   {p.name}  [{doc['mechanism']['primary']}]")

# every pairs_with must point at a real exhibit
for p in paths:
    doc = norm(yaml.safe_load(p.read_text()))
    for other in doc.get("pairs_with", []):
        if other not in ids:
            fail += 1; print(f"FAIL {p.name}: pairs_with '{other}' does not exist")

print(f"\n{len(paths) - fail}/{len(paths)} valid")
sys.exit(1 if fail else 0)
