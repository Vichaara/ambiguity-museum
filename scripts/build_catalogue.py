"""Generate CATALOGUE.md from exhibits/*.yml.

GitHub renders README.md and CATALOGUE.md with its own stylesheet and strips CSS and
JavaScript, so the only design lever available is structure: headings, tables,
blockquotes, <details>, and GitHub's alert callouts. Everything below is chosen to
survive that renderer.

Two GitHub-flavoured-markdown traps this avoids:

  1. Markdown inside <details> is only parsed if a BLANK LINE follows </summary> and
     precedes </details>. Without it the block renders as literal text.
  2. A pipe inside a table cell ends the cell. Any text interpolated into a table row
     has to escape it, along with the newlines YAML block scalars leave behind.

Run after editing any exhibit:  python3 scripts/build_catalogue.py
"""
import pathlib, re, yaml
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
EX   = ROOT / "exhibits"

def flat(s):
    """Collapse a YAML block scalar to one line."""
    return " ".join(str(s or "").split())

def cell(s):
    """Safe inside a markdown table cell."""
    return flat(s).replace("|", "\\|")

def human(s):
    return flat(s).replace("-", " ").replace("_", " ")

def anchor(acc):
    """Explicit anchor id, emitted as <a id> just above the heading.

    NOT a reimplementation of GitHub's heading slugger. That was the first approach and
    it produced dead links: github-slugger replaces spaces one at a time rather than
    collapsing runs, so a heading like "1836.01  Which George Gord?" slugs to
    "183601--which-george-gord" with a DOUBLE hyphen where the removed punctuation left
    two adjacent spaces. Reproducing that faithfully means tracking their sanitiser
    forever. An explicit id is stable, survives retitling, and reads better in a URL.

    GitHub's sanitiser rewrites these to id="user-content-ex-2017-01" and its own scroll
    handler resolves "#ex-2017-01" against them, so the short form is what we link to."""
    return "ex-" + acc.replace(".", "-")

docs = [yaml.safe_load(p.read_text()) for p in sorted(EX.glob("*.yml"))]
docs.sort(key=lambda d: str(d["case"]["date"]))

# Accession numbers are year-based: they encode when the case was decided, which is
# real information. A 01/02/03 sequence would encode only the order I happened to
# write the files in.
seen_year = Counter()
for d in docs:
    y = str(d["case"]["date"])[:4]
    seen_year[y] += 1
    d["_acc"] = f"{y}.{seen_year[y]:02d}"
    d["_head"] = f"{d['_acc']}  {flat(d['title'])}"
    d["_anchor"] = anchor(d["_acc"])

n            = len(docs)
n_confirmed  = sum(1 for d in docs if d["verification"]["status"] == "confirmed")
n_clear      = sum(1 for d in docs if d["resolution"]["court_declared_ambiguous"] is False)
n_boundary   = sum(1 for d in docs if d["inclusion_test"].get("boundary"))
n_mech       = len({d["mechanism"]["primary"] for d in docs})
multi        = [d for d in docs if len(d["decisions"]) > 1]
n_flip       = sum(1 for d in multi if len({x["adopted"] for x in d["decisions"]}) > 1)
n_ambdis     = sum(1 for d in multi
                   if len({x["declared_ambiguous"] for x in d["decisions"]
                           if x["declared_ambiguous"] is not None}) > 1)
instruments  = Counter(d["instrument"]["type"] for d in docs)
jurisdictions= Counter(d["case"]["jurisdiction"] for d in docs)

L = []
w = L.append

w("# Catalogue")
w("")
w(f"{n} exhibits. Each is a case where a written legal instrument admitted more than")
w("one reading, and a court had to choose between them.")
w("")
w("> [!NOTE]")
w(f"> In **{n_clear} of {n} exhibits the court declared the text unambiguous** — in one")
w("> case after the parties had filed competing dictionary definitions and expert")
w("> affidavits, in another while conceding the reading it enforced would incinerate the")
w("> product the patent existed to make. Judicial confidence in clarity is not evidence")
w("> of clarity, and it is the most consistent finding in the collection.")
w("")

w("## Holdings at a glance")
w("")
w("| | |")
w("|---|---|")
w(f"| Exhibits | {n} |")
w(f"| Instrument types | {', '.join(f'{human(k)} ({v})' for k, v in instruments.most_common())} |")
w(f"| Jurisdictions | {', '.join(f'{k} ({v})' for k, v in jurisdictions.most_common())} |")
w(f"| Distinct mechanisms | {n_mech} across {n} exhibits |")
w(f"| Court called the text clear | {n_clear} |")
w(f"| Boundary specimens | {n_boundary} |")
w(f"| Reached more than one court | {len(multi)} |")
w(f"| ... where the reading changed between courts | {n_flip} |")
w(f"| ... where courts disagreed on whether the text was ambiguous | {n_ambdis} |")
n_inf = sum(1 for d in docs for x in d["decisions"] if x["known_from"] == "inferred")
n_dec = sum(len(d["decisions"]) for d in docs)
w(f"| Decisions recorded, of which inferred rather than read | {n_dec}, {n_inf} inferred |")
w(f"| Verified to a primary source | {n_confirmed} of {n} |")
w("")

w("## Index")
w("")
w("| No. | Exhibit | Instrument | Mechanism | Notes |")
w("|---|---|---|---|---|")
for d in docs:
    flags = []
    if d["resolution"]["court_declared_ambiguous"] is False: flags.append("called clear")
    if d["inclusion_test"].get("boundary"):                  flags.append("boundary")
    if d["verification"]["status"] != "confirmed":           flags.append("**needs primary**")
    w(f"| `{d['_acc']}` | [{cell(d['title'])}](#{d['_anchor']}) | {human(d['instrument']['type'])} "
      f"| {human(d['mechanism']['primary'])} | {', '.join(flags) or '—'} |")
w("")
w("---")
w("")

for d in docs:
    case, res, inc = d["case"], d["resolution"], d["inclusion_test"]
    w(f'<a id="{d["_anchor"]}"></a>')
    w("")
    w(f"## {d['_head']}")
    w("")
    cite = f"**{flat(case['name'])}**, {flat(case['citation'])} ({flat(case['court'])}, {str(case['date'])[:4]})"
    w(cite)
    w("")

    if d["verification"]["status"] != "confirmed":
        w("> [!WARNING]")
        w("> **Not yet verified against a primary source.** The holding below is a")
        w("> placeholder, not a quotation. See *Outstanding* at the end of this entry.")
        w("")

    w("**The text in dispute**")
    w("")
    for line in flat(d["disputed_text"]["quote"]).split("\n"):
        w(f"> {line}")
    w("")
    w(f"The ambiguity sits in {flat(d['disputed_text']['locus'])}.")
    w("")

    w("**The readings**")
    w("")
    for r in d["readings"]:
        who = f" — {flat(r['advanced_by'])}" if r.get("advanced_by") else ""
        won = " — **adopted**" if r.get("adopted") else ""
        w(f"- **Reading {r['id']}**{who}{won}  ")
        w(f"  {flat(r['statement'])}")
    w("")

    held = "**Held**" if res["court_declared_ambiguous"] else "**Held** — the court agreed the text was ambiguous"
    if res["court_declared_ambiguous"] is False:
        held = "**Held** — while calling the text unambiguous"
    w(held)
    w("")
    for line in flat(res["quote"]).split("\n"):
        w(f"> {line}")
    w("")
    if len(d["decisions"]) > 1:
        w("**How it travelled**")
        w("")
        w("| Court | Read it as | Called the text | |")
        w("|---|---|---|---|")
        for x in d["decisions"]:
            amb = {True: "ambiguous", False: "clear", None: "did not say"}[x["declared_ambiguous"]]
            rd = "neither reading" if x["adopted"] == "none" else f"Reading {x['adopted']}"
            cite = f" ({cell(x['citation'])})" if x.get("citation") else ""
            soft = " *(inferred, not read)*" if x["known_from"] == "inferred" else ""
            w(f"| {cell(x['court'])}{cite}{soft} | {rd} | {amb} | {human(x['disposition'])} |")
        w("")

    w("**The edits that would have prevented it**")
    w("")
    w("Both readings were draftable. What the text failed to do was choose between them.")
    w("")
    for e in d["preventive_edits"]:
        tag = "" if e["plausible_intent"] else " *(a possible parse, not a possible bargain)*"
        w(f"- **To force Reading {e['forces']}**{tag}  ")
        w(f"  {flat(e['edit'])}")
        if e.get("changes_bargain"):
            w(f"  <br>*Effect:* {flat(e['changes_bargain'])}")
    w("")

    w("<details>")
    w(f"<summary>Apparatus — provenance, stakes, and why this exhibit qualifies</summary>")
    w("")
    w("| | |")
    w("|---|---|")
    w(f"| Instrument | {human(d['instrument']['type'])} — {cell(d['instrument']['provision'])} |")
    if d["instrument"].get("drafted_by"):
        w(f"| Drafted by | {cell(d['instrument']['drafted_by'])} |")
    w(f"| Mechanism | {human(d['mechanism']['primary'])}"
      + (f" ({', '.join(human(m) for m in d['mechanism'].get('secondary', []))})" if d["mechanism"].get("secondary") else "")
      + " |")
    w(f"| Resolved on | {', '.join(human(b) for b in res['basis'])} |")
    if d.get("stakes", {}).get("note"):
        amt = f"{cell(d['stakes'].get('amount',''))} — " if d["stakes"].get("amount") else ""
        doc = "" if d["stakes"].get("documented") else " *(not stated in the opinion)*"
        w(f"| At stake | {amt}{cell(d['stakes']['note'])}{doc} |")
    if case.get("prior_history"):
        w(f"| History | {cell(case['prior_history'])} |")
    w(f"| Verification | `{d['verification']['status']}`, checked {d['verification']['checked_on']} |")
    w("")
    b = inc.get("boundary")
    if b:
        w(f"**Boundary specimen.** Tests: {', '.join(human(t) for t in b['tests'])}.")
        w("")
        w(f"*The case against including it.* {flat(b['against_inclusion'])}")
        w("")
        w(f"*Why it is here anyway.* {flat(b['why_included'])}")
        w("")
    if inc.get("notes"):
        w(f"**Curator's note.** {flat(inc['notes'])}")
        w("")
    if d["verification"].get("open_questions"):
        w("**Outstanding**")
        w("")
        for q in d["verification"]["open_questions"]:
            w(f"- {flat(q)}")
        w("")
    w("**Sources**")
    w("")
    for s_ in d["sources"]:
        line = f"- [{s_['kind']}]({s_['url']})"
        if s_.get("archived_url"):
            line += f" &middot; [archived]({s_['archived_url']})"
        w(line)
        for k, v in (s_.get("pinpoints") or {}).items():
            w(f"  <br>*{human(k)}* at {flat(v)}")
    w("")
    if d.get("pairs_with"):
        links = ", ".join(
            f"[{flat(o['title'])}](#{o['_anchor']})"
            for pid in d["pairs_with"] for o in docs if o["id"] == pid)
        if links:
            w(f"**Read alongside** {links}")
            w("")
    w("</details>")
    w("")
    w("---")
    w("")

w("<sub>Generated from `exhibits/*.yml` by `scripts/build_catalogue.py`. "
  "Edit the YAML, not this file.</sub>")

(ROOT / "CATALOGUE.md").write_text("\n".join(L) + "\n")
print(f"CATALOGUE.md — {n} exhibits, {n_clear} declared clear, "
      f"{n_confirmed}/{n} confirmed, {len(L)} lines")
