"""Read-only verification of loader revision and v3 pending transport; no torch import."""
from pathlib import Path
import ast,hashlib,json,tarfile

R=Path(__file__).resolve().parent.parent
O=R/'outputs/scq_rf_initialization_loader_20261114_v2';T=O/'pending_transport_v3'
M=R/'outputs/scq_rf_implementation_20261114_v1'


def read(p):return json.loads(p.read_bytes())
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())


d=read(O/'pending_delivery_v3.json')
for row in [d['request'],d['archive'],d['mapping'],d['implementation_P3'],d['entry_P3']]:assert rec(Path(row['path']))==row
q=read(Path(d['request']['path']));mapping=read(Path(d['mapping']['path']))
assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and not q['execution_authorized']
assert rec(M/'initialization_v1.bin')['sha256']==q['rf_initialization']['sha256']=='a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e'
assert len(mapping['files'])==len({r['target'] for r in mapping['files']})==8
expected={'installation_mapping_v3.json':Path(d['mapping']['path'])}
for row in mapping['files']:
    p=T/row['member'];assert rec(p)['sha256']==row['sha256'] and p.stat().st_size==row['bytes'] and row['overwrite'] is False
    expected[row['member']]=p
archive=Path(d['archive']['path'])
with tarfile.open(archive) as tar:
    members=tar.getmembers();assert len(members)==len({m.name for m in members})==9 and {m.name for m in members}==set(expected)
    listing=''
    for m in members:
        assert m.isfile() and '..' not in Path(m.name).parts
        raw=tar.extractfile(m).read();assert raw==expected[m.name].read_bytes()
        listing+=hashlib.sha256(raw).hexdigest()+'  '+m.name+'\n'
assert listing==Path(str(archive)+'.contents.sha256').read_text(encoding='ascii')
assert Path(str(archive)+'.sha256').read_text(encoding='ascii')==d['archive']['sha256']+'  '+archive.name+'\n'
assert int(Path(str(archive)+'.bytes').read_text())==archive.stat().st_size
old_path=R/'outputs/scq_rf_cuda_preparation_20261114_v2/pending_transport_v2/payload/SCQ_RF_artificial_cuda_execution_request_v2.json'
old=read(old_path);assert rec(old_path)['sha256']==q['supersedes']['request_sha256']
for k in ('entry','rf_initialization','initialization','science','phases','limits','fixture','tolerances','numeric','environment','dependencies','optimizer_policy','identity'):assert q[k]==old[k]
for k in old['implementation']:
    if k!='rf_residual':assert q['implementation'][k]==old['implementation'][k]
for k in ('request_path','authorization_path','runtime_path','launcher_path','launch_attempt_path','tmux_session','log','PID','exit_code'):assert q['launch_contract'][k]!=old['launch_contract'][k]
cpu=read(O/'cpu_loader_batch_v2/result_v2.json');assert cpu['count']==36 and cpu['regeneration_calls']==0 and cpu['forward_calls']==0
assert not any((T/'payload'/n).exists() for n in ('authorization_v3.json','runtime_v3.json','launch_once_v3.sh','attempt_claim_v3.json'))
static=read(O/'static_review_v2.json')
for row in static['preserved']+[static['prior_source']]:assert rec(Path(row['path']))==row
report=O/'冻结字节加载修订_CPU与P3_v3待授权说明_zh.md'
assert d['request']['sha256'] in report.read_text(encoding='utf-8') and d['archive']['sha256'] in report.read_text(encoding='utf-8')
receipt=dict(status='RF_BYTE_LOADER_V3_LOCAL_DELIVERY_PASS_NOT_CUDA_EXECUTED',request=d['request'],archive=d['archive'],report=rec(report),
             current_CPU_checks=36,inherited_graph_checks=59,inherited_entry_checks=52,
             frozen_initialization_unchanged=True,only_loader_AST_changed=True,install_files=8,archive_members=9,
             random_regeneration=0,server_operations=0,CUDA_calls=0,execution_authorized=False,controls_materialized=False)
with (O/'final_local_verification_v3.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2,allow_nan=False)
print(json.dumps(dict(status=receipt['status'],request_SHA256=d['request']['sha256'],archive_bytes=d['archive']['bytes'])))
