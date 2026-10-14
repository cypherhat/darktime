"""Generate review candidates from every PDF page, independently of existing citations.
Matches are leads only: this program never creates a relationship.
"""
import argparse,json,re,unicodedata
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--archive',type=Path,required=True)
parser.add_argument('--pages-dir',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
parser.add_argument('--aliases',type=Path)
args=parser.parse_args()
archive=json.loads(args.archive.read_text())
extra_aliases=json.loads(args.aliases.read_text())if args.aliases else{}
args.output_dir.mkdir(parents=True,exist_ok=True)
records=archive['people']+archive['organizations']
unknown_alias_ids=set(extra_aliases)-{r['id']for r in records}
if unknown_alias_ids:raise SystemExit('Unknown alias IDs: '+', '.join(sorted(unknown_alias_ids)))
def normalize(value):
 value=re.sub(r'\b(?:[A-Za-z]\.\s*){2,}',lambda m:''.join(re.findall(r'[A-Za-z]',m.group()))+' ',value)
 value=unicodedata.normalize('NFKD',value)
 value=''.join(c for c in value if not unicodedata.combining(c))
 return re.sub(r'[^a-z0-9]+',' ',value.lower()).strip()
# Surname matches may point to relatives or another person: flag them for review.

for source in archive['sources']:
 sid=source['id']; raw=json.loads((args.pages_dir/f'{sid}-pages.json').read_text())
 if len(raw)!=source['pageCount']:raise SystemExit(f'{sid}: page array length does not match registered pageCount')
 pages=[' '+normalize(p)+' 'for p in raw]
 results=[]
 for r in records:
  variants=[r['name']]+r.get('aliases',[])+extra_aliases.get(r['id'],[])
  generated=[];acronyms=[]
  if r['kind']=='organization':
   variants += [r['name'].split(' · ')[0].split(' — ')[0]]
   variants += re.split(r' / | /|/ ',r['name'].split(' · ')[0])
   base=re.split(r'\s+[·—]|\(',r['name'])[0].strip()
   generated += [base]
   words=re.findall(r'[A-Za-z]+',base)
   acronym=''.join(w[0] for w in words if w.lower()not in {'the','of','for','and','in','a','an','at','to'})
   if 3<=len(acronym)<=6 and acronym.upper()not in {'THE','AND','FOR','ALL','NOT','NOW'}:acronyms.append(acronym.upper())
  else:
   words=r['name'].split(',')[0].split()
   if len(words)>2:generated.append(words[0]+' '+words[-1])
  accepted_terms=set(normalize(v) for v in variants if len(normalize(v))>=2)
  generated_terms=set(normalize(v) for v in generated if len(normalize(v))>=2)-accepted_terms
  terms=set(normalize(v) for v in variants if len(normalize(v))>=2)
  uncertain=[]
  if r['kind']=='person':
   name=r['name'].split(',')[0];surname=normalize(name.split()[-1])
   if ' of ' in name and name.split()[0] not in ['King','Lord','Sir']: surname=normalize(name.split()[0])
   if len(surname)>3 and surname not in {'company','trust','college','university','group','sr','jr'}:uncertain=[surname]
  matches=[]; weak=[];generated_matches=[]
  for i,page in enumerate(pages):
   hit=[t for t in terms if ' '+t+' 'in page]
   ambiguous=[t for t in uncertain if ' '+t+' 'in page]
   generated_hit=[t for t in generated_terms if ' '+t+' 'in page]
   generated_hit += [t for t in acronyms if re.search(r'\b'+r'\.?\s*'.join(t)+r'\.?\b',raw[i])]
   if hit or generated_hit:matches.append(i+1)
   if generated_hit:generated_matches.append(i+1)
   if ambiguous and not hit:weak.append(i+1)
  cited={p for c in r.get('citations',[])if c['sourceId']==sid for p in c['pages']}
  edges=[e for e in archive.get('relationships',[])if r['id']in [e['fromId'],e['toId']] and any(c['sourceId']==sid for c in e['citations'])]
  results.append(dict(id=r['id'],name=r['name'],kind=r['kind'],terms=sorted(terms),generatedCandidateTerms=sorted(generated_terms)+acronyms,generatedVariantPages=generated_matches,ambiguousSurnameTerms=uncertain,matchedPages=matches,ambiguousSurnamePages=weak,uncitedPages=sorted(set(matches)-cited),uncitedSurnamePages=sorted(set(weak)-cited),knownPages=sorted(cited),accounts=[a for a in r.get('accounts',[])if a['sourceId']==sid],existingRelations=edges))
 out=dict(sourceId=sid,pageCount=len(pages),method='All-page normalized literal name/alias scan with generated short-form and acronym leads; generated forms and ambiguous surnames require identity resolution. Every proposed link requires body-text review. No proximity inference.',records=results)
 (args.output_dir/f'source-wide-{sid}.json').write_text(json.dumps(out,indent=2)+'\n')
 print(sid,len(results),'identities;',sum(bool(r['uncitedPages']or r['uncitedSurnamePages'])for r in results),'with uncited candidate passages')
