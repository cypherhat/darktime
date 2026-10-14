"""Merge reviewed PDF affiliations; safe to rerun without multiplying edges."""
import json,re
from pathlib import Path
path=Path('src/data/archive.json'); archive=json.loads(path.read_text())
records={r['id']:r for kind in ['people','organizations'] for r in archive[kind]}
sources={s['id']:s for s in archive['sources']}
added=updated=0
for file in sorted(Path('scripts/data').glob('connection-audit-*.json')):
 audit=json.loads(file.read_text()); source=audit['sourceId']
 assert source in sources
 assert set(audit['reviewedIds']) <= records.keys()
 for row in audit['relationships']:
  assert row['fromId'] in records and row['toId'] in records
  assert row['description'] and row['evidence']
  assert all(isinstance(p,int) and 0<p<=sources[source]['pageCount'] for p in row['pages'])
  matches=[r for r in archive['relationships'] if {r['fromId'],r['toId']}=={row['fromId'],row['toId']} and any(c['sourceId']==source for c in r['citations'])]
  exact=next((r for r in matches if r['label']==row['label']),None)
  generic=next((r for r in matches if r['label'].lower() in ['associated with','association','affiliation','associated']),None)
  edge=exact or generic
  if edge: updated+=1
  else:
   slug=re.sub(r'[^a-z0-9]+','-',row['label'].lower()).strip('-')
   edge={'id':f"{source}-audit-{row['fromId']}-{row['toId']}-{slug}"}
   archive['relationships'].append(edge);added+=1
  edge.update(row)
  edge['citations']=[{'sourceId':source,'pages':row['pages']}]
  for id in [row['fromId'],row['toId']]:
   record=records[id]
   note={'date':'2026-10-14','note':f'Connection audit added or refined page-cited affiliations from {source}.'}
   if note not in record['history']: record['history'].append(note)
   citation=next((c for c in record['citations'] if c['sourceId']==source),None)
   if citation: citation['pages']=sorted(set(citation['pages']+row['pages']))
   else: record['citations'].append({'sourceId':source,'pages':row['pages']})
 for update in audit.get('profileUpdates',[]):
  record=records[update['id']];account=next((a for a in record.get('accounts',[])if a['sourceId']==source),None)
  if account:account['description']=update['description']
  else:record.setdefault('accounts',[]).append({'sourceId':source,'description':update['description'],'role':record['role']})
  if record['citations'][0]['sourceId']==source:record['description']=update['description']
  citation=next((c for c in record['citations'] if c['sourceId']==source),None)
  if citation: citation['pages']=sorted(set(citation['pages']+update['pages']))
  else: record['citations'].append({'sourceId':source,'pages':update['pages']})
archive['updated']='2026-10-14'
path.write_text(json.dumps(archive,indent=2)+'\n')
print(f'{added} new links; {updated} existing links refined; {len(archive["relationships"])} total')
