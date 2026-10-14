# Dark Time

A browser-only, source-attributed historical atlas. Explore linked characters, organizations, events, professional affiliations and author-claimed influence through searchable directories, intersecting timelines and a focused connections graph.

Live: https://cypherhat.github.io/darktime/

## Collections

Tragedy and Hope is the default collection. Explicit source selections and record deep links retain their selected collection.

The archive contains **477 people, 247 organizations, 450 events, 1,332 relationships and 29 timeline threads**, plus 72 explicitly cited links between events. Shared identities are counted once; collection counts overlap.

- **Carroll Quigley, The Anglo-American Establishment**: 170 people, 76 organizations, 90 events. Selected passages from all thirteen chapters and the tentative appendix roster. Quigley’s reported institutional roles are distinguished from inferred network membership and bracketed conjectures.
- **Peter Dale Scott, The State, the Deep State, and the Wall Street Overworld**: 74 people, 42 organizations, 37 events. Article and notes reviewed; important denials, memoir qualifications and publication-date discrepancies are preserved.
- **Carl Oglesby, The Yankee and Cowboy War**: 117 people, 57 organizations, 76 events. Selected records across the narrative, revised preface and appendix. His faction model, alternative accounts, official findings and denials retain their attribution. OCR uncertainty is noted.

- **Carroll Quigley, Tragedy and Hope**: 196 people, 131 organizations, 247 events, 296 affiliations and 70 event connections across eight threads. A selective institutional and political digest of the supplied 1,090-page annotated PDF, emphasizing finance, empire, world wars and connections through the 1950s, with selected 1960s developments. Later introductory material and identified bracketed editorial additions are excluded from Quigley-attributed accounts. Dates, inconsistencies and coverage limits remain visible.

These are substantive attributed digests, not exhaustive indexes of every passing reference. The books’ interpretation of an event is not independent corroboration. Citations use **1-based PDF file pages**; printed-page references are included where discernible. The original PDFs in the single canonical `docs/` directory remain local research files and are not redistributed by the website. All event narratives are embedded static assets, with no outbound source links required.

## Browser-only architecture

React, TypeScript and D3, built by Vite and served by GitHub Pages. No backend, database, secrets or visitor accounts. Source bundles load only when selected; long event narratives load when a record is opened. Timeline and graph code also load on demand. Directories and relationship inventories are paginated. The graph defaults to a core overview or a selected entity’s neighborhood.

Select arbitrary source combinations with the **Choose sources to overlay** checkboxes. Vertical connectors identify a single event shared across threads. Dashed arcs join chronological events through a shared cited participant across sources; solid arrows represent source-claimed influence or organizational continuation. A shared person does not establish causal influence. Source attribution remains visible in event narratives and relationship records. The PDF-based collections share cited identities; each source’s interpretation remains separately attributed.

Timelines provide UTC dates, year-bearing tick labels, smooth pan/zoom, period and participant filters, precision/duration bars, readable full-title labels, staggered numbered markers, hover/focus previews, and a matching event list. Source checkboxes stay pinned above the timeline. Thread controls, collections and the matching event list fold away; the diagram uses the document’s vertical scrolling instead of a nested scroll area. Click a marker to highlight its cross-thread connectors and open a persistent event panel alongside the diagram. Browse Connections and Source account tabs, follow clickable people, organizations and events, and use Back to retrace your path. The prominent Show details button reopens the panel. On mobile the panel docks below the diagram. Highlights persist through zoom and scrolling. Use the zoom buttons or Ctrl/Command + scroll to zoom; ordinary scrolling moves the page.

Choose **People & organization timelines** to build one or several aligned tracks from any records in the selected sources, or use **View timeline** in a record’s details. Shared events connect the tracks. Comparisons can be shared through `tracks=person-id,organization-id` in the URL. Explicitly cited birth/death, career and institutional-change milestones supplement the event inventory; missing lifespan endpoints are labeled, never inferred from first/last appearances. The initial lifecycle data includes 16 cited lifespan pairs and nine career or institutional milestones. These are embedded on their parent records rather than expanding the global event inventory with every birthday.

Stable IDs support shareable URLs, e.g. `?collection=tragedy,scott#allen-dulles`. Retired source IDs in overlay URLs are ignored; a retired-only selection falls back to Tragedy and Hope. Export downloads the complete archive, including detailed narratives.

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

The ingestion scripts and `scripts/data/` research artifacts document the PDF extraction. `ingest-anglo.py`, `merge-research.py`, `ingest-tragedy.py`, `ingest-lifecycle.py` and `apply-summaries.py` record the staged additions; the canonical archive remains authoritative for subsequent manual revisions. Only PDF sources listed in the canonical archive are selectable or exported.

The duplicate Anglo-American Establishment PDF formerly in `sources/` was removed after SHA-256 comparison with `docs/anglo.pdf`. All source metadata uses paths in `docs/`. Tragedy and Hope uses PDF-file pages rather than the original printed pagination; its chapter map records all 77 chapters, while the digest covers the selected passages described in its source notes.

PDF affiliation audits are stored in `scripts/data/connection-audit-*.json`. They record reviewed identities, accepted page-cited relationships, profile corrections and unresolved cases. Run `python3 scripts/ingest-connection-audit.py` to merge them; `npm run check` verifies every accepted finding remains in the archive. The October 2026 pass added 411 links and refined 30 existing ones across the four sources. Tragedy and Hope received a full profile/edge inventory review with targeted passage rereading; this does not exhaust every affiliation in the 1,090-page book. Unnamed counterparts, identity ambiguities and unsupported claims remain unresolved rather than becoming inferred graph edges.
