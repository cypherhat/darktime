import assert from "node:assert/strict";
import raw from "../src/data/archive.json";
import type { Archive, Citation } from "../src/types";
const data = raw as Archive;
const entries = [...data.people, ...data.organizations, ...data.events];
const ids = new Set(entries.map((e) => e.id));
const people = new Set(data.people.map((e) => e.id));
const organizations = new Set(data.organizations.map((e) => e.id));
const events = new Set(data.events.map((e) => e.id));
assert.equal(ids.size, entries.length, "Record IDs must be unique");
const lanes = new Set(data.lanes.map((l) => l.id));
const sources = new Map(data.sources.map((s) => [s.id, s]));
function validateCitations(cs: Citation[], id: string) {
  assert(cs.length, `${id}: missing citations`);
  for (const c of cs) {
    const source = sources.get(c.sourceId);
    assert(source, `${id}: unknown source ${c.sourceId}`);
    assert(c.pages.length, `${id}: missing pages`);
    for (const page of c.pages)
      assert(
        Number.isInteger(page) && page > 0 && page <= (source.pageCount || 26),
        `${id}: invalid page ${page}`,
      );
  }
}
for (const e of entries) {
  validateCitations(e.citations, e.id);
  assert(e.history.length, `${e.id}: missing history`);
  for (const a of e.accounts || [])
    assert(sources.has(a.sourceId), `${e.id}: unknown account source`);
}
for (const entry of entries) {
  for (const milestone of entry.milestones || []) {
    validateCitations(milestone.citations, `${entry.id}:${milestone.id}`);
    assert(
      !Number.isNaN(Date.parse(milestone.date)),
      `${entry.id}: invalid lifecycle date`,
    );
    assert(
      milestone.details.length >= 2,
      `${entry.id}: missing milestone context`,
    );
  }
}
for (const e of data.events) {
  assert(!Number.isNaN(Date.parse(e.date!)), `${e.id}: bad date`);
  if (e.endDate)
    assert(
      Date.parse(e.endDate) >= Date.parse(e.date!),
      `${e.id}: reversed interval`,
    );
  for (const id of e.people!)
    assert(people.has(id), `${e.id}: broken person ${id}`);
  for (const id of e.organizations!)
    assert(organizations.has(id), `${e.id}: broken organization ${id}`);
  for (const id of e.lanes!) assert(lanes.has(id), `${e.id}: missing lane`);
  assert(
    e.sourceSummaries?.length,
    `${e.id}: missing substantive source narrative`,
  );
  for (const s of e.sourceSummaries!) {
    assert(
      s.summary.length > 80 && s.details.length >= 2 && s.context.length > 40,
      `${e.id}: inadequate narrative`,
    );
    assert(
      e.citations.some((c) => c.sourceId === s.sourceId),
      `${e.id}: narrative without source citation`,
    );
  }
}
for (const o of data.organizations) {
  for (const id of o.members || [])
    assert(people.has(id), `${o.id}: invalid member ${id}`);
  for (const id of o.founderIds || [])
    assert(ids.has(id), `${o.id}: invalid founder ${id}`);
}
assert.equal(
  new Set(data.relationships.map((r) => r.id)).size,
  data.relationships.length,
  "Relationship IDs must be unique",
);
for (const r of data.relationships) {
  assert(ids.has(r.fromId) && ids.has(r.toId), `Broken relation ${r.id}`);
  validateCitations(r.citations, r.id);
}
for (const l of data.eventLinks || []) {
  assert(
    events.has(l.fromId) && events.has(l.toId),
    `Broken event influence ${l.id}`,
  );
  validateCitations(l.citations, l.id);
}
assert.notEqual("arnold-toynbee", "arnold-j-toynbee");
assert(
  people.has("arnold-toynbee") && people.has("arnold-j-toynbee"),
  "Distinct Toynbees must survive",
);
assert(
  !sources.has("gemstone"),
  "Only retained PDF sources belong in the archive",
);
for (const source of data.sources)
  assert(
    source.localPath?.endsWith(".pdf"),
    `${source.id}: source must be a local PDF`,
  );
assert(
  data.events.some((e) => e.lanes!.length > 1),
  "Expected intersections",
);
assert.equal(data.sources.length, 4, "Expected four PDF sources");
const byId = new Map(entries.map((entry) => [entry.id, entry]));
for (const event of data.events.filter((event) =>
  event.citations.some((citation) => citation.sourceId === "tragedy"),
)) {
  for (const id of [...event.people!, ...event.organizations!])
    assert(
      byId
        .get(id)
        ?.citations.some((citation) => citation.sourceId === "tragedy"),
      `${event.id}: participant ${id} lacks a book-specific account`,
    );
}
assert.equal(
  sources.get("tragedy")?.chapters?.length,
  77,
  "Tragedy and Hope chapter map must cover all 77 chapters",
);
console.log(
  `Archive valid: ${data.people.length} people, ${data.organizations.length} organizations, ${data.events.length} substantive event narratives, ${data.relationships.length} cited relationships, ${data.eventLinks?.length} attributed event links.`,
);
