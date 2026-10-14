import json
from pathlib import Path
p=Path('src/data/archive.json');d=json.loads(p.read_text());updated=0
for source in ['gemstone','anglo','scott','yankee']:
 f=Path(f'scripts/data/{source}-event-summaries.json')
 if not f.exists():continue
 summaries=json.loads(f.read_text())
 if 'events' in summaries:summaries=summaries['events']
 if isinstance(summaries,list):summaries={e['id']:e for e in summaries}
 for e in d['events']:
  if e['id'] not in summaries:continue
  summary=summaries[e['id']];assert summary.get('sourceId',source)==source
  summary['sourceId']=source
  if 'details' in summary:assert isinstance(summary['details'],list)
  e['sourceSummaries']=[x for x in e.get('sourceSummaries',[]) if x['sourceId']!=source]+[summary]
  e['description']=summary['summary']
  if not any(h['note']=='Expanded source narrative and timeline context.'for h in e['history']):e['history'].append(dict(date='2026-10-14',note='Expanded source narrative and timeline context.'))
  for a in e.get('accounts',[]):
   if a['sourceId']==source:a['description']=summary['summary']
  updated+=1
# More descriptive names for the original collection, while keeping stable deep-link IDs.
names={'election':'Nixon’s election and Roberts’ claimed leverage','court':'Traffic ticket dismissed; Roberts invokes Cambodia','collision':'Roberts reports an Alioto-family collision','legal-help':'Roberts asks Nixon and Mitchell for legal help','settlement':'Nader–GM settlement: Roberts alleges a connection','look-story':'Carlson’s Alioto story omits Roberts’ collision account','nader-letter':'Roberts sends Nader his Chappaquiddick account','insert':'Roberts joins three claims in a later summary'}
for e in d['events']:
 if e['id'] in names:e['name']=names[e['id']]
 if e['id']=='election':
  for c in e['citations']:
   if c['sourceId']=='gemstone':c['pages']=sorted(set(c['pages']+[8]))
p.write_text(json.dumps(d,indent=2)+'\n');print('Expanded narratives:',updated)
