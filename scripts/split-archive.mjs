import fs from 'node:fs/promises';
const root=new URL('../src/data/',import.meta.url);const archive=JSON.parse(await fs.readFile(new URL('archive.json',root),'utf8'));
await fs.mkdir(new URL('collections/',root),{recursive:true});await fs.mkdir(new URL('narratives/',root),{recursive:true});const counts={};const recordSources={};
for(const item of [...archive.people,...archive.organizations,...archive.events])recordSources[item.id]=[...new Set(item.citations.map(c=>c.sourceId))];
for(const source of archive.sources){
 const narratives=Object.fromEntries(archive.events.filter(e=>e.sourceSummaries?.some(s=>s.sourceId===source.id)).map(e=>[e.id,e.sourceSummaries.filter(s=>s.sourceId===source.id)]));await fs.writeFile(new URL(`narratives/${source.id}.json`,root),JSON.stringify(narratives));
 const belongs=e=>e.citations.some(c=>c.sourceId===source.id);const subset={...archive,people:archive.people.filter(belongs),organizations:archive.organizations.filter(belongs),events:archive.events.filter(belongs),relationships:archive.relationships.filter(belongs),lanes:archive.lanes.filter(l=>l.sourceIds?.includes(source.id))};
 // Include any explicitly linked record from another collection so links cannot break.
 subset.eventLinks=(archive.eventLinks||[]).filter(e=>belongs(e));subset.references=[];const ids=new Set([...subset.people,...subset.organizations,...subset.events].map(e=>e.id));
 const referenced=new Set(subset.relationships.flatMap(r=>[r.fromId,r.toId]));for(const e of subset.events)for(const id of [...e.people,...e.organizations])referenced.add(id);
 for(const o of subset.organizations)for(const id of [...o.members,...(o.founderIds||[])])referenced.add(id);
 for(const key of ['people','organizations','events'])for(const e of archive[key])if(referenced.has(e.id)&&!ids.has(e.id)){subset.references.push(e);ids.add(e.id)}
 counts[source.id]=Object.fromEntries(['people','organizations','events','relationships','lanes'].map(k=>[k,subset[k].length]));await fs.writeFile(new URL(`collections/${source.id}.json`,root),JSON.stringify(subset,function(key,value){if(key==='sourceSummaries')return undefined;if(key==='accounts'&&value.length===1&&value[0].description===this.description)return undefined;return value;}));
}
counts.all=Object.fromEntries(['people','organizations','events','relationships','lanes'].map(k=>[k,archive[k].length]));
await fs.writeFile(new URL('catalog.json',root),JSON.stringify({version:archive.version,updated:archive.updated,sources:archive.sources,counts,recordSources}));console.log('Static collection bundles generated:',counts);
