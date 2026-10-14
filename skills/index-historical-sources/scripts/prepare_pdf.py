#!/usr/bin/env python3
"""Extract page-preserving text and source metadata with local Poppler tools."""
import argparse,hashlib,json,re,subprocess,tempfile
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('pdf',type=Path);parser.add_argument('--source-id',required=True)
parser.add_argument('--output-dir',type=Path,required=True)
parser.add_argument('--title');parser.add_argument('--author');parser.add_argument('--layout',action='store_true')
args=parser.parse_args()
if not re.fullmatch(r'[a-z0-9][a-z0-9-]*',args.source_id):parser.error('source ID must contain lowercase letters, numbers and hyphens')
info=subprocess.check_output(['pdfinfo',str(args.pdf)],text=True)
count=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))
with tempfile.TemporaryDirectory() as temp:
 textpath=Path(temp)/'extracted.txt'
 command=['pdftotext','-enc','UTF-8','-eol','unix']+(['-layout']if args.layout else[])+[str(args.pdf),str(textpath)]
 subprocess.run(command,check=True)
 text=textpath.read_text();pages=text.split('\f')
 if pages[-1].strip()=='':pages.pop()
 if len(pages)!=count:raise SystemExit(f'Expected {count} pages, extracted {len(pages)}. Resolve extraction/page boundaries before indexing.')
digest=hashlib.sha256()
with args.pdf.open('rb')as f:
 for block in iter(lambda:f.read(1024*1024),b''):digest.update(block)
args.output_dir.mkdir(parents=True,exist_ok=True)
metadata=dict(id=args.source_id,title=args.title or args.pdf.stem,author=args.author or 'Not supplied',localPath=str(args.pdf),pageCount=count,sha256=digest.hexdigest(),pageConvention='1-based PDF file pages; printed-page labels must be recorded separately.',textPages=count,blankOrUnextractedPages=[i+1 for i,p in enumerate(pages)if not p.strip()],coverage='Text extracted; manual indexing and review not yet completed.')
(args.output_dir/f'{args.source_id}-pages.json').write_text(json.dumps(pages,ensure_ascii=False)+'\n')
(args.output_dir/f'{args.source_id}-metadata.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+'\n')
print(f'{args.source_id}: {count} PDF pages; {len(metadata["blankOrUnextractedPages"])} blank or unextracted pages; SHA-256 {digest.hexdigest()}')
