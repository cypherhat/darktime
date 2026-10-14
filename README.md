# Dark Time

A browser-only, source-attributed historical atlas. Explore linked characters, organizations, events, professional affiliations and author-claimed influence through searchable directories, intersecting timelines and a focused connections graph.

Live: https://cypherhat.github.io/darktime/

## Collections

The archive contains **357 people, 158 organizations, 221 events, 694 relationships and 26 timeline threads**, plus five explicitly cited links between events. Shared identities are counted once; collection counts overlap.

- **Gemstone letters**: 25 people, 9 organizations, 18 events. Selective extraction of the transcription attributed to Bruce Porter Roberts, including retrospective claims. The transcription has missing material, conflicting dates and amounts, and a truncated ending.
- **Carroll Quigley, The Anglo-American Establishment**: 170 people, 70 organizations, 90 events. Selected passages from all thirteen chapters and the tentative appendix roster. Quigley’s reported institutional roles are distinguished from inferred network membership and bracketed conjectures.
- **Peter Dale Scott, The State, the Deep State, and the Wall Street Overworld**: 72 people, 40 organizations, 37 events. Article and notes reviewed; important denials, memoir qualifications and publication-date discrepancies are preserved.
- **Carl Oglesby, The Yankee and Cowboy War**: 111 people, 49 organizations, 76 events. Selected records across the narrative, revised preface and appendix. His faction model, alternative accounts, official findings and denials retain their attribution. OCR uncertainty is noted.

These are substantive attributed digests, not exhaustive indexes of every passing reference. The books’ interpretation of an event is not independent corroboration. Citations use **1-based PDF file pages**; printed-page references are included where discernible. The original PDFs in `docs/` and `sources/` remain local research files and are not redistributed by the website. All event narratives are embedded static assets, with no outbound source links required.

## Browser-only architecture

React, TypeScript and D3, built by Vite and served by GitHub Pages. No backend, database, secrets or visitor accounts. Source bundles load only when selected; long event narratives load when a record is opened. Timeline and graph code also load on demand. Directories and relationship inventories are paginated. The graph defaults to a core overview or a selected entity’s neighborhood.

Select arbitrary source combinations with the **Choose sources to overlay** checkboxes. Vertical connectors identify a single event shared across threads. Dashed arcs join chronological events through a shared cited participant across sources; solid arrows represent source-claimed influence or organizational continuation. A shared person does not establish causal influence. Source attribution remains visible in event narratives and relationship records. The Quigley–Gemstone overlay has an explicit shared Churchill identity; Roberts’ 1932 alliance story remains a separately identified allegation.

Timelines provide UTC dates, year-bearing tick labels, smooth pan/zoom, period and participant filters, precision/duration bars, readable full-title labels, staggered numbered markers, hover/focus previews, and a matching event list. Clicking a marker opens substantive source paragraphs and explains the point’s relevance to its threads.

Stable IDs support shareable URLs, e.g. `?collection=gemstone,anglo#election`. Previous `#nader` links still resolve. Export downloads the complete archive, including detailed narratives.

## Develop and validate

Use Node 22 or newer.

```sh
npm ci
npm run dev
npm run check
npm run build
```

`npm run prepare:data` regenerates collection bundles, narrative bundles and the small catalog from the canonical `src/data/archive.json`. It runs automatically before development/build. `dist/` is a portable static site with relative asset URLs.

Browser checks use Playwright. On macOS, the configuration uses installed Google Chrome; override with `PLAYWRIGHT_CHROME_PATH`. On other platforms, install Playwright Chromium. With a dev server running on port 5173:

```sh
npm run test:browser
```

To test the production build, serve it on port 5174 and set `PLAYWRIGHT_BASE_URL=http://127.0.0.1:5174`. The tests cover lazy source loading, marker interaction, year labels, source narratives, pagination, multi-source overlays, old deep links, cross-source identities and mobile layout.

GitHub Actions validates and builds `main`, then deploys to Pages. Its `github-pages` environment allows `main`.

## Extend the archive

Edit `src/data/archive.json`, the authoritative dataset. Keep IDs stable. Each record has citations, dated revisions, source-specific accounts and optional aliases. Each event also has source summaries with a lead summary, substantive paragraphs, timeline context and any precision note. Event date anchors never silently convert unknown dates into exact days. Organization members/associates may represent different types of relationship, identified through cited edges.

Use distinct identities for people with similar names. Merge only when the text establishes the identity, and retain source-specific accounts instead of overwriting them. Add `eventLinks` only when a source actually asserts the relationship. The renderer does not infer causal links from chronological proximity.

For a new collection, register source metadata, associate its lane definitions with the source ID and add its records/citations. The build discovers generated source/narrative bundles automatically. Run the validator, build and browser checks before committing.

The ingestion scripts and `scripts/data/` research artifacts document this initial extraction. `scripts/seed.py` regenerates the first Gemstone seed only and must **not** be run over an expanded collection. `ingest-anglo.py`, `merge-research.py`, `apply-summaries.py` and `add-overlay-evidence.py` record the staged additions; the canonical archive remains authoritative for subsequent manual revisions.
