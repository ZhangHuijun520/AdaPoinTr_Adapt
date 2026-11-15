"""Final readonly local delivery verification; no model imports or server calls."""
from pathlib import Path
import hashlib,json,tarfile

R=Path(__file__).resolve().parent.parent
O=R/'outputs/scq_rf_Sref_C_training_implementation_20261114_v1';T=O/'pending_transport_v1'


def read(p):return json.loads(p.read_bytes())
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())


d=read(O/'pending_delivery_v1.json')
for row in [d['request'],d['archive'],d['installation_mapping'],d['P3']]:assert rec(Path(row['path']))==row
q=read(Path(d['request']['path']));mapping=read(Path(d['installation_mapping']['path']))
assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
assert q['arm']=='S-ref' and q['variant']=='S' and q['fold']=='C' and q['paired_baseline'] is None
assert q['science']['updates']==3900 and q['science']['exposures']==31200 and q['science']['drops']==300
assert len(mapping['files'])==len({r['target'] for r in mapping['files']})==15
expected={'installation_mapping_v1.json':Path(d['installation_mapping']['path'])}
for row in mapping['files']:
    p=T/row['member'];assert p.stat().st_size==row['bytes'] and rec(p)['sha256']==row['sha256'] and row['overwrite'] is False
    expected[row['member']]=p
arc=Path(d['archive']['path'])
with tarfile.open(arc) as tar:
    members=tar.getmembers();assert len(members)==len({m.name for m in members})==16 and {m.name for m in members}==set(expected)
    listing=''
    for m in members:
        assert m.isfile() and '..' not in Path(m.name).parts
        raw=tar.extractfile(m).read();assert raw==expected[m.name].read_bytes()
        listing+=hashlib.sha256(raw).hexdigest()+'  '+m.name+'\n'
assert listing==Path(str(arc)+'.contents.sha256').read_text(encoding='ascii')
assert Path(str(arc)+'.sha256').read_text(encoding='ascii')==d['archive']['sha256']+'  '+arc.name+'\n'
assert int(Path(str(arc)+'.bytes').read_text())==arc.stat().st_size
prior=read(O/'P3_gap_review_v1.json')
for k in ('entry','bridge','unchanged_runtime','unchanged_contract','test','failure','child_stderr','child_stdout'):assert rec(Path(prior[k]['path']))==prior[k]
cpu=read(O/'cpu_entry_batch_v2/result_v1.json');assert cpu['count']==36 and cpu['optimizer_steps']==cpu['CUDA_calls']==cpu['server_operations']==0
for name in ('authorization_v1.json','runtime_v1.json','launch_once_v1.sh','attempt_claim_v1.json'):assert not (T/'payload'/name).exists()
report=O/'Sref_C_CPU通过_P3与待授权训练说明_zh_v1.md'
assert d['request']['sha256'] in report.read_text(encoding='utf-8') and d['archive']['sha256'] in report.read_text(encoding='utf-8')
result=dict(status='RF_SREF_C_PENDING_TRAINING_LOCAL_DELIVERY_PASS_NOT_EXECUTED',request=d['request'],archive=d['archive'],report=rec(report),
    CPU_checks=36,P3_pass=True,install_files=15,archive_members=16,entry_bridge_runtime_unchanged_during_fixture_fix=True,
    old_failure_preserved=True,server_operations=0,CUDA_calls=0,training_started=False,execution_controls_materialized=False)
with (O/'final_local_verification_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False)
print(json.dumps(dict(status=result['status'],request_SHA256=d['request']['sha256'],archive_bytes=d['archive']['bytes'])))
