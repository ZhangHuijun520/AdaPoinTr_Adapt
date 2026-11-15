"""Read-only verification of the local RF CUDA pending deliverable."""
from pathlib import Path
import hashlib
import json
import tarfile

R=Path(__file__).resolve().parent.parent
O=R/'outputs/scq_rf_cuda_preparation_20261114_v1'
T=O/'pending_transport_v1'


def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())


d=json.loads((O/'pending_delivery_v1.json').read_bytes())
for row in [d['request'],d['archive'],d['installation_mapping'],d['entry'],d['entry_P3']]:assert rec(Path(row['path']))==row
q=json.loads(Path(d['request']['path']).read_bytes())
assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and not q['execution_authorized']
assert (q['science']['full_forward'],q['science']['full_loss'],q['science']['full_backward'],q['science']['optimizer_steps'])==(5,4,4,0)
assert q['readiness']['server_checked_this_turn'] is False and not q['real_data_allowlist'] and not q['checkpoint_allowlist']
mapping=json.loads(Path(d['installation_mapping']['path']).read_bytes())
assert len(mapping['files'])==12 and len({r['target'] for r in mapping['files']})==12
assert mapping['request_sha256']==d['request']['sha256']
expected={'installation_mapping_v1.json':Path(d['installation_mapping']['path'])}
expected.update({r['member']:T/r['member'] for r in mapping['files']})
for row in mapping['files']:
    p=T/row['member'];assert p.stat().st_size==row['bytes'] and rec(p)['sha256']==row['sha256'] and row['overwrite'] is False
archive=Path(d['archive']['path'])
assert Path(str(archive)+'.sha256').read_text(encoding='ascii')==d['archive']['sha256']+'  '+archive.name+'\n'
assert int(Path(str(archive)+'.bytes').read_text())==archive.stat().st_size
with tarfile.open(archive) as tar:
    members=tar.getmembers();assert len(members)==len(expected)==13 and len({m.name for m in members})==13
    assert {m.name for m in members}==set(expected)
    contents=''
    for m in members:
        assert m.isfile() and '..' not in Path(m.name).parts
        raw=tar.extractfile(m).read();assert raw==expected[m.name].read_bytes()
        contents+=hashlib.sha256(raw).hexdigest()+'  '+m.name+'\n'
assert contents==Path(str(archive)+'.contents.sha256').read_text(encoding='ascii')
ip3=json.loads((R/'outputs/scq_rf_implementation_20261114_v1/P3_implementation_v2.json').read_bytes())
for row in ip3['candidate_sources']+ip3['initialization']:assert rec(Path(row['path']))==row
assert not any((T/'payload'/name).exists() for name in ('authorization_v1.json','runtime_v1.json','launch_once_v1.sh','attempt_claim_v1.json'))
report=O/'RF人工CUDA短入口与待授权说明_zh_v1.md'
assert d['request']['sha256'] in report.read_text(encoding='utf-8') and d['archive']['sha256'] in report.read_text(encoding='utf-8')
receipt=dict(status='RF_CUDA_PENDING_DELIVERY_LOCAL_VERIFY_PASS',request=d['request'],archive=d['archive'],report=rec(report),
             CPU_implementation_checks=59,CPU_entry_checks=37,installation_files=12,archive_members=13,
             production_initialization_unchanged=True,server_operations=0,CUDA_calls=0,execution_authorized=False,
             execution_control_materialized=False,training_request_created=False)
with (O/'final_local_verification_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2,allow_nan=False)
print(json.dumps(dict(status=receipt['status'],request_sha256=d['request']['sha256'],archive_bytes=d['archive']['bytes'])))
