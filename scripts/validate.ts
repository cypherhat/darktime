import assert from 'node:assert/strict';import data from '../src/data/archive.json';
const entries=[...data.people,...data.organizations,...data.events];const ids=new Set(entries.map(e=>e.id));assert.equal(ids.size,entries.length,'Unique record IDs');const lanes=new Set(data.lanes.map(l=>l.id));
for(const e of entries){assert(e.pages.length>0,`${e.id}: missing citation`);for(const c of e.citations)assert(data.sources.some(s=>s.id===c.sourceId)&&c.pages.length,`${e.id}: invalid citation`);assert(e.history.length>0,`${e.id}: missing revision`)}
for(const e of data.events){assert(!Number.isNaN(Date.parse(e.date)),`${e.id}: invalid date`);for(const id of [...e.people,...e.organizations])assert(ids.has(id),`${e.id}: broken participant ${id}`);for(const id of e.lanes)assert(lanes.has(id),`${e.id}: missing lane`)}
for(const o of data.organizations)for(const id of o.members)assert(data.people.some(p=>p.id===id),`Invalid member ${id}`);
for(const r of data.relationships){assert(ids.has(r.fromId)&&ids.has(r.toId),`Broken relation ${r.id}`);assert(r.pages.length)}
assert(data.events.some(e=>e.lanes.length>1),'Expected timeline intersections');console.log(`Archive valid: ${data.people.length} people, ${data.organizations.length} organizations, ${data.events.length} events; references, citations, dates and intersections checked.`);
