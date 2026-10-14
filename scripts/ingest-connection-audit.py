"""Apply Dark Time's review ledgers through the portable, validated skill importer."""
import argparse,datetime,subprocess,sys
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--revision-date',default=datetime.date.today().isoformat())
args=parser.parse_args();root=Path(__file__).resolve().parent.parent
files=sorted((root/'scripts/data').glob('connection-audit-*.json'))+sorted((root/'scripts/data').glob('source-wide-review-*.json'))
command=[sys.executable,str(root/'skills/index-historical-sources/scripts/merge_findings.py'),'--archive',str(root/'src/data/archive.json'),'--revision-date',args.revision_date]
for file in files:command+=['--finding',str(file)]
subprocess.run(command,check=True)
