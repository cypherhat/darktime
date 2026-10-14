"""Merge reviewed PDF affiliations; safe to rerun without multiplying edges."""
import argparse,datetime,json,re,subprocess,sys,tempfile
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--archive',type=Path,required=True)
parser.add_argument('--finding',type=Path,action='append',required=True)
parser.add_argument('--revision-date',default=datetime.date.today().isoformat())
args=parser.parse_args()
revision_date=datetime.date.fromisoformat(args.revision_date).isoformat()
path=args.archive;archive=json.loads(path.read_text())
records={r['id']:r for kind in ['people','organizations','events'] for r in archive[kind]}
sources={s['id']:s for s in archive['sources']}
added=updated=0
files=args.finding
for file in files:
 audit=json.loads(file.read_text())
 if audit.get('source') and audit['sourceId'] not in sources:
  assert audit['source']['id']==audit['sourceId']
  archive['sources'].append(audit['source']);sources[audit['sourceId']]=audit['source']
 for lane in audit.get('newLanes',[]):
  if not any(l['id']==lane['id'] for l in archive.get('lanes',[])):archive.setdefault('lanes',[]).append(lane)
# New counterparties may be referred to by a different source's findings.
for file in files:
 audit=json.loads(file.read_text()); source=audit['sourceId']
 for kind,key in [('person','newPeople'),('organization','newOrganizations'),('event','newEvents')]:
  for row in audit.get(key,[]):
   if row['id'] in records:
    assert records[row['id']]['name']==row['name'], f"Conflicting identity {row['id']}"
    if row.get('milestones'):
     existing=records[row['id']]
     for m in row['milestones']:
      existing['milestones']=[old for old in existing.get('milestones',[]) if old['id']!=m['id']]+[m]
    continue
   row=dict(row);row.setdefault('kind',kind);row.setdefault('role',{'organization':'Institution described in source','person':'Person described in source','event':'Event described in source'}[kind])
   row.setdefault('citations',[{'sourceId':source,'pages':row['pages']}])
   row.setdefault('accounts',[{'sourceId':source,'description':row['description'],'role':row['role']}])
   row.setdefault('history',[{'date':revision_date,'note':f'Added from source-wide passage review of {source}.'}])
   row.setdefault('aliases',[])
   if kind=='organization':
    row.setdefault('members',[]);row.setdefault('founderIds',[]);row.setdefault('founders','Not established by the cited passages.')
   archive[{'person':'people','organization':'organizations','event':'events'}[kind]].append(row);records[row['id']]=row
for file in files:
 audit=json.loads(file.read_text()); source=audit['sourceId']
 assert source in sources
 assert set(audit.get('reviewedIds',[])) <= records.keys()
 for row in audit.get('relationships',[]):
  assert row['fromId'] in records and row['toId'] in records
  assert row['description'] and row['evidence']
  assert row['pages'] and all(isinstance(p,int) and not isinstance(p,bool) and 0<p<=sources[source]['pageCount'] for p in row['pages'])
  matches=[r for r in archive['relationships'] if {r['fromId'],r['toId']}=={row['fromId'],row['toId']} and len(r['citations'])==1 and r['citations'][0]['sourceId']==source]
  exact=next((r for r in matches if r['label']==row['label']),None)
  generic=next((r for r in matches if r['label'].lower() in ['associated with','association','affiliation','associated']),None)
  edge=exact or generic
  if edge: updated+=1
  else:
   slug=re.sub(r'[^a-z0-9]+','-',row['label'].lower()).strip('-')
   edge={'id':f"{source}-audit-{row['fromId']}-{row['toId']}-{slug}"}
   archive.setdefault('relationships',[]).append(edge);added+=1
  edge.update(row)
  edge['citations']=[{'sourceId':source,'pages':row['pages']}]
  for id in [row['fromId'],row['toId']]:
   record=records[id]
   note={'date':revision_date,'note':f'Connection audit added or refined page-cited affiliations from {source}.'}
   if note not in record.setdefault('history',[]): record['history'].append(note)
   citation=next((c for c in record['citations'] if c['sourceId']==source),None)
   if citation: citation['pages']=sorted(set(citation['pages']+row['pages']))
   else: record['citations'].append({'sourceId':source,'pages':row['pages']})
 for update in audit.get('profileUpdates',[]):
  record=records[update['id']];account=next((a for a in record.get('accounts',[])if a['sourceId']==source),None)
  if account:
   account['description']=update['description']
   if update.get('role'):account['role']=update['role']
  else:record.setdefault('accounts',[]).append({'sourceId':source,'description':update['description'],'role':record['role']})
  if record['citations'][0]['sourceId']==source:record['description']=update['description']
  citation=next((c for c in record['citations'] if c['sourceId']==source),None)
  if citation: citation['pages']=sorted(set(citation['pages']+update['pages']))
  else: record['citations'].append({'sourceId':source,'pages':update['pages']})
 for update in audit.get('organizationUpdates',[]):
  record=records[update['id']]
  for key in ['founders','founderIds','members']:
   if key in update:record[key]=update[key]
 for update in audit.get('eventUpdates',[]):
  event=next(e for e in archive['events'] if e['id']==update['id'])
  for key in ['name','description','people','organizations','pages']:
   if key in update:event[key]=update[key]
  summary=update['sourceSummary'];sid=summary['sourceId']
  event['sourceSummaries']=[s for s in event['sourceSummaries'] if s['sourceId']!=sid]+[summary]
  c=next(c for c in event['citations']if c['sourceId']==sid);c['pages']=update['pages']
  account=next((a for a in event.get('accounts',[])if a['sourceId']==sid),None)
  if account:account['description']=update['description']
  note={'date':revision_date,'note':'Expanded event participants and narrative from the source-wide passage review.'}
  if note not in event['history']:event['history'].append(note)
 for item in audit.get('additionalAliases',[]):
  record=records[item['id']];record['aliases']=list(dict.fromkeys(record.get('aliases',[])+item['aliases']))
archive['updated']=revision_date
# Validate a temporary result before replacing the destination archive.
with tempfile.TemporaryDirectory() as temp:
 candidate=Path(temp)/'archive.json';candidate.write_text(json.dumps(archive,indent=2)+'\n')
 subprocess.run([sys.executable,str(Path(__file__).with_name('validate_index.py')),str(candidate)],check=True)
 path.write_text(candidate.read_text())
print(f'{added} new links; {updated} existing links refined; {len(archive["relationships"])} total')
