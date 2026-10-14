# Dark Time

A browser-only historical atlas: linked characters, organizations, events, and intersecting timelines. React + TypeScript + D3, bundled with Vite. No server, database, API keys, or account required by visitors. Data is bundled locally; the optional Google Fonts stylesheet falls back to local fonts.

## Develop

Use Node 22 or newer.

```sh
npm ci
npm run dev
npm run check
npm run build
```

Deploy `dist/` to any static host. Relative asset paths and hash record links work on GitHub Pages subdirectories. `.github/workflows/pages.yml` validates and deploys main to GitHub Pages; enable **Settings → Pages → Source → GitHub Actions**.

## Expand the archive

The authoritative content file is `src/data/archive.json`. Keep IDs stable. Add source metadata, people, organizations, events, relationships, and lane definitions. Each record has page references and a dated description history. Organization entries record unresolved founders explicitly. Event precision distinguishes day, month, approximate and disputed dates. First-of-month values are plotting anchors, not claims of an exact day. Add a history entry when revising a description; preserve earlier revisions.

The initial dataset is a **selective extraction** from https://realgemstonefile.blogspot.com/, accessed October 14, 2026. It covers 22 people, 9 organizations and 17 dated passages across five threads. It does not exhaust every name or historical allusion. The supplied transcription contains missing passages and ends mid-sentence on page 26. All source claims are unverified here; historical calendar dates supplied as editorial context are noted in event descriptions. Conflicting amounts, times and dates are retained explicitly. Each record has a `citations` array with source IDs and page references. Add citations to additional sources as the collection grows; the legacy `pages` field refers to the initial source. For conflicting individual assertions, retain their attribution in the description.

## Timeline

D3 UTC time scales, SVG vector rendering, adaptive date ticks, touch/pinch and wheel zoom, drag pan, animated zoom controls, and keyboard-accessible event points. Zoom reaches day-level detail; labels are culled to prevent overlap. Vertical connectors identify the same event in several lanes, not evidence of causal relationships. Lane filters and text search narrow the plot; participants open linked profiles. Record detail URLs use stable hashes. Archive export downloads the complete JSON dataset.

## Content workflow

1. Read new materials and register sources.
2. Add or amend records and source-specific citations; keep uncertainty explicit.
3. Update dated description histories.
4. Run `npm run check` and `npm run build`.
5. Commit and push to main to publish.

`scripts/seed.py` documents the initial extraction and regenerates that first dataset only. Do not run it over an expanded collection.
