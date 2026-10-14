"""Merge the page-cited Tragedy and Hope research into the canonical archive.

The supplied annotated PDF is the source. Editorial insertions are excluded from
Quigley's accounts; every research record keeps its 1-based PDF page citations.
Existing IDs are resolved by exact identity or an explicit mapping, never surname.
"""
import hashlib,json,re,unicodedata
from pathlib import Path
SOURCE='tragedy';TODAY='2026-10-14';PDF=Path('docs/TragedyAndHope.pdf')
path=Path('src/data/archive.json');data=json.loads(path.read_text())
parts=[json.loads(Path(f'scripts/data/tragedy-{name}.json').read_text()) for name in ['foundations','interwar','war','postwar']]
text=Path('tmp/pdfs/tragedy-pages.json')
if text.exists(): pages=json.loads(text.read_text())
else:
 import subprocess
 raw=subprocess.check_output(['pdftotext','-layout',str(PDF),'-']).decode();pages=raw.split('\f');pages=pages[:-1] if not pages[-1].strip() else pages
chapters=[]
for i,page in enumerate(pages):
 if i<13:continue
 match=re.search(r'(?m)^Chapter (\d+)[—–-]([^\n]+)',page)
 if match:chapters.append(dict(title=page[match.start():].split("\n\n",1)[0].replace("\n", " ").strip(),pdfStart=i+1))
for i,chapter in enumerate(chapters):chapter['pdfEnd']=chapters[i+1]['pdfStart']-1 if i+1<len(chapters) else len(pages)
source=dict(id=SOURCE,title='Tragedy and Hope: A History of the World in Our Time',shortTitle='Tragedy and Hope',author='Carroll Quigley',published='1966',url='',localPath=str(PDF),accessed=TODAY,pageCount=len(pages),sha256=hashlib.sha256(PDF.read_bytes()).hexdigest(),description='A wide-ranging historical synthesis of financial capitalism, imperial administration, international diplomacy, world wars and the Cold War. This supplied PDF is a retyped, annotated edition rather than a facsimile of the 1966 printing. Accounts distinguish Quigley’s interpretations from the later introduction and visible editorial insertions.',pageConvention='All citations use 1-based pages of this 1,090-page PDF. These are not page numbers in the original Macmillan printing. January 1 and the first of a month are plotting anchors for dates whose day is not given.',coverage='Selective, substantive extraction across the book’s institutional and political chapters, with emphasis on finance, empire and connections through the 1950s; selected 1960s developments extend the chronology. This is not an exhaustive index of every name, battle or theoretical passage. '+ ' '.join(part['coverage'] for part in parts),chapters=chapters,evidenceIssues=[dict(pages=[5,6,7,8,9,10,11],description='A later introductory essay mentions a 1996 study and advances additional claims. It is not Quigley’s 1966 text and is excluded from Quigley-attributed profiles and events.'),dict(pages=[278,281,451,454,755,756,785,808,813,960,964,980,986],description='The supplied edition contains visible bracketed editorial comments, omissions and editorial-sounding headings. Digests use the body passages, exclude identified editorial insertions and do not attribute the headings’ rhetoric to Quigley.'),dict(pages=[826,938,942],description='Some dates conflict within the supplied text: the Oppenheimer passage and Bay of Pigs references require care. Specific event accounts record their citation and precision notes; contradictory passages are not silently reconciled.')])
existing=next((s for s in data['sources'] if s['id']==SOURCE),None)
if existing:data['sources']=[source if s['id']==SOURCE else s for s in data['sources']]
else:data['sources'].append(source)
for s in data['sources']:
 if s['id']=='anglo':s['shortTitle']='Anglo-American Establishment'
 if s['id']=='scott':s['shortTitle']='Wall Street Overworld'
 if s['id']=='yankee':s['shortTitle']='Yankee and Cowboy War'
lane_defs=[('finance','Finance & central banks','#d3b476'),('empire','Empire & Commonwealth','#99b5cf'),('diplomacy','Treaties & international institutions','#a1bc9b'),('war','World wars & military alliances','#c48b91'),('revolution','Revolution & authoritarian states','#b09dbe'),('security','Cold War & security institutions','#8dbdbb'),('decolonization','Decolonization & regional conflicts','#c4a487'),('domestic','Domestic politics & public institutions','#b7bd83')]
for id,name,color in lane_defs:
 if not any(l['id']==f'tragedy-{id}' for l in data['lanes']):data['lanes'].append(dict(id=f'tragedy-{id}',name=name,color=color,sourceIds=[SOURCE]))
index={e['id']:e for key in ['people','organizations','events'] for e in data[key]}
alias={'brett':'esher','the-times':'times','mohandas-k-gandhi':'mohandas-gandhi','cecil-rhodes':'rhodes','alfred-milner':'milner','nathan-mayer-rothschild':'rothschild','j-p-morgan-company':'jp-morgan'}
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
def canon(id):
 while id in alias and alias[id]!=id:id=alias[id]
 return id
def citation(pages):
 assert pages and all(isinstance(p,int) and 1<=p<=len(globals()['pages']) for p in pages),pages
 return dict(sourceId=SOURCE,pages=sorted(set(pages)))
def upsert(key,item):
 if item['id'] not in index:data[key].append(item);index[item['id']]=item;return
 old=index[item['id']];assert old['kind']==item['kind'],item['id']
 cs=next((c for c in old['citations'] if c['sourceId']==SOURCE),None)
 if cs:cs['pages']=sorted(set(cs['pages']+item['pages']))
 else:old['citations']+=item['citations'];old['history'].append(dict(date=TODAY,note='Added a separately attributed account from Tragedy and Hope.'))
 account=next((a for a in old.get('accounts',[]) if a['sourceId']==SOURCE),None)
 if account:
  if item['description'] not in account['description']:account['description']+=' '+item['description']
 else:old.setdefault('accounts',[]).extend(item['accounts'])
 old['aliases']=list(dict.fromkeys(old.get('aliases',[])+item.get('aliases',[])+([item['name']] if item['name']!=old['name'] else [])))
 if key=='organizations':
  for field in ['members','founderIds']:old[field]=list(dict.fromkeys(old.get(field,[])+item.get(field,[])))
 if key=='events':
  if old['date']!=item['date']:raise ValueError(f"Event date conflict: {item['id']} {old['date']} / {item['date']}")
  for field in ['lanes','people','organizations']:old[field]=list(dict.fromkeys(old[field]+item[field]))
  old.setdefault('sourceSummaries',[])
  prior=next((a for a in old['sourceSummaries'] if a['sourceId']==SOURCE),None)
  new=item['sourceSummaries'][0]
  if prior:
   prior['details']=list(dict.fromkeys(prior['details']+new['details']))
   if len(new['summary'])>len(prior['summary']):prior['summary']=new['summary']
   if new['context'] not in prior['context']:prior['context']+=' '+new['context']
   if new.get('precisionNote') and new['precisionNote'] not in prior.get('precisionNote',''):prior['precisionNote']=prior.get('precisionNote','')+' '+new['precisionNote']
  else:old['sourceSummaries'].extend(item['sourceSummaries'])
 if old['citations'][0]['sourceId']==SOURCE:
  old['description']=next(a['description'] for a in old['accounts'] if a['sourceId']==SOURCE);old['pages']=old['citations'][0]['pages']
# Resolve all names before processing event and relationship references.
for part in parts:
 for key in ['people','organizations']:
  for row in part[key]:
   id=canon(row['id']);kind='person' if key=='people' else 'organization'
   if id not in index:
    hits=[e for e in index.values() if e['kind']==kind and norm(row['name']) in [norm(e['name'])]+[norm(a) for a in e.get('aliases',[])]]
    if len(hits)==1:alias[row['id']]=hits[0]['id'];id=hits[0]['id']
   role=row.get('role','Institution / network' if kind=='organization' else 'Source participant')
   item=dict(id=id,name=row['name'],kind=kind,role=role,description=row['description'],pages=row['pages'],citations=[citation(row['pages'])],accounts=[dict(sourceId=SOURCE,description=row['description'],role=role)],history=[dict(date=TODAY,note='Initial PDF-page-cited account from Tragedy and Hope.')],aliases=row.get('aliases',[]),evidence=row.get('evidence','Attributed account from supplied PDF'))
   if kind=='organization':item.update(founders=row.get('foundersDescription','Founding roles are shown only where the cited PDF explicitly establishes them.'),founderIds=row.get('founderIds',[]),members=row.get('members',[]))
   upsert(key,item)
for o in data['organizations']:
 for field in ['members','founderIds']:o[field]=list(dict.fromkeys(canon(id) for id in o.get(field,[])))
for part in parts:
 for row in part['events']:
  summary=dict(sourceId=SOURCE,summary=row['summary'],details=row['details'],context=row['context'])
  if row.get('precisionNote'):summary['precisionNote']=row['precisionNote']
  chosen=[f'tragedy-{l.removeprefix("tragedy-")}' for l in row['lanes']]
  item=dict(id=row['id'],name=row['name'],kind='event',role=row['date'],description=row['summary'],date=row['date'],precision=row['precision'],people=list(dict.fromkeys(canon(id) for id in row['people'])),organizations=list(dict.fromkeys(canon(id) for id in row['organizations'])),lanes=chosen,pages=row['pages'],citations=[citation(row['pages'])],sourceSummaries=[summary],accounts=[dict(sourceId=SOURCE,description=row['summary'])],history=[dict(date=TODAY,note='Added from the supplied Tragedy and Hope PDF; source interpretation and date precision retained.')],evidence=row.get('evidence','Event described in source; interpretation attributed to Quigley'),status=row.get('evidence','Source-described event'))
  if row.get('endDate'):item['endDate']=row['endDate']
  upsert('events',item)
 for i,row in enumerate(part['relationships']):
  a,b=canon(row['fromId']),canon(row['toId']);rid=f'tragedy-rel-{a}-{b}-{norm(row["label"])}'
  item=dict(id=rid,fromId=a,toId=b,label=row['label'],description=row.get('description',''),pages=row['pages'],citations=[citation(row['pages'])],evidence=row.get('evidence','Source-attributed relationship'))
  prior=next((r for r in data['relationships'] if r['id']==rid),None)
  if not prior:data['relationships'].append(item)
  else:prior['citations'][0]['pages']=sorted(set(prior['citations'][0]['pages']+row['pages']))
 for row in part.get('eventLinks',[]):
  a,b=canon(row['fromId']),canon(row['toId']);rid=f'tragedy-link-{a}-{b}'
  if not any(l['id']==rid for l in data.get('eventLinks',[])):data.setdefault('eventLinks',[]).append(dict(id=rid,fromId=a,toId=b,label=row['label'],kind=row.get('kind','Source-described influence'),citations=[citation(row['pages'])]))
# Explicitly listed affiliations receive source-cited edges, without interpreting
# an author's broad informal network as an employer or a legal membership roll.
for part in parts:
 for row in part['organizations']:
  for field,label in [('members','Institutional association described in source'),('founderIds','Founding role described in source')]:
   for person in row.get(field,[]):
    a,b=canon(person),canon(row['id'])
    if not any(r['fromId']==a and r['toId']==b and any(c['sourceId']==SOURCE for c in r['citations']) for r in data['relationships']):data['relationships'].append(dict(id=f'tragedy-affiliation-{a}-{b}',fromId=a,toId=b,label=label,pages=row['pages'],citations=[citation(row['pages'])],evidence='Association attributed to cited PDF'))
ids=set(index);problems=[]
for key in ['relationships','eventLinks']:
 for row in data[key]:
  for id in [row['fromId'],row['toId']]:
   if id not in ids:problems.append((key,row['id'],id))
for e in data['events']:
 for id in e['people']+e['organizations']:
  if id not in ids:problems.append(('event',e['id'],id))
for o in data['organizations']:
 for id in o['members']+o['founderIds']:
  if id not in ids:problems.append(('organization',o['id'],id))
if problems:raise ValueError(json.dumps(problems,indent=2))
data['version']=4;data['updated']=TODAY;path.write_text(json.dumps(data,indent=2)+'\n')
print({k:len(data[k]) for k in ['sources','people','organizations','events','relationships','lanes','eventLinks']})
