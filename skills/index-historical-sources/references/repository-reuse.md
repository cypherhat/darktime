# Reusing the indexing workflow

Copy the whole `skills/index-historical-sources` folder into the destination repository. Its `SKILL.md`, reference files and Python helpers are portable; they do not require Dark Time's books or a backend. An agent can invoke the skill by its path, or install that folder in its configured skills directory. Installation outside the workspace is a separate operation and is not performed by this workflow.

For a new corpus, define a clean archive and register only its own sources. Keep canonical originals in one directory, commonly `docs/`; decide separately whether those originals may be committed or redistributed. Place temporary extracts in an ignored working directory. The extracted page arrays are input to the scanner, not published source files.

Example from the destination repository (use the actual revision date):

```sh
python3 skills/index-historical-sources/scripts/prepare_pdf.py docs/book.pdf --source-id book --title "Book title" --author "Author" --output-dir tmp/pdfs
python3 skills/index-historical-sources/scripts/scan_mentions.py --archive src/data/archive.json --pages-dir tmp/pdfs --output-dir tmp/review
python3 skills/index-historical-sources/scripts/merge_findings.py --archive src/data/archive.json --finding tmp/review/book-review.json --revision-date 2026-10-14
python3 skills/index-historical-sources/scripts/validate_index.py src/data/archive.json
```

The scanner accepts `--aliases tmp/review/variants.json`, a JSON object mapping entity IDs to candidate name variants. Review an alias before committing it to the entity. It suggests organization base names, initial-free personal names and case-sensitive acronyms as review leads. Generated acronyms can be wrong or shared by unrelated institutions; its surname candidates likewise cannot resolve relatives or namesakes. It does not interpret OCR damage or prove corporate continuity on its own. Re-run after accepted identities or aliases change.

If cloning the application as well as the skill, adapt these project-specific parts:

- `src/types.ts`: retain or deliberately adapt the record contract before changing importers.
- `src/main.tsx`: choose a default source from the new corpus; Dark Time's default is `tragedy`. Keep multi-source selection available throughout the application.
- `scripts/split-archive.mjs`: regenerate catalog, collection and narrative bundles from the new canonical archive. Do not hand-edit generated bundles.
- `scripts/validate.ts` and `tests/archive.spec.ts`: retain structural and interaction tests, but replace Dark Time's source counts, specific identities and fixture assertions with the new corpus's invariants. The portable validator provides a corpus-independent baseline.
- `vite.config.ts`, `package.json`, page title, branding and GitHub Pages workflow: adapt the repository name and base URL. Preserve distinct Pages artifact names for retry attempts. Publishing requires the destination user's authorization.
- Old source-specific ingestion scripts and research artifacts: remove or replace them deliberately so they cannot reintroduce the original historical dataset on a later import. Preserve the generic citation, identity and merge checks.

When refreshing an established corpus, preserve existing IDs and source accounts. A revised edition with shifted pages gets its own source ID and page map. Add new evidence rather than replacing a disputed account with an unqualified synthesis.

A completion report should state separately: text extraction coverage, automated screening coverage, manual passage review, accepted affiliations, rejected collisions, unresolved work, and application/deployment verification. Counts and a successful build do not certify historical truth or exhaustive extraction.
