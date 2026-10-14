import json
from pathlib import Path
p=Path('src/data/archive.json');d=json.loads(p.read_text());updated=0
for source in [s['id'] for s in d['sources']]:
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
p.write_text(json.dumps(d,indent=2)+'\n');print('Expanded narratives:',updated)
