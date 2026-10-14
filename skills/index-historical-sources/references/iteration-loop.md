# Iterative reference discovery and review

Run from a repository with registered sources, seed identities, and page-preserving extracts:

```sh
python3 skills/index-historical-sources/scripts/iterate_references.py --archive src/data/archive.json --pages-dir tmp/pdfs --state-dir tmp/index-iterations --until-stable
```

Requires Python 3 on macOS/Linux (standard-library `fcntl` protects against simultaneous runs). Keep the state directory ignored. The command writes no archive records or graph edges.

The cumulative ladder searches registered names and aliases; short names and acronym leads; surnames, initials and corporate suffixes; compact/dehyphenated forms; bounded OCR confusions; then single-edit long tokens with another exact name anchor. Short acronyms and standalone surnames are never fuzzy-matched. These are candidate rules, not identity evidence. Acronyms, surnames and OCR substitutions can produce false positives.

All six levels must run before stopping. The loop then requires two consecutive passes adding zero new references. `--max-passes 12` bounds one invocation; exceeding it exits unsuccessfully and preserves resumable state. Omit `--until-stable` to advance one pass, review, update the inputs, and resume. Changes to the engine, sources, extracted text, identities, aliases or approved equivalences restart the ladder and quiet counter. Previously discovered references remain in the history; inactive passages do not enter the current queue.

A reference is one canonical identity in one source paragraph, located by PDF page, paragraph ordinal and normalized text hash. Multiple aliases or rules hitting that passage count once. Distinct paragraphs, pages and sources remain separate. Two people sharing a surname stay separate. This measures passage discovery, not the number of token occurrences or accepted relationships.

## Review feedback

`review-queue.json` contains active reference IDs, source/page locators, excerpts, matching rules and evidence hashes. Read the full passage and surrounding text before making a decision. `state.json` preserves discovery history; `report.json` records counts, input revision, per-pass results and separate discovery/review completion flags.

Supply candidate variants with `--aliases variants.json`, mapping entity IDs to arrays of strings. Add new identities found through section reading to the archive, using stable IDs. Both changes trigger a fresh cycle.

Deduplication across identity IDs requires `--equivalences approved.json`:

```json
[{"fromId":"variant-id","toId":"canonical-id","reason":"The cited passage explicitly identifies the same institution.","citations":[{"sourceId":"book","pages":[12]}]}]
```

Both IDs must exist and have the same kind; citations and a substantive reason are required. Cycles and conflicting mappings are rejected. Equivalences consolidate the reference queue only. Review and merge actual archive identities separately, preserving citations and relationships. Revoking an equivalence restores separate references. No fuzzy match automatically merges identities.

Supply reviewed decisions with `--decisions decisions.json`:

```json
{"reference-id":{"status":"accepted","reason":"Full passage resolves the name and explicit role.","evidenceHash":"copy the current queue hash"}}
```

Statuses are `accepted`, `rejected` or `unresolved`; all require a reason. A missing decision or outdated evidence hash is pending. Changed matching evidence requires renewed review. Accepting a candidate reference is not automatically accepting a graph relationship; use the ordinary reviewed finding ledger and merger for those.

After reviewing and importing findings, rerun discovery against the resulting archive. Repeat widening and review until discovery has two quiet passes and every active candidate has a current resolved decision. `searchSaturated` alone means the configured search stabilized. `reviewComplete` additionally requires zero pending and unresolved references. Neither flag certifies exhaustive historical coverage: unreadable OCR, unnamed entities, unknown aliases and implicit relationships require further reading, improved extraction or new rules, followed by another cycle.

Run the mechanism's regression fixtures with:

```sh
python3 -m unittest discover -s skills/index-historical-sources/tests -v
```
