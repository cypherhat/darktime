"""Merge a page-cited reading of Quigley into the archive. Existing descriptions survive."""
import json, re, hashlib
from pathlib import Path
path=Path('src/data/archive.json'); data=json.loads(path.read_text()); SOURCE='anglo'; TODAY='2026-10-14'
def cite(pages,note=''):
 return [dict(sourceId=SOURCE,pages=sorted(set(pages)),note=note)]
def base(id,name,kind,role,description,pages,**extra):
 return dict(id=id,name=name,kind=kind,role=role,description=description,pages=pages,citations=cite(pages),history=[dict(date=TODAY,note='Added from Quigley with PDF-page citations; membership and causal interpretations remain attributed to the author.')],**extra)
source=dict(id=SOURCE,title='The Anglo-American Establishment',author='Carroll Quigley',subtitle='From Rhodes to Cliveden',url='',localPath='docs/anglo.pdf',accessed=TODAY,published='1981',written='1949',pageCount=342,pageConvention='Citations use 1-based PDF pages, not the printed book pagination. The digital edition warns that its page breaks do not exactly match the original.',sha256=hashlib.sha256(Path('docs/anglo.pdf').read_bytes()).hexdigest(),description='A historical study written in 1949 and published in 1981. Quigley traces elite networks through education, publishing, imperial governance and foreign policy. His appendix labels the membership roster tentative, with possible errors and explicitly bracketed conjectures. The archive distinguishes reported roles from his inferred affiliations. The PDF remains a local research document and is not redistributed by this site.',coverage='All 13 chapters represented by selected records; the tentative appendix roster is indexed. Not every name, date, footnote, or passing reference has been extracted.')
if not any(s['id']==SOURCE for s in data['sources']):data['sources'].append(source)
else:data['sources']=[source if s['id']==SOURCE else s for s in data['sources']]
people=[]; orgs=[]; events=[]; rels=[]
def person(id,name,role,desc,pages,aliases=[],evidence='Reported role',**extra):
 people.append(base(id,name,'person',role,desc,pages,aliases=aliases,evidence=evidence,**extra));return id
def org(id,name,purpose,pages,founders='Not established in the cited passages.',founderIds=[],members=[],evidence='Reported institution',**extra):
 orgs.append(base(id,name,'organization','Institution / network',purpose,pages,founders=founders,founderIds=founderIds,members=members,evidence=evidence,**extra));return id
def relation(a,b,label,pages,evidence='Reported role',date=None,endDate=None):
 id='anglo-rel-'+a+'-'+b+'-'+re.sub('[^a-z0-9]+','-',label.lower()).strip('-')
 item=dict(id=id,fromId=a,toId=b,label=label,pages=pages,citations=cite(pages),evidence=evidence)
 if date:item['date']=date
 if endDate:item['endDate']=endDate
 rels.append(item)
def event(id,date,name,desc,pages,lanes,people=[],organizations=[],precision='year',endDate=None,evidence='Source-described event'):
 item=base('anglo-'+id,name,'event',date,'Quigley '+desc,pages,date=date,precision=precision,lanes=lanes,people=people,organizations=organizations,status=evidence,evidence=evidence)
 if endDate:item['endDate']=endDate
 events.append(item)
# Distinct people retain distinct identities even where surnames, titles or initials overlap.
core=[
('quigley','Carroll Quigley','Historian · author','Author of this study. His preface dates the manuscript to 1949 and distinguishes an inner core from an outer circle; he acknowledges possible errors in assigning membership.',[2,5,6,7],[]),
('rhodes','Cecil John Rhodes','Businessman · imperial advocate','Quigley places Rhodes at the origin of the proposed Society of the Elect and describes his wills, wealth and scholarships as instruments for imperial unity.',[8,36,37,42],['Cecil Rhodes']),
('milner','Alfred Milner','Administrator · Viscount Milner','The organizing figure in Quigley’s account: Oxford friendships, South African administration, the Kindergarten and wartime government link successive phases of the network.',[12,18,54,87,146],['Lord Milner','Viscount Milner']),
('stead','William T. Stead','Journalist · editor','Editor of the Pall Mall Gazette and founder of the Review of Reviews. Quigley describes his role in the 1891 discussions and his later estrangement over the Boer War.',[16,40,42,44],['W. T. Stead']),
('esher','Reginald Baliol Brett','Royal adviser · Viscount Esher','Quigley describes a co-organizer of the 1891 society, a behind-the-scenes royal adviser and a mentor to Maurice Hankey.',[8,44,45,158],['Lord Esher','Reginald Brett']),
('salisbury','Robert Gascoyne-Cecil','Prime minister · 3rd Marquess of Salisbury','Quigley identifies him as the builder of the Cecil Bloc, using family connections, public appointments, Oxford and journalism. Do not confuse him with his descendants bearing the same title.',[19,20,21],['Lord Salisbury','Robert Arthur Talbot Gascoyne-Cecil']),
('balfour','Arthur James Balfour','Prime minister · foreign secretary','Salisbury’s nephew and successor. Quigley connects him to the Cecil Bloc, Rhodes’s circle and wartime foreign policy.',[19,21,44,147],['Arthur Balfour','A. J. Balfour']),
('goschen','George Joachim Goschen','Chancellor · 1st Viscount Goschen','Milner’s employer and political patron. Quigley credits his introductions and influence with linking Milner to Salisbury’s circle.',[16,18],['Lord Goschen']),
('arnold-toynbee','Arnold Toynbee','Social reformer · Milner’s contemporary','Milner’s close Balliol friend, whose ideals Quigley treats as formative. He died in 1883. Distinct from his nephew, the historian Arnold J. Toynbee.',[12,14,15],[]),
('arnold-j-toynbee','Arnold J. Toynbee','Historian · international-affairs researcher','Nephew of Arnold Toynbee. Quigley describes his work at the Royal Institute of International Affairs and later wartime research; these are different individuals.',[12,165,303,305],['A. J. Toynbee']),
('george-parkin','George Robert Parkin','Educator · Rhodes Trust secretary','Imperial-federation lecturer and first Rhodes Trust secretary. Quigley follows his correspondence with Milner and connections in Canada.',[12,13,90],['Sir George Parkin','George R. Parkin']),
('gell','Philip Lyttelton Gell','Publisher · company director','A longtime friend of Milner, first chairman of Toynbee Hall and later director of the British South Africa Company in Quigley’s account.',[13,304],['Lyttelton Gell']),
('brassey','Thomas Brassey','Imperial-federation supporter · Lord Brassey','Quigley describes financial support for Parkin’s work and cooperation with Milner’s circle.',[12,46],['Lord Brassey']),
('albert-grey','Albert Grey','4th Earl Grey · administrator','Introduced to Rhodes by Stead; a British South Africa Company director, Rhodes trustee and later Governor-General of Canada in the book.',[15,16,50],['Earl Grey']),
('edward-grey','Edward Grey','Foreign secretary · Viscount Grey of Fallodon','Named among the Liberal imperialists close to the Cecil Bloc. Quigley’s later foreign-policy analysis distinguishes him from Albert Grey.',[33,101],['Grey of Fallodon']),
('rosebery','Archibald Primrose','Prime minister · Earl of Rosebery','Quigley describes support for Parkin, friendship with Rhodes and trusteeship, while qualifying the extent of his active membership.',[12,49],['Lord Rosebery']),
('rothschild','Nathan Mayer Rothschild','Financier · Baron Rothschild','Trustee named in Rhodes’s wills. Quigley says Rhodes envisaged his handling the financial side but describes his limited enthusiasm for the society plan.',[37,42,49],['Natty Rothschild','Lord Rothschild']),
('beit','Alfred Beit','Businessman · philanthropist','Rhodes’s business associate and trustee, whose bequests funded African transport and Oxford colonial-history posts. Quigley ties these resources to Milner’s network.',[50,90,91],[]),
('bailey','Abe Bailey','Businessman · financier','Quigley describes funding for South African union advocacy, The Round Table and the international-affairs institute, including a 1928 endowment.',[49,77,78],['Sir Abe Bailey']),
('jameson','Leander Starr Jameson','Administrator · Cape premier','Rhodes’s doctor and close associate, leader of the 1895 raid and later Cape premier. Quigley records his cooperation with the Kindergarten.',[50,77],['Dr. Jameson','Starr Jameson']),
('smuts','Jan Christiaan Smuts','South African statesman','Quigley follows his work in South African union, the Imperial War Cabinet, the peace settlement and Irish negotiations; his motives and network membership are the author’s interpretation.',[79,80,81,146,182],['Jan C. Smuts','Jan Smuts']),
('selborne','William Waldegrave Palmer','2nd Earl of Selborne · High Commissioner','Milner’s successor in South Africa. Quigley describes his cooperation with the Kindergarten and the January 1907 dispatch advocating closer union.',[54,77,78],['Lord Selborne']),
('duncan','Patrick Duncan','Administrator · Governor-General','Milner’s former assistant and Transvaal official. Quigley describes him as a leading Kindergarten member who remained in South Africa and worked with Smuts.',[55,56,57],['Sir Patrick Duncan']),
('brand','Robert Henry Brand','Banker · Baron Brand','The Round Table circle’s economic specialist, a Lazard Brothers partner and later wartime financial official. Quigley describes his marriage to Nancy Astor’s sister.',[62,63,119],['R. H. Brand','Lord Brand']),
('kerr','Philip Kerr','Editor · Marquess of Lothian','Quigley traces him from The State and The Round Table to Lloyd George’s secretariat, the Rhodes Trust and the Washington embassy.',[63,64,119,146],['Lord Lothian','Philip Henry Kerr']),
('curtis','Lionel Curtis','Organizer · imperial-federation advocate','A central organizer linking Closer Union Societies, Round Table groups, Indian constitutional reform and the international-affairs institute in Quigley’s analysis.',[66,67,68,69,77,119],[]),
('dawson','Geoffrey Dawson','Journalist · editor of The Times','Called Geoffrey Robinson until 1917. Quigley traces South African journalism, two terms editing The Times and involvement in Indian reform and appeasement.',[55,64,65,104,105],['Geoffrey Robinson']),
('amery','Leopold Amery','Journalist · cabinet minister','Quigley traces his Times work, wartime secretarial posts, colonial policy and later leadership of the India Office.',[56,69,70,148,163],['L. S. Amery','Leo Amery']),
('grigg','Edward Grigg','Journalist · Baron Altrincham','Times staff member, Round Table editor, Lloyd George secretary and colonial official in Quigley’s account.',[56,70,71,104],['Lord Altrincham']),
('fisher','Herbert Albert Laurens Fisher','Historian · education minister','New College fellow and later warden; Quigley describes him as a bridge between Oxford recruitment and public office, distinct from All Souls membership.',[56,71,72,73,74],['H. A. L. Fisher']),
('halifax','Edward Frederick Lindley Wood','Viceroy · foreign secretary · Earl of Halifax','Also known as Lord Irwin. Quigley connects his All Souls fellowship to Indian policy, appeasement and the wartime embassy in Washington.',[74,75],['Edward Wood','Lord Irwin','Lord Halifax']),
('waldorf-astor','Waldorf Astor','Politician · Viscount Astor','Quigley describes his ownership role at The Times, Cliveden gatherings and work with the international-affairs institute. Distinct from his brother John Jacob Astor.',[105,106,167],['Lord Astor']),
('nancy-astor','Nancy Astor','Politician · Lady Astor','Named in the tentative inner circle and in Quigley’s discussion of Cliveden. Her sister’s marriage to Brand provides a specifically reported family connection.',[63,308,309],['Lady Astor']),
('john-jacob-astor','John Jacob Astor','Newspaper proprietor','Waldorf Astor’s brother, named as a director after the 1922 Times purchase. He is distinct from Waldorf.',[106],['Colonel Astor']),
('hichens','William Lionel Hichens','Administrator · industrialist','Quigley follows his Transvaal treasury and railway work, industrial appointments and educational interests.',[55,58,59],['W. L. Hichens']),
('feetham','Richard Feetham','Lawyer · judge','Johannesburg official, Selborne adviser and later chairman of the Irish Boundary Commission in Quigley’s account.',[55,57],[]),
('dougal-malcolm','Dougal Orme Malcolm','Administrator · company director','Kindergarten official and later British South Africa Company director and president. Distinct from General Neill Malcolm.',[55,57,58],['Sir Dougal Malcolm']),
('dove','John Dove','Administrator · Round Table editor','Quigley describes his South African service, later editorial work and correspondence with Brand on economics and policy.',[69,126,127,151],[]),
('basil-long','Basil Kellett Long','Journalist · South African legislator','Successor to Kerr at The State, later Times department head and Cape Times editor. Quigley distinguishes him from the formally employed Kindergarten officials.',[56,75,104],['B. K. Long']),
('basil-williams','Basil Williams','Historian · Kindergarten associate','Listed among the Kindergarten, author of a Milner biographical entry and contributor to union-related work in Quigley’s account.',[55,62,78],[]),
('meston','James Scorgie Meston','Indian civil servant · Baron Meston','Quigley describes his Transvaal work, Indian finance, advice to the circle and chairmanship of the institute’s executive committee.',[81,82],['Lord Meston']),
('marris','William Marris','Indian civil servant','Brought to the Transvaal from the Indian Civil Service. Quigley credits his discussions with Curtis with broadening the latter’s conception of self-government.',[81,82,119,120],['Sir William Marris']),
('coupland','Reginald Coupland','Historian · Beit professor','Quigley describes his Oxford chair, Round Table editorship and involvement in Palestine and Indian constitutional debates.',[91,94,127,173],['Sir Reginald Coupland']),
('zimmern','Alfred Eckhard Zimmern','Scholar · international-affairs advocate','Oxford teacher and international-politics scholar. Quigley stresses his League work and differences from some colleagues over Germany and appeasement.',[92,93,150,151],['Sir Alfred Zimmern']),
('hankey','Maurice Pascal Alers Hankey','Cabinet secretary · Baron Hankey','Secretary to the defence committee and wartime cabinets, described as Esher’s protege. His placement differs between sections of Quigley’s tentative roster.',[146,157,158,309],['Lord Hankey','Maurice P. A. Hankey']),
('florashaw','Flora Shaw','Journalist · Lady Lugard','Times colonial department head, later married Frederick Lugard. Quigley discusses her communications with Rhodes and her role around the Jameson Raid.',[108,109,110,111,114],['Lady Lugard']),
('lugard','Frederick Lugard','Colonial administrator · Baron Lugard','Quigley names him on the Permanent Mandates Commission and identifies Flora Shaw as his wife.',[108,172],['Lord Lugard']),
('george-buckle','George Earle Buckle','Editor of The Times','Quigley identifies his editorial tenure and All Souls fellowship as part of the institutional overlap he studies.',[12,104],['George E. Buckle']),
('northcliffe','Alfred Harmsworth','Publisher · Lord Northcliffe','Times owner from 1908; Quigley describes conflicts with Dawson and the ownership transfer after Northcliffe’s death.',[46,104,105,106],['Lord Northcliffe']),
('monypenny','William Flavelle Monypenny','Journalist · biographer','Times assistant editor and Johannesburg Star editor; the book describes wartime civil-supplies work and subsequent return to The Times.',[55,65,104],['W. F. Monypenny']),
('chilrol','Valentine Chirol','Foreign editor · journalist','Times Foreign Department head who later advised on Indian constitutional questions, according to Quigley.',[115,117],['Sir Valentine Chirol']),
('fiddes','George Vandeleur Fiddes','Colonial official','Milner’s secretary and later Permanent Under Secretary for the Colonies, identified in the Kindergarten chapter.',[55,59,148,163],['Sir George Fiddes']),
('walrond','Main Swete Osmond Walrond','Administrator · Egypt adviser','Milner’s private secretary in South Africa and later an adviser to the Egypt mission, according to the book.',[55,66,183],['M. S. O. Walrond']),
('buchan','John Buchan','Writer · Baron Tweedsmuir','Kindergarten associate, publisher and later public official. Quigley quotes his recollections of the group and imperial federation.',[55,59,60,61,84],['Lord Tweedsmuir']),
('holland','Reginald Sothern Holland','Administrator · Rhodes trustee','Secretary to Jameson, trade and munitions official, and later Rhodes trustee in the book.',[50,51,90],['Sir Sothern Holland']),
('arthur-glazebrook','Arthur James Glazebrook','Banker · Canadian organizer','The Canadian Round Table organizer in Quigley’s account. Distinct from Michael Glazebrook and from his son George Parkin de T. Glazebrook.',[14,121,123],['A. J. Glazebrook']),
('george-glazebrook','George Parkin de T. Glazebrook','Historian · Canadian official','Quigley identifies him as Arthur Glazebrook’s son and a later Canadian network figure alongside Vincent Massey.',[13,122,123,303],['G. P. de T. Glazebrook','George Parkin Glazebrook']),
('massey','Vincent Massey','Canadian diplomat','Parkin’s son-in-law, Canadian minister in Washington and High Commissioner in London in Quigley’s account.',[13,122,303],[]),
('corbett','Percy Ellwood Corbett','Legal scholar · Rhodes Scholar','Quigley describes his Balliol studies, All Souls fellowship, League service and wartime work in the United States.',[95,303],['Percy Corbett']),
('beer','George Louis Beer','Historian · American Round Table associate','Quigley describes him as an early non-British Round Table member and a contributor to discussions of colonial mandates.',[171,172],[]),
('anson','William Anson','Warden of All Souls','Quigley describes his work with Fisher in recruiting talented fellows; he expressly says Anson was not necessarily aware of a coordinated Milner group.',[18,27,74],['Sir William Anson']),
('michael-glazebrook','Michael Glazebrook','Educator · cleric','Milner’s Balliol friend and a follower of Toynbee’s religious and social ideas; not the Canadian organizer Arthur Glazebrook.',[13,14],[]),
('raleigh','Thomas Raleigh','Lawyer · Oxford fellow','Milner and Parkin’s friend, an All Souls fellow and an official in the India-related councils described by Quigley.',[13],['Sir Thomas Raleigh']),
('barnett','Samuel Augustus Barnett','Cleric · social reformer','Quigley connects his Whitechapel social work to Milner’s early public service and contacts with Goschen.',[15,16],['Samuel A. Barnett']),
('hugh-wyndham','Hugh Archibald Wyndham','Administrator · historian','Kindergarten member and author of the South African union chapter in the Cambridge imperial history cited by Quigley.',[23,55,76],['Hugh A. Wyndham']),
('edward-cook','Edward Tyas Cook','Journalist · biographer','Quigley describes him as a newspaper colleague, editor of Ruskin’s works and author of Garrett’s biography. His Society of the Elect roster entry is bracketed as conjectural.',[14,16,47,48,307],['Sir Edward Cook']),
('harry-johnston','Harry Hamilton Johnston','Explorer · administrator','Quigley places him among early recipients of Rhodes’s plan, then describes a breach with Rhodes; later roster inclusion is the author’s classification.',[42,43,44],['Sir Harry Johnston']),
('hawksley','Bourchier Francis Hawksley','Lawyer · Rhodes trustee','Rhodes’s lawyer, involved with the wills. Quigley infers initiation from knowledge of the plan and the confidential legal relationship.',[37,46,307],['B. F. Hawksley']),
('garrett','Edmund Garrett','Journalist · Cape Times editor','Quigley describes close relationships with Rhodes and Milner and use as an intermediary, treating these as evidence of membership.',[47,48,307],[]),
('robert-cecil','Robert Cecil','League advocate · Viscount Cecil of Chelwood','Salisbury’s son, involved in blockade and League planning. Quigley says he attended early inner meetings but assigns him to the longer-term outer circle.',[20,147,165,307,309],['Lord Robert Cecil','Lord Cecil of Chelwood']),
('asquith','Herbert Henry Asquith','Prime minister','Quigley describes an Oxford friendship with Milner and a place among Liberal imperialists, without equating every political acquaintance with membership.',[14,33,84,159],['H. H. Asquith']),
('lloyd-george','David Lloyd George','Prime minister','Quigley examines his reliance on Milner’s associates during war and peace, while describing independent electoral decisions and later disagreements.',[145,146,149],['Lloyd George']),
('joseph-chamberlain','Joseph Chamberlain','Colonial secretary','Described as Milner’s ministerial superior in South Africa and an advocate of imperial preference. His governmental cooperation is not itself proof of membership.',[22,54,112],[]),
('curzon','George Nathaniel Curzon','Viceroy · foreign secretary','Salisbury protege and All Souls fellow in Quigley’s account; included in the institutional background rather than assumed identical with the Milner inner circle.',[21,27,147],['Lord Curzon']),
('violet-milner','Violet Milner','Lady Milner · formerly Lady Edward Cecil','Quigley describes her marriage first to Edward Cecil and then to Milner in 1921, connecting family and social networks.',[20,21],['Violet Maxse','Lady Edward Cecil']),
('edward-cecil','Edward Cecil','British official','Salisbury’s son and an Egyptian financial official; Violet Cecil became Milner’s wife after Edward’s death.',[20,21],['Lord Edward Cecil']),
('maguire','James Rochfort Maguire','Company director · Rhodes associate','An All Souls fellow and Rhodes’s longstanding associate, later British South Africa Company director and president in Quigley’s account.',[51],['J. Rochfort Maguire']),
('michell','Lewis Loyd Michell','Banker · Rhodes trustee','Rhodes’s banker, trustee and biographer, identified by Quigley among the older Rhodes associates cooperating with Milner.',[51],['Sir Lewis Michell']),
('egerton','Hugh Edward Egerton','Historian · Beit professor','First holder of the Oxford Beit chair from 1905; Quigley describes a link between Cecil-era patronage, colonial history and Milner’s circle.',[14,91],['H. E. Egerton']),
('jowett','Benjamin Jowett','Master of Balliol','Quigley cites his account of Toynbee’s cooperative study method as part of the circle’s intellectual background.',[15],[]),
('ruskin','John Ruskin','Writer · Oxford professor','Quigley identifies his teaching as an influence on Toynbee and Milner’s social-service outlook. Intellectual influence is distinguished from society membership.',[14,15],[]),
('james-allen','James Allen','New Zealand politician','Quigley names him as an early New Zealand Round Table leader and a later High Commissioner in London.',[120],['Sir James Allen']),
('downie-stewart','William Downie Stewart','New Zealand politician','Named as a later leading New Zealand Round Table figure with ministerial and parliamentary roles.',[120,121],['William Downie-Stewart'])]
for row in core:person(*row)
# Appendix roster. Brackets are stored as uncertainty, not silently converted to membership.
roster_rows='''
rhodes|Cecil John Rhodes|307|Society of the Elect
rothschild|Nathan Rothschild|307|Society of the Elect
harry-johnston|Harry Johnston|307|Society of the Elect
stead|William T. Stead|307|Society of the Elect
esher|Reginald Brett|307|Society of the Elect
milner|Alfred Milner|307|Society of the Elect
hawksley|B. F. Hawksley|307|Society of the Elect
brassey|Thomas Brassey|307|Society of the Elect
garrett|Edmund Garrett|307|Society of the Elect
edward-cook|Edward Cook|307|Society of the Elect|tentative
beit|Alfred Beit|307|Society of the Elect
bailey|Abe Bailey|307|Society of the Elect
albert-grey|Albert Grey|307|Society of the Elect
rosebery|Archibald Primrose|307|Society of the Elect
balfour|Arthur James Balfour|307|Society of the Elect
george-parkin|George R. Parkin|307|Society of the Elect
gell|Philip Lyttelton Gell|308|Society of the Elect
henry-birchenough|Henry Birchenough|308|Society of the Elect
holland|Reginald Sothern Holland|308|Society of the Elect
arthur-smith|Arthur Lionel Smith|308|Society of the Elect
fisher|Herbert A. L. Fisher|308|Society of the Elect
selborne|William Waldegrave Palmer|308|Society of the Elect
alfred-lyttelton|Alfred Lyttelton|308|Society of the Elect|tentative
duncan|Patrick Duncan|308|Society of the Elect
brand|Robert Henry Brand|308|Society of the Elect
kerr|Philip Kerr|308|Society of the Elect
curtis|Lionel Curtis|308|Society of the Elect
dawson|Geoffrey Dawson|308|Society of the Elect
grigg|Edward Grigg|308|Society of the Elect
smuts|Jan C. Smuts|308|Society of the Elect
amery|Leopold Amery|308|Society of the Elect
waldorf-astor|Waldorf Astor|308|Society of the Elect
nancy-astor|Nancy Astor|308|Society of the Elect
duncan|Patrick Duncan|308|Helpers · inner circle
brand|Robert Henry Brand|308|Helpers · inner circle
kerr|Philip Kerr|308|Helpers · inner circle
curtis|Lionel Curtis|308|Helpers · inner circle
hichens|William L. Hichens|308|Helpers · inner circle
dawson|Geoffrey Dawson|308|Helpers · inner circle
grigg|Edward Grigg|308|Helpers · inner circle
fisher|Herbert A. L. Fisher|308|Helpers · inner circle
amery|Leopold Amery|308|Helpers · inner circle
feetham|Richard Feetham|308|Helpers · inner circle
hugh-wyndham|Hugh A. Wyndham|308|Helpers · inner circle
dougal-malcolm|Dougal Malcolm|308|Helpers · inner circle
basil-williams|Basil Williams|308|Helpers · inner circle
basil-long|Basil Kellett Long|308|Helpers · inner circle
bailey|Abe Bailey|308|Helpers · inner circle
smuts|Jan C. Smuts|308|Helpers · inner circle
marris|William Marris|308|Helpers · inner circle
meston|James S. Meston|308|Helpers · inner circle
malcolm-hailey|Malcolm Hailey|309|Helpers · inner circle
florashaw|Flora Shaw|309|Helpers · inner circle
coupland|Reginald Coupland|309|Helpers · inner circle
waldorf-astor|Waldorf Astor|309|Helpers · inner circle
nancy-astor|Nancy Astor|309|Helpers · inner circle
hankey|Maurice Hankey|309|Helpers · inner circle
arnold-j-toynbee|Arnold J. Toynbee|309|Helpers · inner circle
rushbrook-williams|Laurence F. Rushbrook Williams|309|Helpers · inner circle
hv-hodson|Henry Vincent Hodson|309|Helpers · inner circle
harlow|Vincent Todd Harlow|309|Helpers · inner circle
buchan|John Buchan|309|Helpers · outer circle
fabian-ware|Fabian Ware|309|Helpers · outer circle
zimmern|Alfred Zimmern|309|Helpers · outer circle
gilbert-murray|Gilbert Murray|309|Helpers · outer circle
robert-cecil|Robert Cecil|309|Helpers · outer circle
headlam-morley|James Wycliffe Headlam-Morley|309|Helpers · outer circle
chelmsford|Frederick J. N. Thesiger|309|Helpers · outer circle
chilrol|Valentine Chirol|309|Helpers · outer circle
halifax|Edward F. L. Wood|309|Helpers · outer circle
arthur-salter|Arthur Salter|309|Helpers · outer circle
steel-maitland|Arthur Steel-Maitland|309|Helpers · outer circle
ormsby-gore|William G. A. Ormsby-Gore|309|Helpers · outer circle
edith-lyttelton|Edith Lyttelton|309|Helpers · outer circle
lugard|Frederick Lugard|309|Helpers · outer circle
jameson|Leander Starr Jameson|309|Helpers · outer circle
hwc-davis|Henry William Carless Davis|309|Helpers · outer circle
john-simon|John Simon|309|Helpers · outer circle
samuel-hoare|Samuel J. G. Hoare|309|Helpers · outer circle
hankey|Maurice P. A. Hankey|309|Helpers · outer circle
wilson-harris|Wilson Harris|309|Helpers · outer circle
francis-clarke|Francis Clarke|309|Helpers · outer circle|tentative
wgs-adams|William George Stewart Adams|309|Helpers · outer circle
wk-hancock|William Keith Hancock|309|Helpers · outer circle|tentative
ernest-woodward|Ernest Llewellyn Woodward|309|Helpers · outer circle
harold-butler|Harold Butler|309|Helpers · outer circle
kenneth-bell|Kenneth N. Bell|309|Helpers · outer circle
donald-somervell|Donald B. Somervell|309|Helpers · outer circle
maurice-gwyer|Maurice L. Gwyer|309|Helpers · outer circle
charles-harris|Charles R. S. Harris|310|Helpers · outer circle
edward-peacock|Edward R. Peacock|310|Helpers · outer circle
cyril-radcliffe|Cyril J. Radcliffe|310|Helpers · outer circle
john-wheeler-bennett|John W. Wheeler-Bennett|310|Helpers · outer circle
robert-stopford|Robert J. Stopford|310|Helpers · outer circle
barrington-ward|Robert M. Barrington-Ward|310|Helpers · outer circle
kenneth-wheare|Kenneth C. Wheare|310|Helpers · outer circle|tentative
edward-carr|Edward Hallett Carr|310|Helpers · outer circle
malcolm-macdonald|Malcolm MacDonald|310|Helpers · outer circle
godfrey-elton|Godfrey Elton|310|Helpers · outer circle
neill-malcolm|Neill Malcolm|310|Helpers · outer circle
willingdon|Freeman Freeman-Thomas|310|Helpers · outer circle
isaiah-berlin|Isaiah Berlin|310|Helpers · outer circle
roger-makins|Roger M. Makins|310|Helpers · outer circle
arthur-willert|Arthur Willert|310|Helpers · outer circle
ivison-macadam|Ivison S. Macadam|310|Helpers · outer circle
arthur-glazebrook|Arthur J. Glazebrook|310|Canada
george-parkin|George Parkin|310|Canada
massey|Vincent Massey|310|Canada
george-glazebrook|George P. de T. Glazebrook|310|Canada
corbett|Percy Corbett|310|Canada
joseph-flavelle|Joseph Flavelle|310|Canada|tentative
beer|George Louis Beer|310|United States
frank-aydelotte|Frank Aydelotte|310|United States
jerome-greene|Jerome Greene|310|United States
clarence-streit|Clarence Streit|310|United States|tentative
smuts|Jan C. Smuts|310|South Africa
duncan|Patrick Duncan|310|South Africa
bailey|Abe Bailey|310|South Africa
basil-long|Basil K. Long|310|South Africa
feetham|Richard Feetham|310|South Africa
james-rose-innes|James Rose-Innes|310|South Africa|tentative
thomas-bavin|Thomas Bavin|310|Australia
fw-eggleston|Frederic Eggleston|310|Australia
dudley-braham|Dudley D. Braham|310|Australia|tentative
james-allen|James Allen|311|New Zealand
downie-stewart|William Downie Stewart|311|New Zealand
arthur-atkinson|Arthur R. Atkinson|311|New Zealand
helmuth-moltke|Helmuth James von Moltke|311|Germany
adam-trott|Adam von Trott zu Solz|311|Germany
'''
roster={}
for line in roster_rows.strip().splitlines():
 parts=line.split('|');id,name,page,section=parts[:4];page=int(page);tentative=len(parts)>4
 if id not in roster:roster[id]=dict(name=name,pages=[],sections=[],tentative=False)
 r=roster[id];r['pages'].append(page);r['sections'].append(section);r['tentative'] |= tentative
org('milner-group','Milner Group','Quigley’s analytical label for overlapping personal, institutional and political networks pursuing imperial unity. It is not a verified formal membership organization. The author explicitly warns that the roster is tentative.',[5,6,9,307],founders='Quigley traces the network to Rhodes, Milner, Stead and their associates; formal incorporation is not established.',founderIds=['rhodes','milner','stead','esher'],members=list(roster),evidence='Author’s network interpretation')
org('society-elect','Society of the Elect','Inner-circle structure proposed in the Rhodes–Stead discussions of 1891, as reconstructed by Quigley. He says the ideal organizational plan was not implemented in all its details.',[8,42,43,307,308],founders='Rhodes, Stead and Brett in Quigley’s reconstruction.',founderIds=['rhodes','stead','esher'],members=[id for id,r in roster.items() if 'Society of the Elect' in r['sections']],evidence='Author’s network interpretation')
org('association-helpers','Association of Helpers','Proposed outer association in the 1891 plan. Quigley relates it to the later Kindergarten and Round Table circles and lists inner and outer subdivisions tentatively.',[9,42,43,308,309,310],founders='Part of the 1891 organizational plan described by Quigley.',founderIds=['rhodes','stead','esher'],members=[id for id,r in roster.items() if any(s.startswith('Helpers') for s in r['sections'])],evidence='Author’s network interpretation')
for id,r in roster.items():
 p=next((p for p in people if p['id']==id),None)
 if not p:
  person(id,r['name'],'Tentative roster entry',f"Quigley lists {r['name']} under {'; '.join(r['sections'])} in his tentative appendix. This entry records his classification, not independently established membership."+(' The name is bracketed, indicating the author lacked convincing evidence.' if r['tentative'] else ''),r['pages'],evidence='Bracketed conjecture' if r['tentative'] else 'Tentative roster')
 else:
  p['citations']+=cite(sorted(set(r['pages'])),'Tentative appendix classification; not independent membership verification.')
 p=next(p for p in people if p['id']==id);p['roster']=dict(sections=r['sections'],bracketed=r['tentative'],sourceId=SOURCE,pages=sorted(set(r['pages'])))
 relation(id,'milner-group','Quigley’s roster: '+'; '.join(r['sections']),r['pages'],evidence='Bracketed conjecture' if r['tentative'] else 'Tentative roster')
# Institutional entries separate organizations from the author's umbrella labels.
org('cecil-bloc','Cecil Bloc','Quigley’s name for the Cecil family’s political and social nexus, including relatives, proteges and Oxford connections. The book treats this as a patronage network, not an incorporated body.',[19,20,21,32],founders='Robert Gascoyne-Cecil, 3rd Marquess of Salisbury, in Quigley’s analysis.',founderIds=['salisbury'],members=['salisbury','balfour','robert-cecil','edward-cecil','curzon','goschen','asquith','rosebery','edward-grey'],evidence='Author’s network interpretation')
org('kindergarten','Milner’s Kindergarten','Informal name for Milner’s South African administrative assistants. Quigley differentiates civil-service members from other associates present in South Africa.',[54,55,56,84],founders='Alfred Milner assembled the administrative team.',founderIds=['milner'],members=['duncan','kerr','brand','curtis','dawson','buchan','dougal-malcolm','hichens','feetham','dove','basil-williams','hugh-wyndham','fiddes','walrond','monypenny'],evidence='Source-described informal team')
org('round-table','Round Table movement','Study circles across Britain and the Dominions seeking closer imperial relationships. Quigley identifies Kerr as London secretary and Curtis as the international organizer. Distinct from its quarterly journal and from India’s official Round Table Conferences.',[119,120,121,123],founders='Curtis, Kerr and cooperating Kindergarten associates; Bailey supplied early finance.',founderIds=['curtis','kerr'],members=['curtis','kerr','brand','marris','arthur-glazebrook','massey','george-glazebrook','james-allen','downie-stewart','beer'])
org('round-table-journal','The Round Table · journal','Quarterly founded in 1910 as the movement’s publication. Quigley describes anonymous contributions and editorial succession; this record denotes the publication, not every organization using the phrase Round Table.',[119,123,126,127],founders='Kerr and the Round Table circle, with Bailey’s financial support.',founderIds=['kerr','bailey'],members=['kerr','dove','hv-hodson','harlow','coupland','dawson'])
org('rhodes-trust','Rhodes Trust','Trust administering Rhodes’s scholarship bequest. Quigley analyzes the trustees and secretaries as an institutional link within his network thesis.',[36,37,90],founders='Cecil Rhodes’s final will supplied the bequest.',founderIds=['rhodes'],members=['milner','george-parkin','dawson','grigg','kerr','albert-grey','beit','michell','hawksley','amery','fisher','holland','edward-peacock'])
org('beit-trust','Beit Railway Trust','Beit’s bequest for transport and other improvements in Africa. Quigley compares its governance with the Rhodes Trust and Oxford academic appointments.',[90,91],founders='Alfred Beit’s bequest.',founderIds=['beit'])
org('all-souls','All Souls College, Oxford','Oxford college whose fellowships and public-service connections recur in Quigley’s study. The author explicitly distinguishes college membership from membership in his Milner Group.',[24,25,26,74,95],founders='The book names Henry Chichele as the founder of the endowment.',members=['salisbury','anson','brand','dawson','dougal-malcolm','raleigh','halifax','zimmern','corbett','isaiah-berlin'])
org('balliol','Balliol College, Oxford','Oxford college associated with Milner’s early friendships and Toynbee’s social ideas in this account.',[12,13,14,15],members=['milner','arnold-toynbee','george-parkin','gell','michael-glazebrook','raleigh','asquith','amery','jowett'])
org('new-college','New College, Oxford','Quigley describes it as a recurrent educational setting for the Kindergarten and later recruitment, especially through Fisher’s recommendations.',[55,56,73,74],members=['milner','fisher','curtis','kerr','brand','dougal-malcolm','hichens','feetham','coupland'])
org('oxford-university','University of Oxford','University containing the colleges, scholarship schemes and academic posts discussed in Quigley’s institutional analysis. Affiliation alone does not establish political-network membership.',[12,91,101],members=['milner','fisher','halifax','zimmern','coupland','salisbury','goschen','curzon'])
org('toynbee-hall','Toynbee Hall','London social-settlement institution described as a memorial to Arnold Toynbee. Quigley connects it to Milner’s educational and social-service interests.',[12,13,15],founders='Quigley describes Milner’s role in establishing the memorial settlement and making Gell first chairman.',members=['milner','gell','barnett'])
org('bsac','British South Africa Company','Chartered company associated with Rhodes’s African expansion. Quigley discusses its directors and relationships to administration, journalism and the 1895 raid.',[16,41,50,51,58],founders='Cecil Rhodes’s project, established by royal charter in 1889, in Quigley’s account.',founderIds=['rhodes'],members=['rhodes','albert-grey','gell','jameson','dougal-malcolm','maguire','michell'])
org('closer-union','Closer Union Societies','Advocacy bodies created in South Africa to promote political union, using memoranda, comparative constitutions and journalism.',[77,78],founders='Lionel Curtis with Philip Kerr’s assistance and Selborne’s permission.',founderIds=['curtis','kerr'],members=['curtis','kerr','dawson','hichens','brand','feetham','dougal-malcolm'])
org('intercolonial-council','Inter-colonial Council','Administrative link between the Transvaal and Orange River Colony. Quigley treats it as a practical precursor to wider union.',[55,58,77],members=['brand','hichens','duncan'])
org('central-sa-railways','Central South African Railways','Railway administration linking the former colonies, identified as a lever for closer union in Quigley’s account.',[55,58,77,82],members=['hichens','marris'])
org('the-state','The State · South African journal','Monthly established to support South African union. Quigley calls it a precursor to The Round Table.',[9,77,75],founders='Kindergarten associates; financed by Abe Bailey.',founderIds=['bailey','kerr'],members=['kerr','basil-long'])
org('times','The Times','London newspaper. Quigley studies overlap between its proprietors, editors, Oxford associates and imperial policy; assertions of coordinated control are the author’s interpretation.',[103,104,105,106,108],members=['george-buckle','dawson','amery','grigg','basil-long','monypenny','florashaw','chilrol','northcliffe','waldorf-astor','john-jacob-astor','brand'])
org('cape-times','Cape Times','South African newspaper associated in the book with Garrett and later Basil Long. Quigley notes differing accounts of its early ownership.',[47,75],members=['garrett','basil-long'])
org('johannesburg-star','Johannesburg Star','South African newspaper edited at different periods by Monypenny and Dawson in the book’s account.',[65,77],members=['dawson','monypenny'])
org('pall-mall-gazette','Pall Mall Gazette','Newspaper where Quigley locates early working relationships among Stead, Milner, Cook and other associates.',[16,40,45],members=['stead','milner','edward-cook'])
org('review-reviews','The Review of Reviews','Stead’s magazine, founded in 1890 and discussed as a possible public-facing element of Rhodes’s proposed association.',[16,42],founders='William T. Stead.',founderIds=['stead'],members=['stead'])
org('imperial-federation-league','Imperial Federation League','Advocacy organization established in 1884 in Quigley’s account; Parkin joined its Canadian branch and carried out overseas speaking work before its dissolution.',[12,130],members=['george-parkin','brassey','goschen'])
org('lazard','Lazard Brothers and Company','Banking firm where Quigley locates Brand and later Adam Marris, linking finance and wartime service.',[63,126,301],members=['brand'])
org('lloyds-bank','Lloyd’s Bank','Bank where Quigley identifies Brand as a director. This is a reported business appointment, not proof of political control.',[63],members=['brand'])
org('cliveden-circle','Cliveden circle','A label associated with gatherings at the Astors’ house. Quigley says the popular label inadequately represents the broader network and distinguishes differing policy positions within it.',[9,63,75],founders='Not a formally founded institution; gatherings were hosted by the Astors.',members=['waldorf-astor','nancy-astor','brand','kerr','dawson','halifax'],evidence='Author’s network interpretation')
org('war-cabinet','British War Cabinet','Wartime decision-making body discussed in connection with Lloyd George, Milner, Curzon, secretarial staff and postwar planning.',[145,146,157],members=['lloyd-george','milner','curzon','hankey','amery','kerr','grigg'])
org('imperial-war-cabinet','Imperial War Cabinet','Wartime body incorporating representatives from overseas parts of the empire. Quigley discusses its role in consultations and the peace delegation.',[146,157,160],members=['lloyd-george','milner','smuts','meston','hankey'])
org('committee-defence','Committee of Imperial Defence','Defence-coordination committee whose secretariat connected to the wartime cabinets, as described by Quigley.',[45,157,158],members=['esher','hankey'])
org('colonial-office','Colonial Office','British department for colonial administration; the book follows appointments and policies across Milner, Amery and later officials.',[54,148,163],members=['joseph-chamberlain','milner','amery','fiddes','ormsby-gore','malcolm-macdonald'])
org('league-of-nations','League of Nations','International institution whose covenant, mandates and intellectual-cooperation work feature in Quigley’s account.',[20,29,147,172],founders='International peace-settlement arrangements; no single founder is claimed in these passages.',members=['robert-cecil','zimmern','fisher','corbett','lugard'])
org('mandates-commission','Permanent Mandates Commission','League commission supervising the mandate system. Quigley traces successive British representatives.',[172],members=['ormsby-gore','lugard','malcolm-hailey','hankey'])
org('peel-commission','Peel Commission','Commission investigating Palestine whose report proposed partition. Quigley discusses Coupland’s involvement and the subsequent debate.',[173,176,177],members=['coupland'])
org('irish-boundary-commission','Irish Boundary Commission','Body chaired by Richard Feetham in 1924–1925, as recorded in the Kindergarten chapter.',[57],members=['feetham'])
org('psychical-research','Society for Psychical Research','Society described by Quigley as another meeting ground for members of the Cecil family network, distinct from imperial-policy institutions.',[34,35],founders='The book names the Balfour family and relatives Rayleigh and Sidgwick.',founderIds=['balfour'],members=['balfour','gilbert-murray','edith-lyttelton'])
# Nine new historical threads; shared event IDs visibly connect lanes.
new_lanes=[('anglo-origins','Rhodes & network origins','#c9aa76'),('anglo-oxford','Oxford & scholarships','#9fabc8'),('anglo-south-africa','South Africa & union','#a9bfa8'),('anglo-press','Press & publishing','#cd9390'),('anglo-commonwealth','War & Commonwealth','#b3a0bf'),('anglo-institutes','International-affairs institutes','#8dbdbb'),('anglo-india','India & constitutional reform','#d3b476'),('anglo-foreign','European diplomacy','#a6b6d1'),('anglo-wartime','Wartime research & Washington','#c995b0')]
for id,name,color in new_lanes:
 if not any(l['id']==id for l in data['lanes']):data['lanes'].append(dict(id=id,name=name,color=color,sourceIds=[SOURCE]))
for l in data['lanes']:
 if not l.get('sourceIds'):l['sourceIds']=['anglo']
A='anglo-origins';O='anglo-oxford';S='anglo-south-africa';P='anglo-press';C='anglo-commonwealth';I='anglo-institutes';D='anglo-india';F='anglo-foreign';W='anglo-wartime'
event('confession','1875-01-01','Rhodes’s imperial program','describes Rhodes’s Confession of Faith as an early statement of the aims later embedded in his wills and society plans.',[36,37],[A],['rhodes'])
event('first-will','1877-01-01','Rhodes’s first will','describes a bequest for an association devoted to expanding British rule and links it to Rhodes’s earlier program. The year is given; January 1 is a plotting anchor.',[36,37],[A,O],['rhodes'],['society-elect'])
event('milner-press','1881-01-01','Milner begins writing for the Pall Mall Gazette','places Milner’s entry into journalism in 1881, connecting him to Morley and Stead. This is a reported professional relationship.',[16],[A,P],['milner','stead'],['pall-mall-gazette'])
event('psychical-society','1882-01-01','Psychical research society founded','describes the Balfour family and relatives founding the Society for Psychical Research, later a meeting ground for several associates.',[34,35],[A,O],['balfour'],['psychical-research'])
event('toynbee-death','1883-01-01','Arnold Toynbee dies','records the death of Milner’s close friend and the subsequent memorial work. This is Arnold Toynbee, not the later historian Arnold J. Toynbee.',[12,14],[A,O],['arnold-toynbee','milner'],['balliol'])
event('toynbee-hall','1884-01-01','Toynbee Hall opens','describes the memorial settlement opening with Gell as its first chairman and Milner involved in its establishment.',[12,13],[A,O],['milner','gell','barnett'],['toynbee-hall'])
event('federation-league','1884-01-01','Imperial Federation League established','places the league’s founding in 1884 and associates it with earlier imperial-unity advocacy.',[130],[A,C],['brassey','goschen'],['imperial-federation-league'])
event('goschen-secretary','1887-01-01','Milner serves Goschen in government','describes Milner becoming Goschen’s private secretary when Goschen became Chancellor, opening further political and administrative connections.',[18],[A,C],['milner','goschen'],['cecil-bloc'])
event('rhodes-stead','1889-04-04','Rhodes shares plans with Stead','dates the introduction of Stead to Rhodes’s society scheme to April 4, 1889; the book distinguishes these preliminary discussions from the later organizational plan.',[8,40,41],[A,P],['rhodes','stead'],precision='day')
event('bsac-charter','1889-01-01','British South Africa Company charter','describes the company’s royal charter and the introduction of Albert Grey to Rhodes through Stead.',[16,41],[A,S],['rhodes','stead','albert-grey'],['bsac'])
event('review-founded','1890-01-01','Stead establishes Review of Reviews','records Stead leaving the Pall Mall Gazette editorship and founding his magazine.',[16,42],[A,P],['stead'],['review-reviews'])
event('brett-plan','1890-02-03','Brett is told of Rhodes’s scheme','dates Brett’s introduction to the plan to February 3, 1890, before the organizational discussion of 1891.',[8,41],[A],['rhodes','stead','esher'],precision='day')
event('society-plan','1891-02-01','The 1891 society plan','reconstructs a London discussion among Rhodes, Stead and Brett, with Milner included in the proposed leadership. Quigley says the ideal arrangement did not take effect in all its details. The precise day is not supplied.',[8,42,43],[A,P,O],['rhodes','stead','esher','milner'],['society-elect','association-helpers'],precision='month',evidence='Author’s reconstruction')
event('parkin-contract','1893-06-01','Parkin’s federation work receives funding','describes Parkin, Milner and Brassey signing a three-year agreement to finance public advocacy for imperial solidarity.',[12,46],[A,C],['george-parkin','milner','brassey'],precision='day')
event('jameson-raid','1895-12-01','Jameson Raid','examines the failed raid, Rhodes’s communications and the Times role. His account of coordinated planning and concealment remains attributed to the book.',[50,109,110,111,112],[A,S,P],['jameson','rhodes','florashaw','stead','esher'],['bsac','times'],precision='month')
event('rhodes-resignation','1896-01-07','Rhodes’s resignation announced','quotes the Times history dating the announcement of Rhodes’s departure from the premiership after the raid; he analyzes the newspaper’s shift toward the Kaiser telegram.',[110],[S,P],['rhodes','florashaw'],['times'],precision='day')
event('milner-commissioner','1897-01-01','Milner becomes High Commissioner','describes the South African appointment as the turning point that enabled his administrative team. The account of how the appointment was secured is Quigley’s interpretation.',[18,54],[A,S],['milner','joseph-chamberlain'],['colonial-office','kindergarten'])
event('beit-dinner','1898-11-30','Trustees meet at Beit’s house','describes Milner, Grey and Beit dining with Gell and discussing important matters; the contents of the conversation are not fully established.',[53],[A,O],['milner','albert-grey','beit','gell'],['rhodes-trust'],precision='day')
event('boer-war','1899-01-01','Boer War and reconstruction','discusses the 1899–1902 war and Milner’s administrative network. His thesis that the network caused the war is an interpretation, not a conclusion independently established by this archive.',[9,54,55,65],[A,S,P],['milner','rhodes','stead','jameson'],['kindergarten'],endDate='1902-12-31')
event('rhodes-death','1902-03-26','Rhodes dies; trust succession','dates Rhodes’s death and describes Milner assuming greater influence over the bequest and associated institutions.',[52,89,90],[A,O],['rhodes','milner','george-parkin'],['rhodes-trust'],precision='day')
event('beit-chair','1905-01-01','Beit colonial-history chair established','describes the Oxford chair and lectureship endowed by Beit, with Egerton as the first professor. Institutional-control claims belong to Quigley.',[90,91],[O,S],['beit','egerton'],['oxford-university','all-souls'])
event('selborne-succeeds','1905-01-01','Selborne succeeds Milner','describes the new High Commissioner carrying on with Milner’s selected personnel after Milner returned to England.',[54,87],[A,S],['selborne','milner'],['kindergarten'])
event('closer-union-campaign','1906-01-01','Closer Union Societies organized','describes Curtis and Kerr creating advocacy groups with Selborne’s permission, supported by fellow Kindergarten associates and journalism.',[77,78],[S,P,C],['curtis','kerr','selborne','brand','dawson','bailey'],['closer-union','kindergarten'])
event('selborne-dispatch','1907-01-07','Selborne Federation Dispatch','dates the dispatch setting out arguments for closer South African union, built from Curtis’s memorandum, Kerr’s railway section and Selborne’s additions.',[78],[S,C],['curtis','kerr','selborne'],['closer-union'],precision='day')
event('the-state','1908-01-01','The State supports South African union','places the founding of the monthly in 1908 and describes Bailey’s financing, Kerr’s editorship and later continuity with The Round Table.',[9,75,77],[S,P],['kerr','basil-long','bailey'],['the-state'])
event('union-convention','1908-01-01','South African National Convention','examines the 1908–1909 convention and describes Smuts, Brand and Duncan working on arrangements for union. Formal proceedings and the author’s reconstruction are distinguished.',[78,79,80],[S,C],['smuts','brand','duncan','curtis'],['closer-union'],endDate='1909-12-31')
event('canadian-tour','1909-01-01','Curtis, Kerr and Marris visit Canada','describes a four-month trip to investigate imperial relationships; a discussion with Marris broadened Curtis’s view of self-government beyond Europe.',[119,120],[C,D,A],['curtis','kerr','marris'],['round-table'])
event('south-african-union','1910-01-01','Union of South Africa established','describes the constitution emerging from the convention and traces the Kindergarten’s advocacy. He connects completion of this project to expansion of the Round Table movement.',[78,80,84,120],[S,C,P],['smuts','curtis','brand','duncan'],['closer-union','round-table'])
event('round-table-first','1910-11-15','First issue of The Round Table','gives November 15 as the date on the first issue. He describes anonymous contributions, Kerr’s editorial role and Bailey’s funding.',[119,123],[P,C,A],['kerr','curtis','bailey'],['round-table','round-table-journal'],precision='day')
event('canadian-groups','1911-01-01','Canadian Round Table groups established','describes Arthur Glazebrook establishing about a dozen local units with support from Milner, Curtis, Kerr and Marris.',[121,123],[C,A],['arthur-glazebrook','milner','curtis','kerr','marris'],['round-table'])
event('dawson-times','1912-01-01','Dawson takes the Times editorship','describes Dawson replacing Buckle in 1912, followed by a break in his tenure and return after the later ownership change.',[104,105],[P,A],['dawson','george-buckle','northcliffe'],['times'])
event('lloyd-coalition','1916-12-01','Lloyd George’s wartime coalition','describes Milner entering government without portfolio and several associates taking ministerial or secretarial posts. His explanation of the political intrigue is explicitly an author interpretation.',[144,145,146],[C,A],['lloyd-george','milner','fisher','balfour','kerr'],['war-cabinet'],precision='month')
event('imperial-war','1917-01-01','Imperial War Cabinet consultation','describes fourteen meetings in 1917 and the use of the defence committee’s staff as a shared secretariat, tying wartime consultation to Dominion equality.',[157,160],[C,S],['milner','smuts','hankey','meston'],['imperial-war-cabinet','committee-defence'])
event('smuts-commonwealth','1917-05-15','Smuts speaks of a British Commonwealth','dates Smuts’s parliamentary banquet speech and analyzes its use in popularizing the expression British Commonwealth of Nations.',[153],[C,S],['smuts','milner'],precision='day')
event('milner-war-secretary','1918-04-01','Milner becomes Secretary of State for War','places the appointment in April after his work in France and the Allied command arrangements.',[146,147],[C],['milner','amery','esher'],['war-cabinet'],precision='month')
event('peace-delegation','1919-01-01','Paris peace delegation and expert advisers','examines the concentration of the network’s experts around the British peace delegation, while noting Lloyd George’s independence on several decisions.',[147,149,150],[C,I,F],['milner','smuts','balfour','brand','robert-cecil','zimmern','lloyd-george'],['foreign-office','league-of-nations'])
event('milner-equality','1919-07-09','Milner states an equal-partnership principle','dates a formal statement advocating equal partnership between the United Kingdom and Dominions.',[160],[C],['milner'],precision='day')
event('irish-truce','1921-07-11','Irish armistice takes effect','describes Smuts’s discussions with Irish leaders, the armistice and the opening of a conference three days later; the book presents his role as mediation.',[181,182],[C,S],['smuts','lloyd-george','curtis'],precision='day')
event('times-purchase','1922-01-01','Astor interests acquire The Times','describes purchase of the Harmsworth interest by the Astor brothers and Dawson’s return; Brand’s role in engineering the transaction is Quigley’s attribution.',[104,105,106],[P,A],['waldorf-astor','john-jacob-astor','brand','dawson','northcliffe'],['times'])
event('egypt-declaration','1922-01-01','Egyptian independence declaration','connects the declaration to Milner’s earlier personal negotiations and names Fiddes, Amery and Walrond as advisers or officials.',[183],[C,A],['milner','fiddes','amery','walrond'],['colonial-office'])
event('boundary-commission','1924-01-01','Irish Boundary Commission chaired by Feetham','records Feetham’s chairmanship in 1924–1925 as one of the later roles of a former Kindergarten official.',[57],[C,S],['feetham'],['irish-boundary-commission'],endDate='1925-12-31')
event('milner-death','1925-05-01','Milner dies','records Milner’s death in May 1925 and examines subsequent changes in leadership, Rhodes Trust administration and Oxford positions.',[73,101,160],[A,O,C],['milner','fisher','kerr'],['rhodes-trust','new-college'],precision='month')
event('rhodes-house','1929-01-01','Rhodes House opens','describes colonial-history books being moved from the Bodleian and office and lecture space being assigned to the Beit professor.',[91],[O],['coupland'],['rhodes-trust','oxford-university'])
event('commonwealth-conference','1933-01-01','Unofficial Commonwealth relations conference','describes the first unofficial conference in Toronto, with delegates and participants connected to international-affairs institutes. This is distinct from official Imperial Conferences.',[165,166],[C,I],['robert-cecil','arnold-j-toynbee','zimmern'],['riia'])
event('peel-report','1937-01-01','Peel Commission partition proposal','describes the report proposing partition of Palestine and discusses Coupland’s contribution; the author’s inference about internal group deliberations remains an inference.',[173,176,177],[C,I],['coupland','amery'],['peel-commission'])
# Merge bounded late-chapter research, resolving aliases rather than duplicating identities.
late=json.loads(Path('scripts/data/anglo-late-research.json').read_text())
alias={'lionel-curtis':'curtis','philip-kerr':'kerr','robert-brand':'brand','arnold-toynbee':'arnold-j-toynbee','alfred-zimmern':'zimmern','james-meston':'meston','abe-bailey':'bailey','edward-wood':'halifax','hal-fisher':'fisher','leopold-amery':'amery','edward-grigg':'grigg','bk-long':'basil-long','vincent-massey':'massey','percy-corbett':'corbett','william-marris':'marris','john-dove':'dove','the-times':'times','french-government':'french-government'}
def canonical(id):return alias.get(id,id)
for p in late['people']:
 id=canonical(p['id']);old=next((x for x in people if x['id']==id),None)
 if old:
  old['citations']+=cite(p['pages'],'Additional roles in chapters 10–13.')
  if old.get('role')=='Tentative roster entry':old['description']=p['description']+' '+old['description'];old['role']='Public figure / institutional associate';old['evidence']='Reported role; tentative roster'
 else:person(id,p['name'],'Public figure / institutional associate',p['description'],p['pages'],p.get('aliases',[]))
person('austen-chamberlain','Austen Chamberlain','Foreign secretary · cabinet minister','Quigley describes his wartime India Office role and later handling of European agreements. He is Joseph Chamberlain’s son, distinct from Neville Chamberlain.',[145,147,260,261,262])
for id,name,desc,pg in [
 ('foreign-office','Foreign Office','British diplomatic department; Quigley follows ministerial, intelligence and research appointments and successive foreign-policy decisions.',[147,197,271]),
 ('inquiry','The Inquiry','American peace-conference experts mentioned alongside British counterparts in the origin story of the international-affairs institutes.',[184]),
 ('jp-morgan','J. P. Morgan and Company','Financial firm associated with Thomas Lamont, whose donation funded the Peace Conference history in Quigley’s account.',[185]),
 ('british-treasury','British Treasury','Government financial administration represented in wartime America by Brand and other officials in the book.',[301]),
 ('lse','London School of Economics','Academic institution named as the auspices under which Agenda was founded; the editorial offices were at Chatham House.',[305]),
 ('labour-party','Labour Party','British political party whose postwar government interrupted the network influence Quigley describes. The account is written before later political developments.',[305,306]),
 ('indian-national-congress','Indian National Congress','Indian nationalist party discussed in connection with Gandhi, participation in constitutional talks and opposition to the terms of reform.',[211,218,220]),
 ('french-government','French government · intellectual-cooperation role','Government named as establishing the International Institute of Intellectual Cooperation and handing it to the League in 1926.',[194])]:org(id,name,desc,pg)
for o in late['organizations']:
 id=canonical(o['id']);founder_ids=[canonical(x) for x in o['founders']];members=[canonical(x) for x in o['members']]
 org(id,o['name'],o['description'],o['pages'],founders='Founding participants / sponsors named in the cited account.' if founder_ids else 'Not established in the cited passages.',founderIds=founder_ids,members=members)
org_by_id={o['id']:o for o in orgs}
# Core institutions provide a common chronology, while topic lanes keep the wider plot manageable.
for e in late['events']:
 os=[canonical(x) for x in e['organizations']];ps=[canonical(x) for x in e['people']]
 if e['id']=='anglo-toronto-conference':continue # same event already entered, with both chapter citations below
 if e['id']=='anglo-bailey-endowment':pass
 if any(x in os for x in ['india-office','indian-round-table-conferences','indian-national-congress']):ls=[D,C]
 elif e['id'] in ['anglo-halifax-hitler','anglo-eden-replaced','anglo-geneva-protocol-rejected','anglo-locarno','anglo-naval-agreement','anglo-rhineland','anglo-munich-crisis','anglo-bohemia-moravia','anglo-polish-guarantee','anglo-national-service']:ls=[F,C]+([P] if 'times' in os else [])
 elif any(x in os for x in ['british-embassy-washington','british-food-mission','british-shipping-mission','frps','foreign-office-research','ministry-of-information','agenda','unrra','labour-party']):ls=[W]+([I] if 'riia' in os else [])+([O] if 'all-souls' in os or 'rhodes-trust' in os else [])
 else:ls=[I]+([C] if any(x in os for x in ['canadian-iia','australian-iia','new-zealand-iia','south-african-iia','indian-iia']) else [])
 date=e['date']+'-01-01' if len(e['date'])==4 else e['date']+'-01' if len(e['date'])==7 else e['date']
 end=e.get('endDate');end=end+'-12-31' if end and len(end)==4 else end+'-28' if end and len(end)==7 else end
 item=base(e['id'],e['title'],'event',date,e['description'],e['pages'],date=date,precision=e['precision'],lanes=ls,people=ps,organizations=os,status='Source-described event',evidence='Source-described event')
 if end:item['endDate']=end
 if e['id']=='anglo-ipr-founded':item['evidence']='Author’s chronology · not independently checked';item['status']=item['evidence']
 if e.get('printedPages'):item['citations'][0]['printedPages']=e['printedPages']
 events.append(item)
for r in late['relationships']:relation(canonical(r['source']),canonical(r['target']),r['label'],r['pages'],evidence='Source-described relationship')
# Specific relationships from the early chapters, separate from roster-only membership.
for a,b,label,pg in [
 ('milner','arnold-toynbee','Close friendship and intellectual influence',[12,14,15]),('arnold-toynbee','arnold-j-toynbee','Uncle / nephew',[12]),('milner','goschen','Private secretary and patronage',[16,18]),('salisbury','balfour','Uncle / nephew',[19,21]),('milner','violet-milner','Marriage in 1921',[20]),('violet-milner','edward-cecil','Earlier marriage',[20,21]),('salisbury','edward-cecil','Father / son',[20]),('salisbury','robert-cecil','Father / son',[20]),('george-parkin','massey','Father-in-law / son-in-law',[13]),('arthur-glazebrook','george-glazebrook','Father / son',[121,122,123]),('brand','nancy-astor','Married her sister',[63]),('florashaw','lugard','Marriage in 1902',[108]),('waldorf-astor','john-jacob-astor','Brothers',[106]),('esher','hankey','Mentor / protege',[158]),('fisher','anson','Oxford fellowship recruitment',[74]),('bailey','round-table-journal','Founding financial support',[77,119]),('bailey','the-state','Financial support',[77]),('curtis','kerr','Organizing partnership',[77,119]),('dawson','northcliffe','Editorial conflict',[104,105]),('milner','selborne','High Commission succession',[54]),('rhodes','stead','Society-plan discussions',[40,41,42]),('rhodes','esher','Society-plan discussions',[8,42]),('rhodes','beit','Business and trusteeship',[50]),('rhodes','jameson','Personal and political association',[50]),('milner','smuts','Political cooperation interpreted by Quigley',[79,80,81]),('duncan','smuts','Political lieutenant',[56,81])]:relation(a,b,label,pg)
# Organization membership is stored once and converted to explicitly cited affiliation edges.
for o in orgs:
 for id in o.get('members',[]):
  if o['id'] in ['milner-group','society-elect','association-helpers']:continue
  relation(id,o['id'],'Named associate / role in cited account',o['pages'],evidence='Author’s network interpretation' if o['id'] in ['cecil-bloc','cliveden-circle'] else 'Reported institutional association')
 for id in o.get('founderIds',[]):relation(id,o['id'],'Founding role described',o['pages'],evidence=o.get('evidence','Source account'))
# Append without erasing prior descriptions, IDs, revisions, or other collections.
for key,new in [('people',people),('organizations',orgs),('events',events),('relationships',rels)]:
 index={x['id']:x for x in data[key]}
 for entry in new:
  if entry['id'] not in index:data[key].append(entry);index[entry['id']]=entry
  elif not any(c.get('sourceId')==SOURCE for c in index[entry['id']].get('citations',[])):
   index[entry['id']].setdefault('citations',[]).extend(entry['citations']);index[entry['id']].setdefault('history',[]).append(dict(date=TODAY,note='Cross-source citation added from Quigley.'))
data['version']=2;data['updated']=TODAY
source['chapters']=[dict(title=t,pdfStart=s,pdfEnd=e) for t,s,e in [('Introduction',8,18),('The Cecil Bloc',19,35),('The Secret Society of Cecil Rhodes',36,53),("Milner’s Kindergarten, 1897–1910",54,86),('Milner Group, Rhodes, and Oxford',87,102),('The Times',103,118),('The Round Table',119,143),('War and Peace',144,151),('Creation of the Commonwealth',152,183),('Royal Institute of International Affairs',184,198),('India, 1911–1945',199,225),('Foreign Policy, 1919–1940',226,299),('The Second World War',300,306),('Tentative roster',307,311)]]
# Write merge only after all references resolve.
ids={x['id'] for key in ['people','organizations','events'] for x in data[key]}
for r in data['relationships']:
 assert r['fromId'] in ids and r['toId'] in ids,(r['fromId'],r['toId'])
for e in data['events']:
 for id in e['people']+e['organizations']:assert id in ids,(e['id'],id)
for o in data['organizations']:
 for id in o.get('members',[])+o.get('founderIds',[]):assert id in ids,(o['id'],id)
path.write_text(json.dumps(data,indent=2)+'\n')
print({k:len(data[k]) for k in ['people','organizations','events','relationships','lanes']})
