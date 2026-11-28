
"""Freeze local EJTC P1 schedule, input bindings and targeted CPU evidence."""
from pathlib import Path, PurePosixPath
from collections import Counter
from types import SimpleNamespace
import hashlib
import importlib.util
import json

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GEO = ROOT / "outputs/cranial_bcsp_geov1_20261024"
OASG = ROOT / "outputs/bcsp_oasg_20261124_v1"
RBSS = ROOT / "outputs/bcsp_rbss_20261126_v2"
OUT = HERE / "p1_cuda_preparation_v1"
DATA = GEO / "real_data_qc_v1"
CPU = HERE / "p1_cpu_numeric_v1/cpu_numeric_gradient_receipt_v1.json"
FULL = HERE / "p0b_full315_v1/full_result.json"
PARENT = OASG / "p3_a_d_v1/OASG_A_D_training_execution_request_v1.json"
PARENT_SHA = "ad34d559e1c0604fe065d24d32077e78d95c4e99314007eb81dbaa7e11d38fa6"


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(4194304),b""):
            h.update(b)
    return h.hexdigest()


def bind(path, remote=None):
    return {"path":str(path) if remote is None else remote,"bytes":path.stat().st_size,"sha256":sha(path)}


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    worker_path=HERE/"ejtc_p1_cuda_v1.py"
    candidate_path=HERE/"ejtc_loss_cpu_candidate_v1.py"
    worker=module("worker",worker_path)
    candidate=module("candidate",candidate_path)
    cpu=load(CPU)
    assert sha(CPU)=="50edb44f22f64de2c5165817d1d21b482cf1f85f5b2a64fd07034b4fe0294678"
    assert cpu["status"]=="P1_CPU_CONTRACT_PASS" and cpu["candidate_sha256"]==sha(candidate_path)
    full=load(FULL)
    assert sha(FULL)=="fad524497af55dc53ae74253ca37002447d606ea5a9186ecfb6a2cd15dd53255"
    assert full["status"]=="P0B_FULL315_PASS" and full["verified_cases"]==315
    lm=FULL.parent/"label_manifest_v1.json"
    assert full["label_manifest_sha256"]==sha(lm)
    labels={r["case_id"]:r for r in load(lm)["cases"]}
    assert len(labels)==315
    assert sha(PARENT)==PARENT_SHA
    parent=load(PARENT)
    fold=GEO/"consolidated_binding_v1/fold_binding.json"
    points=DATA/"manifest_8192.jsonl"
    assert sha(fold)==parent["fold"]["sha256"] and sha(points)==parent["point_manifest"]["sha256"]
    ids=load(fold)["folds"]["D"]["train_case_ids"]
    assert set(ids)==set(labels)
    with points.open(encoding="utf-8") as f:
        all_points={r["case_id"]:r for r in map(json.loads,f) if r["case_id"] in labels}
    groups=[]
    used=set()
    for defect in worker.DEFECTS:
        g=[]
        for c in sorted(x for x in ids if x.endswith("__"+defect)):
            source=all_points[c]["source_id"]
            if source not in used:
                g.append(c)
                used.add(source)
            if len(g)==8:
                break
        assert len(g)==8
        groups.append(g)
    order=[c for group in zip(*groups) for c in group]
    batches=[order[i:i+8] for i in range(0,40,8)]
    s=worker.schedule(batches)
    assert worker.planned_counts(s)==worker.COUNTS
    assert Counter(r["phase"] for r in s)=={"equivalence":1,"calibration":10,"timing":39,"native":3}
    assert Counter(r["arm"] for r in s if r["phase"]=="timing" and not r["warmup"])=={"R":10,"T":10,"J":10}
    assert len(used)==len(order)==40
    inputs={}
    proposed=PurePosixPath(parent["project"])/"third_party/bcsp_ejtc_p1_20261127_v1"
    for cid in order:
        p=all_points[cid]
        lab=labels[cid]
        assert lab["source_id"]==p["source_id"] and p["target_array_sha256"]==lab["target_sha256"]
        cloud=bind(DATA/p["point_path"], str(PurePosixPath(parent["data_root"])/p["point_path"]))
        local=HERE/lab["label_path"]
        label=bind(local,str(proposed/"labels"/local.name))
        assert cloud["sha256"]==p["sha256"] and label["sha256"]==lab["label_sha256"]
        inputs[cid]=dict(points=cloud,labels=label,local_label_path=str(local),
                         target_sha256=lab["target_sha256"],source_id=p["source_id"],n_J=lab["n_J"])
    backup=Path("E:/ResearchBackups/AdaPoinTr/BCSP_OASG/2026-11-25_archive_v1/checkpoints")
    c=[r for r in load(backup/"checkpoint_verification_v1.json")["files"]
       if r["file"]=="OASG_A_D_seed2026112102_epoch99_step3900.pth"]
    assert len(c)==1
    ck=bind(backup/c[0]["file"],c[0]["path"])
    assert ck["sha256"]==c[0]["sha256"] and ck["bytes"]==c[0]["bytes"]
    rb=load(RBSS/"p1_v1/transport_h7vvrr_v2/RBSS_P1_CUDA_execution_request_h7vvrr_v1.json")
    for key,path in (("prefix",RBSS/"p0b_prefix16_v1/rbss_prefix16_v1.py"),
                     ("native_loader",OASG/"skullfix_prediction_v2/oasg_sf_native_v2.py")):
        b=rb["bindings"][key]
        assert bind(path,b["path"])==b
    bindings=dict(worker=bind(worker_path,str(proposed/worker_path.name)),
                  candidate=bind(candidate_path,str(proposed/candidate_path.name)),
                  parent=bind(PARENT,rb["binding"]["historical_request"]),
                  **{k:rb["bindings"][k] for k in ("prefix","native_loader")})

    # Run exact frozen minimum observer, original layer adapter and P/Q autograd on CPU.
    ch_path=ROOT/"outputs/cranial_scqr_v12_qa_github_publish_20261019/extensions/chamfer_dist/__init__.py"
    assert sha(ch_path)==cpu["source_sha256"][ch_path.relative_to(ROOT).as_posix()]
    ch=module("original",ch_path)
    assert ch.chamfer is None
    layer=ch.ChamferDistanceL1Directional()
    q=torch.tensor([[[0.,0.,0.],[10.,0.,0.]]],dtype=torch.float64,requires_grad=True)
    p=q+q.new_tensor([[[.01,.01,.01]]])
    line=torch.cat((torch.linspace(.12,.32,32,dtype=q.dtype),torch.linspace(10.5,10.8,32,dtype=q.dtype)))
    g=torch.stack((line,torch.ones_like(line)*.04,torch.zeros_like(line)),dim=-1).unsqueeze(0)
    lab=torch.arange(64).view(1,-1)>=32
    index=[]; values=[]
    orig=layer(p,g)
    snapshot=candidate.dense_loss_and_target_distances
    with worker.capture_dense_neighbors(torch,candidate,index):
        with worker.expose_target(ch,candidate,SimpleNamespace(fine_loss_func=layer),values):
            val=layer(p,g)
    assert candidate.dense_loss_and_target_distances is snapshot and "forward" not in vars(layer)
    torch.testing.assert_close(val,orig,atol=0,rtol=0)
    assert len(index)==len(values)==1 and index[0].tolist()==[[0]*32+[1]*32]
    aux=candidate.auxiliary(values[0],"J",lab)
    a=torch.autograd.grad(orig,(p,q))
    b=torch.autograd.grad(aux,(p,q))
    grads=worker.gradient_stats(torch,a,b,{"P":[0],"Q":[1]})
    assert all(x["ratio"]>0 and abs(x["cosine"])<=1.00000000001 for x in grads.values())
    novelty=worker.manipulation(torch,candidate,values[0],lab,["fixture"],index[0])[0]
    assert novelty["TV"]>=.10 and novelty["J_J_mass"]==.5

    def synthetic(hist_scale):
        return [dict(state=state, arms={arm:dict(value_ratio=.5,ratios={"P":1 if state=="initial" else hist_scale,
                           "Q":1,"Encoder":1,"OASG":1,"LQI":1,"FC":1}) for arm in "TJ"},
                     manipulation=[{"case_id":x,"TV":.2} for x in ba])
                for state in ("initial","historical") for ba in batches]
    lam,passed=worker.calibrate(synthetic(1))
    assert lam==.1 and all(passed.values())
    _,failed=worker.calibrate(synthetic(6))
    assert not failed["historical_T_P"] and not failed["historical_J_P"]
    root=PurePosixPath(parent["project"])
    receipt=dict(status="P1_CUDA_LOCAL_PREPARATION_PASS_AWAITING_SERVER_BINDING",
                 notes="Local bindings only. This document is not an execution request.",
                 initialization=list(worker.SEEDS), counts=worker.COUNTS,batches=batches,schedule=s,
                 inputs=inputs,checkpoint=ck,bindings=bindings,
                 references={k:bind(v) for k,v in dict(cpu=CPU,full=FULL,labels=lm,fold=fold,points=points).items()},
                 proposed_install_root=str(proposed),
                 proposed_output=str(root/"logs/cranial_bcsp_fullmamba/EJTC_P1_zero_update_20261127_v1"),
                 history_only_identity=rb["binding"]["identity"],history_only_interpreter=rb["binding"]["interpreter"],
                 cpu_integration=dict(torch=str(torch.__version__),checks=[
                     "exact 53/51/46/32/39/0 schedule","40 unique train-only identities",
                     "real frozen cdist min observer","forward restored after exposure",
                     "finite real path to P/Q","TV and nearest-neighbor load","lambda success and historical fail cases"],
                     fixture_gradients=grads,fixture_TV=novelty["TV"]),
                 server_contact=False,cuda_calls=0,optimizer_steps=0)
    OUT.mkdir(exist_ok=False)
    path=OUT/"local_preparation_v1.json"
    path.write_text(json.dumps(receipt,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    assert load(path)==receipt
    print(receipt["status"],sha(path),worker.COUNTS)


if __name__=="__main__":
    main()

