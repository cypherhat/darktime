# Archive and review contract

Use repository types when they exist. This contract matches Dark Time while keeping the portable helpers independent of its four books or historical identities.

## Core records

The archive contains `sources`, `people`, `organizations`, `events`, `lanes`, `relationships` and optional `eventLinks`. A citation is `{ "sourceId": "source-a", "pages": [12, 13] }`; pages are 1-based PDF file positions. Optional printed labels are `{ "pdfPage": 12, "printed": 7 }` objects in `printedPages`. Do not subtract an assumed introduction offset throughout a book.

Sources have stable `id`, `title`, `author`, `localPath`, `pageCount`, `sha256`, `pageConvention` and a truthful `coverage` description. Edition-specific metadata, section maps and `evidenceIssues` help distinguish original body, notes, additions and conflicting dates. A new edition is a new source unless the bytes and pagination are the same.

All entities have `id`, `name`, `kind`, `role`, `description`, `citations`, `accounts`, `history` and optional `aliases`. `accounts` hold `{ "sourceId", "description", "role" }` so one source never overwrites another's account. `history` uses dated notes describing meaningful revisions. A description summarizes the source evidence, rather than inventing a generic biography.

An organization can add `founders` (qualified prose), `founderIds` and `members`. Do not populate these from all event participants. A donor, critic or regulator is not automatically a member. The edge label carries the actual role. Distinct legal entities may need separate IDs and cited continuation edges; an institution tracked through a name change needs an explicit identity note and date-qualified accounts.

## Relationships

```json
{
  "id": "source-a-rel-person-a-institution-b-director",
  "fromId": "person-a",
  "toId": "institution-b",
  "label": "Director",
  "description": "The author identifies A as a director of B in the stated period. This is a board role, not evidence of personal ownership.",
  "pages": [12],
  "citations": [{"sourceId": "source-a", "pages": [12]}],
  "evidence": "Office reported by the source; not independently verified"
}
```

Use optional `date` and `endDate` only when supported. A direction encodes the role, not necessarily a causal arrow. Source-specific roles or interpretations may require separate edges even for the same pair. If refining a generic edge, update its accepted-finding ledger too. Deduplicate by source, endpoints and meaning, not merely the pair or an unstable display title.

Important distinctions: founder vs funder; employee vs client; director vs shareholder; personal friendship vs same committee; legal predecessor vs similar name; administrative parent vs shared coalition; membership vs author-assigned faction; attribution vs independently corroborated fact. Explicit denials belong in the description and status rather than an affirmative affiliation.

## Events and entity lifecycles

An event adds `date`, optional `endDate`, `precision`, `people`, `organizations`, `lanes`, and `sourceSummaries`. A narrative contains `sourceId`, `summary`, at least two substantive `details`, `context` and optional `precisionNote`. Explain the source's account of the specific occurrence, its participants and its place in the timeline. A bibliographic citation alone is not an event narrative.

Year/month anchors are display coordinates; show precision to prevent false exact dates. Intervals represent source-supported periods, not guessed lifespans. Optional entity `milestones` contain stable ID, kind, date, precision, narrative and citations. Birth/death and institutional foundation/merger/dissolution dates need explicit supporting passages. Missing dates stay visibly unknown. Shared participation can connect tracks; `eventLinks` expressing influence require a source assertion and separate evidence.

## Review ledger

Store reusable findings independently of the rendered bundles:

```json
{
  "sourceId": "source-a",
  "reviewedIds": ["person-a", "institution-b"],
  "relationships": [{
    "fromId": "person-a", "toId": "institution-b", "label": "Director",
    "pages": [12], "description": "Substantive source account of the role.",
    "evidence": "Reported appointment"
  }],
  "profileUpdates": [{"id": "person-a", "description": "Source-specific account.", "pages": [12]}],
  "additionalAliases": [{"id": "institution-b", "aliases": ["Historical name"]}],
  "newPeople": [], "newOrganizations": [], "newEvents": [], "newLanes": [],
  "organizationUpdates": [], "eventUpdates": [],
  "rejectedCandidates": [{"id": "person-a", "pages": [21], "reason": "Same surname, different person."}],
  "unresolved": [],
  "coverage": {
    "pagesScreened": 30,
    "pagesReviewed": [12, 21],
    "limits": "All pages searched automatically; only the listed passages reviewed manually. OCR and unidentified variants remain limitations."
  },
  "summary": "Describe the actual completed review."
}
```

`reviewedIds` denotes candidate inventories screened, not a promise that every possible reference to those identities was read. Record excerpt vs full-page review when relevant. Unresolved leads need their reason and, when known, pages. Neither empty candidate output nor high graph degree proves completeness.

Save raw extracts outside shipped assets. The canonical archive is authoritative; collection and narrative bundles are generated outputs. A stable ledger and idempotent importer should reproduce accepted additions without multiplying links or dropping previous findings. Verify the importer with a before/after hash on a second run.

The portable importer accepts complete new records in `newPeople`, `newOrganizations` and `newEvents`, new lane objects in `newLanes`, and an optional `source` object for a source not yet registered. `organizationUpdates` explicitly update founder/member metadata; `eventUpdates` can expand a known event’s participants and source narrative using `sourceSummary`. These are reviewed changes, not automatic inferences from labels. It does not update an existing source’s edition metadata or remove disputed links; handle those deliberate corrections separately.
