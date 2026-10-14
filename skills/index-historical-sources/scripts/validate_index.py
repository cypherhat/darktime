#!/usr/bin/env python3
"""Portable structural checks, independent of source count or historical identities."""
import argparse,json,datetime
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);args=p.parse_args();data=json.loads(args.archive.read_text())
def check(ok,message):
 if not ok:raise SystemExit(message)
def unique(rows,label):
 ids=[r['id']for r in rows];check(len(ids)==len(set(ids)),f'{label}: duplicate IDs');return {r['id']:r for r in rows}
sources=unique(data.get('sources',[]),'Sources');check(bool(sources),'No sources')
for s in sources.values():check(isinstance(s.get('pageCount'),int)and s['pageCount']>0,f'{s["id"]}: missing positive PDF pageCount')
records=data.get('people',[])+data.get('organizations',[])+data.get('events',[])
index=unique(records,'Records');people={r['id']for r in data.get('people',[])};orgs={r['id']for r in data.get('organizations',[])};events={r['id']for r in data.get('events',[])};lanes={r['id']for r in data.get('lanes',[])}
def citations(cs,id):
 check(bool(cs),f'{id}: missing citations')
 for c in cs:
  sid=c['sourceId'];check(sid in sources,f'{id}: unknown source {sid}');check(bool(c.get('pages')),f'{id}: no page locators')
  for page in c['pages']:check(isinstance(page,int)and not isinstance(page,bool)and 0<page<=sources[sid]['pageCount'],f'{id}: invalid PDF page {page}')
def date(value,id):
 try:return datetime.date.fromisoformat(value)
 except (ValueError,TypeError):raise SystemExit(f'{id}: invalid date {value}')
for r in records:
 check(bool(r.get('name'))and bool(r.get('description')),f'{r["id"]}: missing name/account')
 citations(r.get('citations'),r['id'])
 for a in r.get('accounts',[]):check(a['sourceId']in sources,f'{r["id"]}: unknown account source')
 for m in r.get('milestones',[]):
  citations(m.get('citations'),f'{r["id"]}/{m["id"]}');start=date(m['date'],m['id'])
  if m.get('endDate'):check(date(m['endDate'],m['id'])>=start,f'{m["id"]}: reversed interval')
for e in data.get('events',[]):
 start=date(e['date'],e['id'])
 if e.get('endDate'):check(date(e['endDate'],e['id'])>=start,f'{e["id"]}: reversed interval')
 check(e.get('precision')in ['day','month','year','decade','approximate'],f'{e["id"]}: missing/unknown precision')
 for id in e.get('people',[]):check(id in people,f'{e["id"]}: invalid person {id}')
 for id in e.get('organizations',[]):check(id in orgs,f'{e["id"]}: invalid organization {id}')
 for id in e.get('lanes',[]):check(id in lanes,f'{e["id"]}: invalid lane {id}')
 check(bool(e.get('sourceSummaries')),f'{e["id"]}: missing source narrative')
 for account in e['sourceSummaries']:
  check(account['sourceId']in [c['sourceId']for c in e['citations']],f'{e["id"]}: uncited narrative')
  check(bool(account.get('summary'))and len(account.get('details',[]))>=2 and bool(account.get('context')),f'{e["id"]}: incomplete narrative')
for label,endpoints in [('relationships',index),('eventLinks',events)]:
 rows=data.get(label,[]);unique(rows,label)
 for r in rows:
  check(r['fromId']in endpoints and r['toId']in endpoints,f'{r["id"]}: broken endpoints')
  check(bool(r.get('label')),f'{r["id"]}: missing relationship label');citations(r.get('citations'),r['id'])
for o in data.get('organizations',[]):
 for id in o.get('members',[]):check(id in people,f'{o["id"]}: invalid member {id}')
 for id in o.get('founderIds',[]):check(id in index,f'{o["id"]}: invalid founder {id}')
missing=sum(not r.get('description')for r in data.get('relationships',[]))
print(f'Valid: {len(sources)} sources, {len(people)} people, {len(orgs)} organizations, {len(events)} events, {len(data.get("relationships",[]))} relationships.')
if missing:print(f'Review signal: {missing} legacy relationships lack a substantive description. Structure validation does not certify source support or indexing completeness.')
