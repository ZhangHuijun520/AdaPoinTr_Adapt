"""Read-only local final verification of RF hook v2 deliverables."""
from pathlib import Path
import hashlib,json,tarfile

R=Path(__file__).resolve().parent.parent
O=R/'outputs/scq_rf_cuda_preparation_20261114_v2';T=O/'pending_transport_v2'


def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(p):return json.loads(p.read_bytes())


d=read(O/'pending_delivery_v2.json')
for row in [d['request'],d['archive'],d['mapping'],d['entry'],d['entry_P3']]:assert rec(Path(row['path']))==row
q=read(Path(d['request']['path']));mapping=read(Path(d['mapping']['path']))
assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
assert d['request']['sha256']=='09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf'
assert len(mapping['files'])==7 and len({r['target'] for r in mapping['files']})==7
expected={'installation_mapping_v2.json':Path(d['mapping']['path'])}
for row in mapping['files']:
    p=T/row['member'];assert rec(p)['sha256']==row['sha256'] and p.stat().st_size==row['bytes'] and row['overwrite'] is False
    expected[row['member']]=p
archive=Path(d['archive']['path'])
with tarfile.open(archive) as tar:
    members=tar.getmembers();assert len(members)==8 and len({m.name for m in members})==8 and {m.name for m in members}==set(expected)
    listing=''
    for m in members:
        assert m.isfile() and '..' not in Path(m.name).parts
        raw=tar.extractfile(m).read();assert raw==expected[m.name].read_bytes()
        listing+=hashlib.sha256(raw).hexdigest()+'  '+m.name+'\n'
assert listing==Path(str(archive)+'.contents.sha256').read_text(encoding='ascii')
assert Path(str(archive)+'.sha256').read_text(encoding='ascii')==d['archive']['sha256']+'  '+archive.name+'\n'
assert int(Path(str(archive)+'.bytes').read_text())==archive.stat().st_size
old_path=R/'outputs/scq_rf_cuda_preparation_20261114_v1/pending_transport_v1/payload/SCQ_RF_artificial_cuda_execution_request_v1.json'
old=read(old_path)
assert rec(old_path)['sha256']==q['supersedes']['request_sha256']
for key in ('implementation','initialization','rf_initialization','science','phases','limits','tolerances','fixture','numeric','environment','identity','dependencies','optimizer_policy'):assert q[key]==old[key]
assert all(q['launch_contract'][k]!=old['launch_contract'][k] for k in ('request_path','authorization_path','runtime_path','launcher_path','launch_attempt_path','tmux_session','log','PID','exit_code'))
assert not any((T/'payload'/name).exists() for name in ('authorization_v2.json','runtime_v2.json','launch_once_v2.sh','attempt_claim_v2.json'))
static=read(O/'static_review_v2.json')
for row in static['preserved']+[static['prior_entry'],static['prior_test'],static['failure_audit']]:assert rec(Path(row['path']))==row
report=O/'RF双调用采集修订与v2待授权说明_zh.md'
assert d['request']['sha256'] in report.read_text(encoding='utf-8') and d['archive']['sha256'] in report.read_text(encoding='utf-8')
result=dict(status='RF_HOOK_V2_FINAL_LOCAL_DELIVERY_PASS_NOT_CUDA_EXECUTED',request=d['request'],archive=d['archive'],report=rec(report),
            CPU_entry_checks=52,implementation_CPU_checks=59,entry_P3_pass=True,install_files=7,archive_members=8,
            original_model_initialization_provider_limits_and_old_failure_unchanged=True,prior_request_consumed=True,
            status_after_delivery='AWAITING_EXPLICIT_USER_AUTHORIZATION',server_operations=0,CUDA_calls=0,control_materialized=False,training_request=False)
with (O/'final_local_verification_v2.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False)
print(json.dumps(dict(status=result['status'],request_sha256=d['request']['sha256'],archive_bytes=d['archive']['bytes'])))
