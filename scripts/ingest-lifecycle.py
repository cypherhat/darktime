"""Add explicit source-cited lifecycle milestones without inferring endpoint dates."""
import json
from pathlib import Path
p=Path('src/data/archive.json');data=json.loads(p.read_text());index={e['id']:e for k in ['people','organizations']for e in data[k]}
def add(entity,id,name,kind,date,precision,description,details,source,pages,endDate=None):
 record=index[entity];milestone=dict(id=id,name=name,kind=kind,date=date,precision=precision,description=description,details=details,citations=[dict(sourceId=source,pages=pages)])
 if endDate:milestone['endDate']=endDate
 record['milestones']=[m for m in record.get('milestones',[])if m['id']!=id]+[milestone]
 citation=next((c for c in record['citations']if c['sourceId']==source),None)
 if citation:citation['pages']=sorted(set(citation['pages']+pages))
 else:
  record['citations'].append(dict(sourceId=source,pages=pages))
  record.setdefault('accounts',[]).append(dict(sourceId=source,description=details[0],role='Cited biographical dates'))
  record['history'].append(dict(date='2026-10-14',note='Added explicitly cited lifecycle dates from the supplied PDF.'))
for row in json.loads(Path('scripts/data/lifecycle-tragedy.json').read_text()):
 for kind in ['birth','death']:
  year=row[kind][:4];name=index[row['entityId']]['name']
  add(row['entityId'],f'tragedy-{kind}',kind.title(),kind,row[kind],row['precision'],f'The supplied PDF gives {year} as {name}’s {kind} year.',[row['description'],f'This is an explicit biographical endpoint, rather than the first or last event mentioning {name}. The source gives only a year, so the timeline does not assert a day or month.'],row['sourceId'],row['pages'])
# Career intervals explicitly supplied in a biographical footnote, PDF file page121.
for id,name,date,end,description in [
 ('bar','Barrister','1897-01-01',None,'Quigley says Eggleston was a barrister from1897.'),
 ('round-table','Round Table correspondent and Australian agent','1911-01-01',None,'Quigley describes Eggleston as a member, correspondent and chief Australian agent of The Round Table from1911.'),
 ('assembly','Legislative service','1920-01-01','1927-12-31','The biographical footnote gives Eggleston’s legislative service as1920–1927. This interval is an office tenure, not his lifespan.'),
 ('railways','Minister for Railways','1924-01-01','1926-12-31','Quigley gives Eggleston’s railway ministry as1924–1926.'),
 ('grants','Commonwealth Grants Commission chair','1934-01-01','1941-12-31','Quigley dates Eggleston’s chairmanship of the Commonwealth Grants Commission to1934–1941.'),
 ('china','Australian minister to China','1941-01-01','1944-12-31','Quigley’s biographical account dates Eggleston’s diplomatic service in China to1941–1944.'),
 ('washington','Australian minister in Washington','1944-01-01','1946-12-31','Quigley dates Eggleston’s diplomatic service in the United States to1944–1946; the later wartime chapter repeats this posting.')]:
 add('fw-eggleston',f'anglo-{id}',name,'career',date,'year',description,[description,'The cited biographical footnote connects legal, legislative and diplomatic work with Eggleston’s international-institute roles. An interval is shown where the source supplies both years; it is not treated as a birth or death date.'],'anglo',[121]+([307]if id=='washington'else[]),end)
add('ipr','anglo-branches','British national branches merge with international-affairs institutes','transformation','1939-01-01','year','Quigley says that by1939 the IPR branches in the United Kingdom and three British dominions had merged with their local institutes of international affairs.', ['The cited passage distinguishes local branch mergers from the continuing international IPR association. It says that the two kinds of institutes already had closely overlapping officers before the mergers.','The American IPR did not merge with the Council on Foreign Relations. This milestone is therefore a partial institutional transformation, not a universal merger or dissolution of the IPR.'],'anglo',[193])
add('ipr','tragedy-inquiry','Senate inquiry scrutinizes IPR','career','1951-01-01','year','Quigley describes the McCarran subcommittee’s1951 inquiry seeking to connect American policy toward China with the Institute of Pacific Relations.', ['The passage identifies the Senate Judiciary Committee’s Internal Security subcommittee and describes its allegation of coordinated policy influence. Quigley also discusses the institute’s national councils and foundation and corporate funding.','A later body passage distinguishes documented political influence from proof of an explicit conspiracy; a bracketed editorial insertion disputes that distinction and is excluded from this account. The1951 date marks scrutiny of the organization, not a dissolution or change of legal identity.'],'tragedy',[783,785])
p.write_text(json.dumps(data,indent=2)+'\n');print('Lifecycle milestones:',sum(len(e.get('milestones',[]))for e in index.values()))
