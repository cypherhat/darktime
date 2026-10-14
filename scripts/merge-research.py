"""Merge source-attributed research artifacts into stable archive identities."""
import json,re,hashlib,calendar
from pathlib import Path
path=Path('src/data/archive.json');data=json.loads(path.read_text());TODAY='2026-10-14'
alias={
 'richard-nixon':'nixon','john-mitchell':'mitchell','john-kennedy':'jfk','john-f-kennedy':'jfk','john-fitzgerald-kennedy':'jfk','robert-maheu':'maheu','robert-a-maheu':'maheu','howard-hughes':'hughes','j-edgar-hoover':'hoover','aristotle-onassis':'onassis','council-foreign-relations':'cfr','central-intelligence-agency':'cia','federal-bureau-of-investigation':'fbi',
 'sullivan-and-cromwell':'sullivan-cromwell','trilateral-commission':'trilateral','committee-to-reelect-president':'creep','committee-to-re-elect-the-president':'creep','e-howard-hunt':'howard-hunt','g-gordon-liddy':'gordon-liddy','james-w-mccord':'james-mccord','james-mccord-jr':'james-mccord','james-w-mccord-jr':'james-mccord','lyndon-b-johnson':'lyndon-johnson','lyndon-baines-johnson':'lyndon-johnson','lyndon-johnson':'lyndon-johnson','allen-w-dulles':'allen-dulles','lee-harvey-oswald':'oswald','jack-ruby':'jack-ruby','e-howard-hunt-jr':'howard-hunt',
 'robert-f-kennedy':'robert-kennedy','robert-francis-kennedy':'robert-kennedy','robert-kennedy':'robert-kennedy','franklin-d-roosevelt':'franklin-roosevelt','robert-bennett':'robert-bennett','james-angleton':'james-angleton','john-foster-dulles':'john-foster-dulles','dwight-eisenhower':'dwight-eisenhower','george-bush':'george-hw-bush','george-h-w-bush':'george-hw-bush',
 'richard-helms':'richard-helms','henry-kissinger':'henry-kissinger','william-colby':'william-colby','carl-oglesby':'carl-oglesby','twa':'twa','trans-world-airlines':'twa','hughes-tool-company':'hughes-tool','hughes-aircraft-company':'hughes-aircraft','democratic-national-committee':'dnc','white-house-plumbers':'white-house-plumbers','mullen-company':'mullen','robert-mullen-company':'mullen','national-transportation-safety-board':'ntsb','federal-aviation-administration':'faa','watergate-break-in':'watergate-break-in','yankee-watergate-breakin':'watergate-break-in','yankee-watergate-burglary':'watergate-break-in',
 'council-on-foreign-relations':'cfr','committee-to-investigate-assassinations':'ctia','security-international-inc':'security-international','peter-dale-scott':'peter-dale-scott','william-h-jackson':'william-h-jackson','standard-oil-new-jersey':'standard-oil-nj','anglo-iranian-oil':'anglo-iranian','anglo-iranian-oil-company':'anglo-iranian','frank-wisner':'frank-wisner'
}
def canon(id):return alias.get(id,id)
def norm(s):return re.sub(r'[^a-z0-9]','',s.lower().replace('’',"'"))
def source_data(id):
 pdf=Path(f'docs/{id}.pdf');common=dict(id=id,url='',localPath=f'docs/{id}.pdf',accessed=TODAY,sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),pageConvention='Citations use 1-based PDF file pages. Printed-page references are provided where discernible. The original PDF remains a local research file.')
 if id=='scott':return dict(**common,title='The State, the Deep State, and the Wall Street Overworld',author='Peter Dale Scott',published='2014',pageCount=27,description='An Asia-Pacific Journal / Japan Focus article examining the interplay of security institutions, financial elites and international covert operations. Causal arguments and quoted interpretations are attributed to Scott or their named authors; the notes include denials and evidentiary qualifications.',coverage='Article and all endnotes reviewed. Selective extraction of dated events, institutions and people; passing names are not exhaustive.',chapters=[dict(title='Article and thematic sections',pdfStart=1,pdfEnd=19),dict(title='Endnotes and source qualifications',pdfStart=19,pdfEnd=27)])
 return dict(**common,title='The Yankee and Cowboy War',author='Carl Oglesby',subtitle='Conspiracies from Dallas to Watergate',published='1977 edition · originally 1976',pageCount=390,description='Oglesby interprets Dallas, Watergate and the Hughes business struggle through competing elite factions. Yankee and Cowboy are his analytical labels, not verified formal organizations. Alternative assassination, covert-operation and sabotage theories remain source-attributed; denials and official accounts are preserved.',coverage='Selected records across the narrative, 1977 preface and appendix, with notes and index used as finding aids. The scan contains OCR errors; names and dates are normalized cautiously. This is an attributed digest, not an exhaustive extraction of every reference.')
def citation(s,pages,note='',printed=None):
 c=dict(sourceId=s,pages=sorted(set(pages)))
 if note:c['note']=note
 if printed:c['printedPages']=printed
 return c
for e in data['people']+data['organizations']+data['events']:
 if not e.get('accounts'):e['accounts']=[dict(sourceId=e['citations'][0]['sourceId'],description=e['description'],role=e['role'])]
index={e['id']:e for key in ['people','organizations','events'] for e in data[key]}
def upsert(key,item,sourceId):
 old=index.get(item['id'])
 if old:
  assert old['kind']==item['kind'],('Identity kind conflict',item['id'])
  account=next((a for a in old.get('accounts',[]) if a['sourceId']==sourceId),None)
  if account is None:
   old.setdefault('accounts',[]).append(dict(sourceId=sourceId,description=item['description'],role=item['role']));old['history'].append(dict(date=TODAY,note=f'Added an attributed account from {sourceId}; earlier descriptions and citations retained.'))
  elif item['description'] not in account['description'] and not any(s['sourceId']==sourceId for s in old.get('sourceSummaries',[])):
   account['description']+=' '+item['description']
   old['history'].append(dict(date=TODAY,note=f'Extended the {sourceId} account with an additional cited role.'))
  for c in item['citations']:
   if c not in old['citations']:old['citations'].append(c)
  for field in ['aliases','members','founderIds','people','organizations','lanes']:
   if field in item:old[field]=list(dict.fromkeys(old.get(field,[])+item[field]))
 else:data[key].append(item);index[item['id']]=item

def normalizeDate(date,end=False):
 if len(date)==4:return date+('-12-31' if end else '-01-01')
 if len(date)==7:return date+f'-{calendar.monthrange(int(date[:4]),int(date[5:7]))[1]:02d}' if end else date+'-01'
 return date
for sourceId,files in [('scott',['scripts/data/scott-research.json']),('yankee',['scripts/data/yankee-first-research.json','scripts/data/yankee-second-research.json'])]:
 if not all(Path(f).exists() for f in files):print('Awaiting research',sourceId);continue
 artifacts=[json.loads(Path(f).read_text()) for f in files];source=source_data(sourceId)
 if sourceId=='scott':
  source['evidenceIssues']=artifacts[0].get('evidenceIssues',[]);source['description']+=' The PDF header gives March 3, the recommended citation March 10, and the revision March 13, 2014.'
 if not any(s['id']==sourceId for s in data['sources']):data['sources'].append(source)
 else:data['sources']=[source if s['id']==sourceId else s for s in data['sources']]
 if sourceId=='yankee':source['chapters']=artifacts[0].get('chapters',[])[:-1]+[dict(title='The Hughes Connection',pdfStart=189,pdfEnd=242),dict(title='The Watergate Plane Crash',pdfStart=243,pdfEnd=283),dict(title='McCord, Double Agent',pdfStart=284,pdfEnd=332),dict(title='Who Killed JFK?',pdfStart=335,pdfEnd=340),dict(title='Official crash account appendix',pdfStart=341,pdfEnd=351),dict(title='Notes and index',pdfStart=353,pdfEnd=390)]
 if sourceId=='scott':lanes=[('scott-finance','Wall Street & finance','#d3b476'),('scott-security','Security institutions','#99b5cf'),('scott-oil','Oil & foreign policy','#a1bc9b'),('scott-covert','Covert funding & operations','#c48b91'),('scott-transnational','Transnational networks','#b09dbe')]
 else:lanes=[('yankee-factions','Oglesby’s faction analysis','#c9aa76'),('yankee-dallas','Dallas & assassination debates','#9fabc8'),('yankee-cuba','Cuba & intelligence','#a9bfa8'),('yankee-hughes','Hughes business struggle','#cd9390'),('yankee-watergate','Watergate & investigations','#b3a0bf'),('yankee-flight','Flight 553: competing accounts','#8dbdbb'),('yankee-after','Post-Watergate & Carter','#d3b476')]
 for id,name,color in lanes:
  if not any(l['id']==id for l in data['lanes']):data['lanes'].append(dict(id=id,name=name,color=color,sourceIds=[sourceId]))
 # Match exact names or aliases only, after explicit mappings. Ambiguous names remain distinct.
 for artifact in artifacts:
  for key in ['people','organizations']:
   for row in artifact[key]:
    id=canon(row['id']);kind='person' if key=='people' else 'organization'
    if id not in index:
     hits=[e for e in index.values() if e['kind']==kind and norm(row['name']) in [norm(e['name'])]+[norm(a) for a in e.get('aliases',[])]]
     if len(hits)==1:alias[row['id']]=hits[0]['id'];id=hits[0]['id']
    role=row.get('role') or ('Institution / network' if kind=='organization' else 'Public figure / source participant')
    item=dict(id=id,name=row['name'],kind=kind,role=role,description=row['description'],pages=row['pages'],citations=[citation(sourceId,row['pages'],printed=row.get('printedPages'))],history=[dict(date=TODAY,note=f'Initial page-cited account from {sourceId}.')],accounts=[dict(sourceId=sourceId,description=row['description'],role=role)],evidence=row.get('evidence','Attributed source account'),aliases=row.get('aliases',[]))
    if kind=='organization':item.update(founders=row.get('founderDescription','Founding roles are recorded only where established in the cited account; otherwise unresolved.'),founderIds=[canon(x) for x in row.get('founders',[])],members=[canon(x) for x in row.get('members',[])])
    upsert(key,item,sourceId)
 # Canonicalize references after all supplied entities have resolved.
 for artifact in artifacts:
  for row in artifact['organizations']:
   item=index[canon(row['id'])];item['members']=list(dict.fromkeys(canon(x) for x in item.get('members',[])));item['founderIds']=list(dict.fromkeys(canon(x) for x in item.get('founderIds',[])))
  for row in artifact['events']:
   id=canon(row['id']);description=row['description'];os=[canon(x) for x in row['organizations']];ps=[canon(x) for x in row['people']];text=(row['title']+' '+description).lower()
   if sourceId=='scott':
    chosen=[]
    if any(x in os for x in ['federal-reserve','sullivan-cromwell','cfr','bcci','castle-bank','riggs-bank','booz-allen','carlyle']):chosen.append('scott-finance')
    if any(x in os for x in ['cia','fbi','nsa','opc','oss']):chosen.append('scott-security')
    if any(x in os for x in ['seven-sisters','anglo-iranian','aramco','stanvac','permina'])or any(x in text for x in ['oil','iran','mossadeq']):chosen.append('scott-oil')
    if any(x in text for x in ['covert','fund','coup','lockheed','payoff']):chosen.append('scott-covert')
    if any(x in os for x in ['safari-alliance','safari-resort','bilderberg','acue','bcci'])or any(x in text for x in ['iran-contra','safari','transnational','israel']):chosen.append('scott-transnational')
    if not chosen:chosen=['scott-security']
   else:
    chosen=[]
    if any(x in text for x in ['dallas','dealey','jfk','kennedy assassination','warren','oswald','ruby']):chosen.append('yankee-dallas')
    if any(x in text for x in ['cuba','bay of pigs','castro','mangoo','jmwav','cia']):chosen.append('yankee-cuba')
    if any(x in text for x in ['hughes','twa','maheu','greenspun','toolco','summa']):chosen.append('yankee-hughes')
    if any(x in text for x in ['watergate','mccord','plumber','hush','nixon','burglary','sirica','mitchell']):chosen.append('yankee-watergate')
    if any(x in text for x in ['553','crash','ntsb','aviation','skolnick']):chosen.append('yankee-flight')
    if any(x in text for x in ['carter','trilateral','1977','rockefeller','ford becomes']):chosen.append('yankee-after')
    if len(chosen)==0 or row.get('evidence')=='author-interpretation':chosen.append('yankee-factions')
    if 'yankee-dallas' in chosen and 'nixon' in ps:chosen.append('yankee-factions')
   date=normalizeDate(row['date']);item=dict(id=id,name=row['title'],kind='event',role=date,description=description,date=date,precision=row['precision'],people=ps,organizations=os,lanes=list(dict.fromkeys(chosen)),pages=row['pages'],citations=[citation(sourceId,row['pages'],printed=row.get('printedPages'))],history=[dict(date=TODAY,note=f'Added from {sourceId}; interpretation and date precision remain attributed.')],accounts=[dict(sourceId=sourceId,description=description)],status=row.get('evidence','Source-described event'),evidence=row.get('evidence','Source-described event'))
   if row.get('endDate'):item['endDate']=normalizeDate(row['endDate'],True)
   upsert('events',item,sourceId)
  for i,row in enumerate(artifact['relationships']):
   a,b=canon(row['source']),canon(row['target']);rid=sourceId+'-rel-'+a+'-'+b+'-'+re.sub('[^a-z0-9]+','-',row['label'].lower()).strip('-');item=dict(id=rid,fromId=a,toId=b,label=row['label'],description=row.get('description',''),pages=row['pages'],citations=[citation(sourceId,row['pages'],printed=row.get('printedPages'))],evidence=row.get('evidence','Attributed source relationship'))
   found=next((r for r in data['relationships'] if r['id']==rid),None)
   if not found:data['relationships'].append(item)
   elif item['citations'][0] not in found['citations']:found['citations'].extend(item['citations'])
 # Founders/members become explicit, source-cited affiliation edges if not already represented.
 for artifact in artifacts:
  for row in artifact['organizations']:
   orgId=canon(row['id'])
   for field,label in [('members','Institutional association in cited account'),('founders','Founding role in cited account')]:
    for target in row.get(field,[]):
     a=canon(target)
     if any(r['fromId']==a and r['toId']==orgId and any(c['sourceId']==sourceId for c in r['citations']) for r in data['relationships']):continue
     data['relationships'].append(dict(id=sourceId+'-affiliation-'+a+'-'+orgId,fromId=a,toId=orgId,label=label,pages=row['pages'],citations=[citation(sourceId,row['pages'])],evidence='Attributed institutional association'))
data['version']=3;data['updated']=TODAY
ids={e['id'] for key in ['people','organizations','events'] for e in data[key]};problems=[]
for r in data['relationships']:
 for id in [r['fromId'],r['toId']]:
  if id not in ids:problems.append(('relationship',r['id'],id))
for e in data['events']:
 for id in e['people']+e['organizations']:
  if id not in ids:problems.append(('event',e['id'],id))
for o in data['organizations']:
 for id in o.get('members',[])+o.get('founderIds',[]):
  if id not in ids:problems.append(('organization',o['id'],id))
if problems:
 print('Unresolved references:',json.dumps(problems,indent=2));raise SystemExit(1)
path.write_text(json.dumps(data,indent=2)+'\n');print({k:len(data[k])for k in ['people','organizations','events','relationships','lanes']})
