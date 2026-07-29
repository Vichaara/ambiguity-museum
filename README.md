# The Ambiguity Museum

A curated collection of cases in which a dispute turned on what a written legal
instrument actually said, where the words admitted more than one reading and a court
had to pick one.

Each exhibit records the text verbatim, both readings, how the court resolved it in the
court's own words, what was at stake, and the smallest edit that would have prevented
the whole thing.

Start with [CATALOGUE.md](CATALOGUE.md).

---

## What counts

The collection is narrow on purpose. An exhibit qualifies only if **both** are true:

**(a) The text admits two or more discrete, enumerable readings.** You can write out
Reading A and Reading B. Not "the term is fuzzy," but two parses, both defensible.

**(b) The drafter could have prevented the dispute by editing the text alone**, without
knowing anything about what later happened.

That second test is the operational one. In *O'Connor v. Oakhurst Dairy*, adding one
comma ends the case, and you need to know nothing about dairy delivery routes to add
it. In a fight over whether a party used "reasonable efforts," no edit helps until
someone decides what counts as reasonable in that industry.

### Ambiguity, not vagueness

This is the distinction the whole collection rests on.

- **Ambiguity**: the text admits multiple *discrete* readings. "Packing for shipment or
  distribution" has exactly two parse trees, and you can enumerate them.
- **Vagueness**: one clear structure, an open-textured predicate. "Reasonable,"
  "material," "promptly," "substantial." No amount of parsing resolves it; it takes
  judgment about the world.

Both are written, both turn up constantly in contracts, and only the first is collected
here. Vagueness cases are more abundant and often more famous, which is why they are
excluded by rule rather than by taste. Including them would quietly suggest that
careful structure could resolve *"reasonable,"* which it cannot and should not.

### Also excluded

- **Scrivener's error and mutual mistake.** The text is *wrong* rather than ambiguous,
  which is a different problem with a different remedy.
- **Fact-finding.** Conduct, intent, credibility, what a party actually did. The dispute
  has to be about what the words say, not about what happened.

Criminal law is *not* excluded. Statutory interpretation in criminal cases produces some
of the sharpest exhibits here; see *Pulsifer*, where how a negation distributes across a
three-item list decides who may seek relief from a mandatory minimum. What gets excluded
is fact-finding, not a subject matter.

Subject matter is a separate question from the criterion, and an editorial one. A case
can qualify on the text and still be the wrong thing to put in a collection meant to be
read for pleasure. Where that happens, it stays out.

---

## The wings

**The core.** Text that was genuinely ambiguous, and the court said so.

**Declared clear** (`resolution.court_declared_ambiguous: false`). Cases where a court
held the text unambiguous, sometimes while the record showed sustained disagreement
about what it meant. In *White City*, the parties filed competing dictionary definitions
and expert affidavits, and the court called the term unambiguous in the next breath. In
*Chef America*, the claim was "susceptible to only one reasonable interpretation," and
that interpretation incinerates the product. Judicial confidence in clarity turns out to
be poor evidence of clarity.

**Boundary specimens** (`inclusion_test.boundary: true`). Exhibits that test the
collection's own rule: latent ambiguity that surfaces only once facts arrive, or a court
repairing syntax instead of parsing it. These are labelled rather than quietly dropped,
since a criterion that only gets applied to easy cases is not doing any work.

---

## What this is not

It is not a tool, a product, or a demo of one. Nothing here calls an API or resolves
anything automatically. It is a reading list with structure.

It is also not an argument that ambiguity is a failure of care. Several exhibits were
drafted by sophisticated parties with counsel and revisions; the *White City*
exclusivity clause went through three drafts and still never defined its central word.
In most of these cases the ambiguous term simply looked obvious enough that nobody
thought to define it.

---

## Structure

```
exhibits/     one YAML file per case, filename == id
schema/       exhibit.schema.json, the editorial policy in machine-checkable form
scripts/      validate.py, build_catalogue.py
CATALOGUE.md  generated. Edit the YAML, never this file
```

```bash
python3 scripts/validate.py          # check every exhibit against the schema
python3 scripts/build_catalogue.py   # regenerate CATALOGUE.md
```

### Why the schema is strict

Two rules are worth explaining, because both came out of getting it wrong first.

**`resolution.quote` must be verbatim.** An early draft of this collection was assembled
with automated research and then checked adversarially. Citations and quoted text came
through intact, while every paraphrased characterisation of a court's reasoning was
refuted. Paraphrase is therefore structurally impossible in the one field that proved
untrustworthy: quote the holding, or do not make the claim.

**Provenance is tracked per field rather than per exhibit.** Each source declares what it
confirms. A secondary source can support a dollar figure, but it can never be the sole
support for a citation, the disputed text, or the resolution quote. The validator
enforces this, so an exhibit marked `confirmed` that lacks primary or near-primary
coverage of those three fields fails the build.

Exhibits still being verified carry `verification.status: needs-primary` and say what is
outstanding. Three currently do, all pre-1998 English cases sitting behind bot-protected
archives. They stay in the collection with their gaps visible rather than omitted or
quietly guessed at.

---

## Contributing

Open a PR with one new file in `exhibits/`, then run both scripts. The validator runs on
the diff.

Before writing it, ask the two questions above. If you cannot write out two readings,
you have vagueness. If the fix needs facts, you have a dispute about the world.

Cite primary sources. If you can only reach a case brief or a news article, say so in
`verification.open_questions` and mark the exhibit `needs-primary`. An honest gap is
worth more than a confident guess, and this collection is read by people who will check.

---

## Licence

Code and schema: MIT. Exhibit data and prose: CC BY 4.0.

Quoted judicial text is reproduced from public court records.

---

Built by [Vichaara](https://vichaara.ai). We work on determinism in legal reasoning,
which is why we find these interesting, but nothing in this repository is part of that
product, and none of the product is required to read the exhibits.
