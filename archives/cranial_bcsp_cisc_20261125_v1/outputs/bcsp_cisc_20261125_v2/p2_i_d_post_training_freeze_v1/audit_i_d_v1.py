import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import time
import zlib

ROOT = Path(__file__).resolve().parents[1]
DEST = Path(__file__).resolve().parent
REQ = "CISC_P2_I_D_training_execution_request_v1.json"
SHA = "9744b973329433c5b84b3974139d11c8ec418a5ea6d28e100439db0a99381818"
SOURCE = {
    "inventory": r"""
import hashlib,json,os,socket,subprocess
from pathlib import Path
assert (socket.gethostname(),os.getuid())==('shu-common-25721452-notebook-zrtpob-0',1000)
p=Path('/home/jovyan/adapointr_work/PoinTr')
o=p/'logs/cranial_bcsp_fullmamba/CISC_P2_I_D_seed2026112601_zrtpob_v1'
a=p/'third_party/bcsp_cisc_p2_i_d_20261125_v1'
assert o.resolve(strict=True)==o and a.resolve(strict=True)==a
def j(f): return json.loads(f.read_bytes())
def rows(f): return list(map(json.loads,f.read_bytes().splitlines()))
def canon(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def emit(v): print('AUDIT '+json.dumps(v,separators=(',',':'),allow_nan=False))
def sha(f):
    assert f.is_file() and f.resolve(strict=True)==f
    h=hashlib.sha256()
    with f.open('rb') as s:
        for b in iter(lambda:s.read(1048576),b''): h.update(b)
    return h.hexdigest()
dirs={'cache','hf','mplconfig','tmp','triton'}
for n in dirs:
    d=o/n
    assert d.resolve(strict=True)==d and d.is_dir() and not any(d.iterdir()),n
assert (o/'exit_code.txt').read_bytes()==b'0\n'
for f in ('launcher.pid','worker.pid'):
    pid=int((o/f).read_bytes())
    assert pid>1 and not Path('/proc',str(pid)).exists(),f
t=subprocess.run(['/usr/bin/tmux','has-session','-t','=cisc_p2_i_d_20261125_v1'],capture_output=True,timeout=5)
assert t.returncode==1 and any(x in t.stderr for x in (b"can't find session",b'no server running',b'error connecting'))
outputs={f.name:[f.stat().st_size,sha(f)] for f in o.iterdir() if f.name not in dirs}
controls={f.name:[f.stat().st_size,sha(f)] for f in a.iterdir()}
emit(dict(outputs=outputs,controls=controls,dirs=sorted(dirs),exit=0))
""",
    "identity": r"""
import hashlib,json,os,socket,subprocess
from pathlib import Path
assert (socket.gethostname(),os.getuid())==('shu-common-25721452-notebook-zrtpob-0',1000)
p=Path('/home/jovyan/adapointr_work/PoinTr')
o=p/'logs/cranial_bcsp_fullmamba/CISC_P2_I_D_seed2026112601_zrtpob_v1'
a=p/'third_party/bcsp_cisc_p2_i_d_20261125_v1'
assert o.resolve(strict=True)==o and a.resolve(strict=True)==a
def j(f): return json.loads(f.read_bytes())
def rows(f): return list(map(json.loads,f.read_bytes().splitlines()))
def canon(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def emit(v): print('AUDIT '+json.dumps(v,separators=(',',':'),allow_nan=False))
files=('completion.json','initialization.json','model_construction.json')
r='CISC_P2_I_D_training_execution_request_v1.json'
auth=j(a/'authorization_v1.json')
assert set(auth)=={'request_sha256','explicit_user_authorization','authorization_text'}
assert auth['explicit_user_authorization'] is True and auth['authorization_text'].strip()
emit(dict(values={f:j(o/f) for f in files},authorization_request=auth['request_sha256'],runtime=j(a/'runtime_v1.json'),order_file=j(a/r)['order']['sha256']))
""",
    "trace": r"""
import hashlib,json,os,socket,subprocess
from pathlib import Path
assert (socket.gethostname(),os.getuid())==('shu-common-25721452-notebook-zrtpob-0',1000)
p=Path('/home/jovyan/adapointr_work/PoinTr')
o=p/'logs/cranial_bcsp_fullmamba/CISC_P2_I_D_seed2026112601_zrtpob_v1'
a=p/'third_party/bcsp_cisc_p2_i_d_20261125_v1'
assert o.resolve(strict=True)==o and a.resolve(strict=True)==a
def j(f): return json.loads(f.read_bytes())
def rows(f): return list(map(json.loads,f.read_bytes().splitlines()))
def canon(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def emit(v): print('AUDIT '+json.dumps(v,separators=(',',':'),allow_nan=False))
from collections import Counter
import math
order=j(o/'order_plan.json')
ex=j(o/'exposure.json')
m=rows(o/'metrics.jsonl')
keys='step epoch batch case_ids source_ids LR BN_momentum clip_max_norm optimizer_step_committed'.split()
batches=[(i,b,ids) for i,e in enumerate(order['epochs']) for b,ids in enumerate(e['batches'])]
assert len(m)==len(batches)==3900 and len(order['epochs'])==100
cases=set(order['case_ids'])
dc=Counter()
for i,e in enumerate(order['epochs']):
    flat=[c for b in e['batches'] for c in b]+e['dropped']
    assert i==e['epoch'] and len(e['batches'])==39 and len(e['dropped'])==3 and len(flat)==len(cases)==315 and set(flat)==cases
    dc.update(e['dropped'])
cc,sc=Counter(),Counter()
for step,(r,(i,b,ids)) in enumerate(zip(m,batches),1):
    src=[':'.join(c.split('__')[:2]) for c in ids]
    assert (r['step'],r['epoch'],r['batch'],r['case_ids'],r['source_ids'])==(step,i,b,ids,src),step
    assert len(ids)==8 and r['optimizer_step_committed'] is True and r['clip_max_norm']==10,step
    vals=[r[k] for k in ('loss_sparse','loss_dense','loss_denoise','loss_reconstruction','loss_aux','loss_aux_weighted','loss','grad_norm_before_clip')]
    assert all(math.isfinite(v) and v>=0 for v in vals),step
    assert math.isclose(vals[4]*.05,vals[5],rel_tol=1e-6,abs_tol=1e-8) and math.isclose(vals[3]+vals[5],vals[6],rel_tol=1e-6,abs_tol=1e-8),step
    cc.update(ids)
    sc.update(src)
digest=canon(order)
assert ex==dict(case=cc,source=sc,dropped_case=dc,order_sha256=digest)
emit(dict(batch_count=len(m),trajectory_sha256=canon([[r[k] for k in keys] for r in m]),canonical_order=digest,case_count=len(cc),source_count=len(sc),exposed=sum(cc.values()),dropped=sum(dc.values()),loss_decomposition_steps=len(m)))
""",
    "resources": r"""
import hashlib,json,os,socket,subprocess
from pathlib import Path
assert (socket.gethostname(),os.getuid())==('shu-common-25721452-notebook-zrtpob-0',1000)
p=Path('/home/jovyan/adapointr_work/PoinTr')
o=p/'logs/cranial_bcsp_fullmamba/CISC_P2_I_D_seed2026112601_zrtpob_v1'
a=p/'third_party/bcsp_cisc_p2_i_d_20261125_v1'
assert o.resolve(strict=True)==o and a.resolve(strict=True)==a
def j(f): return json.loads(f.read_bytes())
def rows(f): return list(map(json.loads,f.read_bytes().splitlines()))
def canon(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def emit(v): print('AUDIT '+json.dumps(v,separators=(',',':'),allow_nan=False))
from collections import Counter
import math
q=j(a/'CISC_P2_I_D_training_execution_request_v1.json')
rr=rows(o/'p3_resources.jsonl')
st=Counter(r['stage'] for r in rr)
assert set(st)=={'initial','monitor','before_first_step','epoch_end','before_checkpoint','after_checkpoint'}
assert st['monitor']>0 and st['epoch_end']==100 and all(st[k]==1 for k in ('initial','before_first_step','before_checkpoint','after_checkpoint'))
assert [r['step'] for r in rr if r['stage']=='epoch_end']==list(range(39,3901,39))
lim=q['resources']
peaks=[]
for r in rr:
    assert 0<=r['used_MiB']<=lim['device_used_MiB'] and 0<=r['rss_bytes']<=lim['rss_bytes']
    assert r['disk_free_bytes']>=lim['minimum_disk_bytes'] and 0<=r['output_bytes']<=lim['output_bytes']
    if 'peak_reserved' in r:
        assert 0<=r['peak_allocated']<=r['peak_reserved']<=lim['torch_peak_bytes']
        peaks.append(r['peak_reserved'])
assert peaks and rr[-1]['stage']=='after_checkpoint'
assert rr[0]['stage']=='initial' and rr[0]['disk_free_bytes']>=q['minimum_free_bytes_prelaunch']
g=rows(o/'OASG_geometry.jsonl')
assert [r['step'] for r in g]==[1,39,390,1950,3900]
for r in g:
    assert r['frame']=='D-only normalized'
    for key,size in (('center',3),('minimum',3),('maximum',3),('anchor_displacement_p50_p95',2)):
        m=r['geometry'][key]
        assert len(m)==8 and all(len(x)==size and all(math.isfinite(v) for v in x) for x in m)
    assert all(math.isfinite(v) and v>=0 for v in r['losses'].values())
emit(dict(resource_records=len(rr),resource_stages=st,max_reserved=max(peaks),geometry_steps=[r['step'] for r in g]))
""",
}


def canonical(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(stage):
    source = SOURCE[stage].encode("ascii")
    compile(source, stage, "exec")
    packed = base64.b64encode(zlib.compress(source, 9)).decode("ascii")
    cmd = (
        "/usr/bin/timeout --kill-after=2s 20s /usr/bin/python3 -IBc "
        f"'import base64,zlib;exec(zlib.decompress(base64.b64decode(\"{packed}\")))'"
    )
    if len(cmd.encode("ascii")) > 2048:
        raise ValueError((stage, len(cmd)))
    return cmd


def remote(stage, label):
    started = time.monotonic()
    cmd = command(stage)
    args = [
        "wsl.exe", "-d", "Ubuntu-20.04", "--exec", "/home/zhj/.local/bin/hpc5000",
        "exec", "--timeout", "24", "--", cmd,
    ]
    r = subprocess.run(args, capture_output=True, timeout=30, check=False)
    (DEST / f"{label}_stdout.bin").write_bytes(r.stdout)
    (DEST / f"{label}_stderr.bin").write_bytes(r.stderr)
    output = r.stdout.decode("utf-8", "replace").splitlines()
    hits = [line[6:] for line in output if line.startswith("AUDIT ")]
    if r.returncode or len(hits) != 1:
        raise RuntimeError((label, r.returncode, output))
    print(f"{label}: {len(cmd)} bytes, {time.monotonic() - started:.2f}s", flush=True)
    return json.loads(hits[0])


def read_json(path):
    return json.loads(path.read_bytes())


def reference(arm, record_hash, q):
    directory = ROOT / f"p2_{arm.lower()}_d_post_training_freeze_v1"
    path = directory / f"{arm}_D_formal_post_training_freeze_receipt_v1.json"
    assert sha(path) == record_hash
    r = read_json(path)
    hashes = {Path(filename).name: digest for filename, digest in r["artifact_hashes"].items()}
    names = ("order_plan.json", "metrics.jsonl", "exposure.json", "model_construction.json",
             "initialization.json", "optimizer_actual_defaults.json", "optimizer_parameter_groups.json")
    local = directory / "readback"
    for n in names:
        assert sha(local / n) == hashes[n], (arm, n)
    construct = read_json(local / "model_construction.json")
    init = read_json(local / "initialization.json")
    assert init == r["initialization"] and init["seed"] == q["run"]["seed"]
    assert construct["starting_rng"] == r["starting_rng"] == q["starting_rng"]
    assert construct["shared_initial_sha256"] == r["shared_initial_sha256"] == q["shared_initial_sha256"]
    assert r["complete_order"]["verified_batches"] == 3900
    assert r["identity"] == q["identity"]
    keys = "step epoch batch case_ids source_ids LR BN_momentum clip_max_norm optimizer_step_committed".split()
    metrics = list(map(json.loads, (local / "metrics.jsonl").read_bytes().splitlines()))
    assert len(metrics) == 3900 and all(m["optimizer_step_committed"] is True for m in metrics)
    projection = canonical([[m[k] for k in keys] for m in metrics])
    return r, hashes, projection, record_hash


def audit():
    preparation = ROOT / "p2_i_d_preparation_v1"
    req = preparation / REQ
    assert sha(req) == SHA
    q = read_json(req)
    r, u = (reference("R", q["reference_receipt"]["sha256"], q),
            reference("U", q["uniform_receipt"]["sha256"], q))
    before = remote("inventory", "inventory_before")
    identity = remote("identity", "identity")
    trace = remote("trace", "trace")
    geom = remote("resources", "resources")
    assert before == remote("inventory", "inventory_after"), "artifacts changed while reading"
    outputs, controls = before["outputs"], before["controls"]
    assert set(outputs) == set(
        "ckpt-last.pth completion.json exit_code.txt exposure.json initialization.json launcher.pid launch.log "
        "metrics.jsonl model_construction.json OASG_geometry.jsonl optimizer_actual_defaults.json "
        "optimizer_parameter_groups.json order_plan.json p3_resources.jsonl worker.pid".split()
    )
    assert set(controls) == {REQ, "authorization_v1.json", "runtime_v1.json", "cisc_train_i_d_v1.py",
                             "launch_cisc_i_d_once_v1.sh", "U_D_formal_post_training_freeze_receipt_v1.json"}
    for n in set(controls) - {"authorization_v1.json", "runtime_v1.json"}:
        path = preparation / n
        assert controls[n] == [path.stat().st_size, sha(path)], n
    assert identity["authorization_request"] == SHA
    assert identity["runtime"] == dict(request_sha256=SHA, authorization_sha256=controls["authorization_v1.json"][1])
    values = identity["values"]
    c, ini, model = (values["completion.json"], values["initialization.json"], values["model_construction.json"])
    assert c["scq_prime_run_identity"] == model["run_identity"] == q["run"]
    assert c["optimizer_updates"] == 3900 and c["traversals"] == 100 and c["case_exposures"] == 31200
    assert c["counts"] == dict(forward=3900, backward=3900, clip=3900, step=3900, lr_scheduler=100, bn_scheduler=100)
    assert all(c[k] is False for k in ("bncal_executed", "evaluation_executed", "resume"))
    ckpt = outputs["ckpt-last.pth"]
    assert ckpt[0] > 0 and ckpt[1] == c["checkpoint_sha256"]
    assert model["shared_initial_sha256"] == q["shared_initial_sha256"]
    assert model["starting_rng"] == q["starting_rng"]
    assert model["uniform_initial_sha256"] == u[0]["uniform_initial_sha256"] == q["uniform_initial_sha256"]
    assert ini == u[0]["initialization"]
    assert model["total_parameters"] == 39968069 and model["carrier"] == "spatial_mass_field"
    assert model["labels_sha256_verified"] == 315 and model["auxiliary_loss_weight"] == 0.05
    assert trace["batch_count"] == trace["loss_decomposition_steps"] == 3900
    assert trace["canonical_order"] == c["order_sha256"] == ini["order_sha256"]
    assert outputs["order_plan.json"][1] == identity["order_file"] == q["order"]["sha256"]
    assert (trace["case_count"], trace["source_count"], trace["exposed"], trace["dropped"]) == (315, 63, 31200, 300)
    for baseline, files, projection, _ in (r, u):
        assert baseline["complete_order"]["canonical_sha256"] == trace["canonical_order"]
        assert baseline["counts"] == dict(updates=3900, epochs=100, cases=315, sources=63, exposures=31200, dropped=300)
        assert projection == trace["trajectory_sha256"]
        for n in ("order_plan.json", "exposure.json", "optimizer_actual_defaults.json"):
            assert outputs[n][1] == files[n], n
    assert outputs["optimizer_parameter_groups.json"][1] == u[1]["optimizer_parameter_groups.json"]
    receipt = dict(
        status="FORMAL_CISC_I_D_POST_TRAINING_FREEZE_AND_THREE_ARM_PAIRED_AUDIT_PASS",
        request_sha256=SHA, identity=q["identity"], run=q["run"],
        common_contract_sha256=q["common_contract"]["sha256"],
        reference_audit_sha256=r[3], uniform_audit_sha256=u[3],
        checkpoint=dict(path=q["output"] + "/ckpt-last.pth", bytes=ckpt[0], sha256=ckpt[1], server_reads=2),
        outputs={k:dict(bytes=v[0],sha256=v[1]) for k,v in outputs.items()},
        controls={k:dict(bytes=v[0],sha256=v[1]) for k,v in controls.items()},
        output_directories=before["dirs"], completion=c, model_construction=model, initialization=ini,
        paired=dict(shared_initial_R_U_I=True, full_initial_U_I=True, starting_RNG_R_U_I=True,
                    exact_order_bytes_R_U_I=True, complete_observed_batch_trajectory_R_U_I=True,
                    exact_exposure_file_R_U_I=True),
        counts=trace, resources=geom, exit_code=0, stable_readback=True, server_modified=False,
        checkpoint_deserialized=False, subsequent_run_authorized=False,
    )
    with (DEST / "I_D_formal_post_training_freeze_receipt_v1.json").open("x", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")
    print(json.dumps(dict(status=receipt["status"], checkpoint=receipt["checkpoint"],
                          counts=trace, resources=geom)), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--read-only-audit", action="store_true")
    args = parser.parse_args()
    for stage in SOURCE:
        print(stage, len(command(stage)))
    if args.read_only_audit:
        audit()
