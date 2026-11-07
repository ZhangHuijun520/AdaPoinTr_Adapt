"""Materialize isolated runtime: two log statements and checkpoint H2 metadata only."""
from pathlib import Path
import ast,hashlib,json
S=Path(__file__).resolve().parent;R=S.parents[2]
p=R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_p1_training_runtime_v1.py'
raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee'
s=raw.decode('utf-8');old=s
anchor="                    loss = sparse + dense\n";assert s.count(anchor)==1;s=s.replace(anchor,anchor+"                    h2_event = model.h2_runtime_record()\n")
anchor="                    metrics.write(json.dumps(event, allow_nan=False) + '\\n')";assert s.count(anchor)==1;s=s.replace(anchor,"                    event.update(h2_event)\n"+anchor)
anchor="                        'stage': 'BCSP_INPUT_DENSITY_V1', 'updates': 3900}, stream)";assert s.count(anchor)==1;s=s.replace(anchor,"                        'stage': 'BCSP_INPUT_DENSITY_V1', 'updates': 3900,\n                        'H2': model.h2_metadata()}, stream)")
s='# Isolated H2 derivative. Model adapter adds loss once; runtime adds no loss or forward.\n'+s
ast.parse(s)
target=S/'bcsp_h2_training_runtime_v1.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
with (S/'runtime_derivation_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(parent=dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest()),runtime=dict(path=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest()),changes=['capture already-computed detached H2 log after get_loss','merge H2 fields into existing event','checkpoint H2 mode/constants metadata'],update_and_optimizer_lifecycle_unchanged=True),f,indent=2)
print(target)
