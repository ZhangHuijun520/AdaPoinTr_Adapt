"""One bounded read-only metadata probe; no third-party/model/provider imports."""
import ast
import hashlib
import json
import os
import socket
import sys
import time
from pathlib import Path
start=time.monotonic()
expected='shu-common-25721452-notebook-o9mz8z-0'
assert socket.gethostname()==expected and os.getuid()==1000
root=Path('/home/jovyan/adapointr_work/PoinTr')
assert root.is_dir() and root.resolve()==root
site=Path('/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages')
provider=root/'third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider'
relative=['models/AdaPoinTr.py','models/Transformer_utils.py','models/__init__.py','models/build.py','utils/pointnet2_utils.py','utils/misc.py','tools/runner.py','tools/builder.py','tools/bcsp_adapter.py','tools/bcsp_runtime.py','extensions/chamfer_dist/__init__.py']
paths=[root/r for r in relative]+[provider/'pointnet2_ops'/n for n in ('__init__.py','pointnet2_utils.py','_ext.cpython-310-x86_64-linux-gnu.so')]+[site/'chamfer.cpython-310-x86_64-linux-gnu.so',site/'torch/version.py',Path(sys.executable).resolve()]
wheel=list((provider.parent/'wheelhouse').glob('*.whl'))
assert len(wheel)<=1
paths+=wheel
metadata=[]
for name in ('torch','timm','numpy'):
    found=list(site.glob(name+'-*.dist-info/METADATA'))
    assert len(found)<=1
    paths+=found;metadata+=found
assert len(paths)<=24
rows=[];total=0
for p in paths:
    assert time.monotonic()-start<40
    row={'path':str(p),'exists':p.exists()}
    if p.exists():
        assert p.is_file() and not p.is_symlink()
        size=p.stat().st_size;total+=size
        assert total<=64*1024**2
        h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1048576),b''):h.update(b)
        row.update(bytes=size,sha256=h.hexdigest())
        if p in metadata:
            row['name_version']=[l for l in p.read_text(encoding='utf8').splitlines() if l.startswith(('Name: ','Version: '))][:2]
        if p==site/'torch/version.py':
            row['assignments']={n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(p.read_text()).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('__version__','cuda','hip','git_version','debug')}
    rows.append(row)
print(json.dumps({'hostname':socket.gethostname(),'uid':os.getuid(),'python':sys.version,'python_realpath':str(Path(sys.executable).resolve()),'files':rows,'hashed_bytes':total,'seconds':time.monotonic()-start,'imports':'stdlib only','no_gpu_or_model_calls':True}))
