
"""Read-only EJTC server readiness checks and local request freeze."""
from pathlib import Path, PurePosixPath
import base64
import hashlib
import json
import subprocess
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREP = HERE / "local_preparation_v1.json"
EXPECTED_PREP = "4025ee15e39232d1d52887c7a7f350797370e1ed7af6b04e30a61072fb7749df"
OUT = HERE / "server_readonly_h7vvrr_v1"
WSL = ["wsl.exe", "-d", "Ubuntu-20.04", "--exec", "/home/zhj/.local/bin/hpc5000"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(file, doc):
    with file.open("x", encoding="utf-8") as out:
        json.dump(doc, out, indent=2, ensure_ascii=False, allow_nan=False)
        out.write("\n")


def command(code):
    compile(code, "<read-only-probe>", "exec")
    payload = base64.b64encode(zlib.compress(code.encode(), 9)).decode()
    return ('/opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B -c '
            '"exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+payload+'\')))"')


def probe(code, tag):
    shell = command(code)
    assert len(shell.encode()) <= 2048
    p = subprocess.run(WSL + ["exec", "--timeout", "55", "--", shell],
                       timeout=70, capture_output=True)
    if p.returncode:
        save(OUT / (tag + "_failure.json"), {"returncode":p.returncode,
             "stdout":p.stdout.decode("utf-8", "replace")[-2000:]})
        raise RuntimeError(tag + " remote failure")
    value = json.loads(p.stdout)
    save(OUT / (tag + ".json"), value)
    return value


def main():
    assert sha(PREP) == EXPECTED_PREP
    prep = load(PREP)
    assert prep["status"] == "P1_CUDA_LOCAL_PREPARATION_PASS_AWAITING_SERVER_BINDING"
    parent_file = ROOT/"outputs/bcsp_oasg_20261124_v1/p3_a_d_v1/OASG_A_D_training_execution_request_v1.json"
    assert sha(parent_file) == prep["bindings"]["parent"]["sha256"]
    parent = load(parent_file)
    scope_file = ROOT/"deliverables/cranial_bcsp_fullmamba_20261112_v1/public_payload/support_sources/metadata/frozen_scope_v3.json"
    assert sha(scope_file) == parent["parent_scope"]["sha256"]
    sources = load(scope_file)["bindings"]
    targets = [prep["proposed_install_root"], prep["proposed_output"]]
    identity = prep["history_only_identity"]
    interpreter = prep["history_only_interpreter"]
    assert interpreter["path"] == identity["python_realpath"]
    output = PurePosixPath(targets[1])
    install = PurePosixPath(targets[0])
    ctrl = [str(install / name) for name in
            ("EJTC_P1_CUDA_execution_request_h7vvrr_v1.json", "authorization_v1.json", "runtime_v1.json")]
    loc = {}
    for record in prep["references"].values():
        p = Path(record["path"])
        assert p.stat().st_size == record["bytes"] and sha(p) == record["sha256"]
    for name in ("worker", "candidate"):
        record = prep["bindings"][name]
        p = HERE.parent / PurePosixPath(record["path"]).name
        assert p.stat().st_size == record["bytes"] and sha(p) == record["sha256"]
    inputs = {}
    for cid, record in prep["inputs"].items():
        p = Path(record["local_label_path"])
        assert p.stat().st_size == record["labels"]["bytes"] and sha(p) == record["labels"]["sha256"]
        assert PurePosixPath(record["labels"]["path"]).parent == install/"labels"
        inputs[cid] = {k:v for k,v in record.items() if k != "local_label_path"}
    assert len(inputs) == 40
    OUT.mkdir(exist_ok=False)
    general = f"""import json,os,socket,stat,sys,subprocess
from pathlib import Path
assert (socket.gethostname(),os.getuid())==({identity['hostname']!r},{identity['uid']})
"""
    resource = general + f"""p=Path(sys.executable)
def smi(field,compute=False):
 a=['/usr/bin/nvidia-smi','--id={identity['gpu_uuid']}',('--query-compute-apps=' if compute else '--query-gpu=')+field,'--format=csv,noheader,nounits']
 return subprocess.check_output(a,text=True,timeout=8).strip()
gpu=smi('uuid,name,driver_version,memory.total,memory.used,memory.free').split(',')
gpu=[v.strip() for v in gpu]
occupied=smi('pid',True)
targets={targets!r}
for t in targets:
 a=Path(t);assert a.parent.resolve(strict=True)==a.parent and a.parent.is_dir() and os.access(a.parent,os.W_OK|os.X_OK)
 assert not os.path.lexists(a)
v=os.statvfs('/home/jovyan')
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),python_realpath=str(p.resolve()),python_version=sys.version.split()[0],gpu=gpu,compute_pids=occupied,disk_free=v.f_bavail*v.f_frsize,
 targets=[dict(path=t,absent=True,parent=str(Path(t).parent),parent_writable=True) for t in targets])))
"""
    observation=probe(resource,"remote_identity_and_targets_v1")
    assert {k:observation[k] for k in ("hostname","uid","python_realpath","python_version")} == {
        k:identity[k] for k in ("hostname","uid","python_realpath","python_version")}
    assert observation["gpu"][:4]==[identity[k] for k in ("gpu_uuid","gpu_name","driver_version","total_MiB")]
    assert all(v["absent"] and v["parent_writable"] for v in observation["targets"])
    assert not observation["compute_pids"] and int(observation["gpu"][4])<=256
    assert int(observation["gpu"][5])>=20480 and observation["disk_free"]>=4294967296

    requested = {}
    def add(group, record):
        p=record["path"]
        value=(record["bytes"],record["sha256"])
        if p in requested:
            assert requested[p]["expected"] == list(value)
            requested[p]["groups"].append(group)
        else:
            requested[p]={"expected":list(value),"groups":[group]}

    for record in inputs.values():
        add("training_input",record["points"])
    add("historical_checkpoint",prep["checkpoint"])
    add("interpreter",interpreter)
    for k in ("parent","prefix","native_loader"):
        add("reuse",prep["bindings"][k])
    for k in ("p2_support","static_config","parent_scope","point_manifest","fold"):
        add("reuse",parent[k])
    for rec in parent["dependencies"] + parent["provider"] + list(parent["implementation"].values()):
        add("reuse",rec)
    for rec in sources["candidate"] + sources["isolated_model_project_sources"]:
        rel=rec.get("relative_target",rec.get("relative_path"))
        add("reuse",dict(rec,path=str(PurePosixPath(parent["model_root"])/rel)))
    add("reuse",dict(sources["base_config"],path=str(PurePosixPath(parent["model_root"])/"base_model.yaml")))
    code = general + """import hashlib
def read(name):
 p=Path(name)
 try:
  a=p.lstat()
 except FileNotFoundError:
  return [name,None,"missing"]
 assert p.resolve()==p and stat.S_ISREG(a.st_mode)
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 z=p.lstat()
 assert (z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)==(a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)
 return [name,a.st_size,h.hexdigest()]
"""
    def grouped(paths):
        return code + "print(json.dumps([read(p) for p in "+repr(paths)+"]))"
    groups=[]
    batch=[]
    for p in requested:
        if batch and (len(batch)==10 or len(command(grouped(batch+[p])))>2048):
            groups.append(batch)
            batch=[]
        batch.append(p)
    if batch:
        groups.append(batch)
    observed={}
    for idx,batch in enumerate(groups,1):
        actual=probe(grouped(batch),f"remote_files_{idx:02d}")
        assert [row[0] for row in actual]==batch
        observed.update({row[0]:row[1:] for row in actual})
        print("Checked",len(observed),"/",len(requested),flush=True)
    assert set(observed)==set(requested)
    mismatch=[]
    for p,e in requested.items():
        e["observed"]=observed[p]
        e["match"]=e["expected"]==e["observed"]
        if not e["match"]:
            mismatch.append(p)
    result=OUT/"server_readiness_receipt_v1.json"
    save(result,{"status":"EJTC_P1_SERVER_READY_READ_ONLY" if not mismatch else "EJTC_P1_SERVER_ASSET_HOLD",
         "identity":observation,"files":requested,"mismatches":mismatch,
         "verified_count":len(observed)-len(mismatch),"training_inputs":40,
         "local_sidecars_verified":40,"prep_sha256":EXPECTED_PREP,"server_writes":0,"cuda_model_calls":0})
    if mismatch:
        print("ASSET_HOLD",mismatch,flush=True)
        raise SystemExit(2)

    rb = load(ROOT/"outputs/bcsp_rbss_20261126_v2/p1_v1/transport_h7vvrr_v2/RBSS_P1_CUDA_execution_request_h7vvrr_v1.json")
    limits = rb["binding"]["resources"].copy()
    limits["device_used_MiB"] = int(identity["total_MiB"])*9//10
    request = {
        "schema":"bcsp-ejtc-p1-cuda-v1",
        "status":"AWAITING_EXPLICIT_USER_AUTHORIZATION","execution_authorized":False,
        "identity":identity,"interpreter":interpreter,"resources":limits,
        "initialization":prep["initialization"],"counts":prep["counts"],"batches":prep["batches"],
        "schedule":prep["schedule"],"inputs":inputs,"checkpoint":prep["checkpoint"],
        "bindings":prep["bindings"],"control_paths":ctrl,"output":str(output),
        "local_evidence":{"readiness_sha256":sha(result),"preparation_sha256":EXPECTED_PREP,
                          "cpu_numeric_sha256":prep["references"]["cpu"]["sha256"],
                          "full_labels_sha256":prep["references"]["labels"]["sha256"]},
        "policy":{"training":False,"maximum_attempts":1,"automatic_retry":False,
                  "install_overwrite":False,"development_data":False}
    }
    final=OUT/PurePosixPath(ctrl[0]).name
    save(final,request)
    assert final.stat().st_size<=262144 and load(final)==request
    print("READY",sha(final),final,flush=True)


if __name__=="__main__":
    main()

