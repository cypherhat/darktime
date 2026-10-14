"""Run the portable skill scanner against Dark Time's local research pages."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
subprocess.run([sys.executable,str(root/'skills/index-historical-sources/scripts/scan_mentions.py'),'--archive',str(root/'src/data/archive.json'),'--pages-dir',str(root/'tmp/pdfs'),'--output-dir',str(root/'tmp/pdfs')],check=True)
