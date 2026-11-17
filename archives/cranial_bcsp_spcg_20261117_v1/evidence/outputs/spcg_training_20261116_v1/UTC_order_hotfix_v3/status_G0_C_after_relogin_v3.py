"""Same read-only query; preserve failed query artifacts by counting raw captures."""
from pathlib import Path
p=Path(__file__).resolve().parent/'status_G0_C_v3.py'
s=p.read_text(encoding='utf-8').replace("glob('status_*_result.json')","glob('status_*_stdout.bin')")
exec(compile(s,str(p),'exec'),dict(__file__=str(p),__name__='__main__'))
