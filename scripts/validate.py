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
    b = doc["inclusion_test"].get("boundary")
    if b:
        # The case against a boundary exhibit has to be stated as its best advocate would
        # state it. A stub here would let a weak inclusion pass by looking documented.
        if len(b["against_inclusion"].split()) < 25:
            fail += 1
            print(f"FAIL {p.name}: boundary.against_inclusion is too short to be the strongest argument")
            continue
        if len(b["why_included"].split()) < 25:
            fail += 1
            print(f"FAIL {p.name}: boundary.why_included does not answer it"); continue
    # decisions[] and resolution describe the same last court. If they drift apart one of
    # them is wrong, and the summary field is the likelier culprit because it is the one
    # nobody re-reads.
    ds = doc["decisions"]
    reading_ids = {r["id"] for r in doc["readings"]} | {"none"}
    bad_adopt = [x["adopted"] for x in ds if x["adopted"] not in reading_ids]
    if bad_adopt:
        fail += 1
        print(f"FAIL {p.name}: decision adopts {bad_adopt[0]!r}, which is not a reading id")
        continue
    for x in ds:
        if x["known_from"] == "unverified":
            fail += 1; print(f"FAIL {p.name}: decision '{x['court'][:40]}' is unverified"); break
        if x["known_from"] == "inferred" and x["declared_ambiguous"] is not None:
            fail += 1
            print(f"FAIL {p.name}: '{x['court'][:40]}' is inferred, so it cannot assert "
                  f"declared_ambiguous={x['declared_ambiguous']}")
            break
        if x["known_from"] == "inferred" and x.get("quote"):
            fail += 1; print(f"FAIL {p.name}: an inferred row cannot carry a quote"); break
    else:
        pass
    if fail and ds and any(x["known_from"] in ("unverified",) or
                           (x["known_from"]=="inferred" and (x["declared_ambiguous"] is not None or x.get("quote")))
                           for x in ds):
        continue

    dated = [x["date"] for x in ds if x.get("date")]
    if dated != sorted(dated):
        fail += 1; print(f"FAIL {p.name}: decisions are not in chronological order"); continue
    last, res = ds[-1], doc["resolution"]
    out = str(res["outcome"]).strip()
    if len(out) == 1 and last["adopted"] != out:
        fail += 1
        print(f"FAIL {p.name}: last decision adopted {last['adopted']}, resolution.outcome says {out}")
        continue
    if last["declared_ambiguous"] != res["court_declared_ambiguous"]:
        fail += 1
        print(f"FAIL {p.name}: last decision and resolution disagree on court_declared_ambiguous")
        continue

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
