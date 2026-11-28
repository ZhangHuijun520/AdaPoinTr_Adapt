
from pathlib import Path
from collections import Counter
import hashlib,json,math,statistics
import numpy as np

root=Path("outputs/bcsp_ejtc_20261127_v2/p1_cuda_preparation_v1")
a=root/"post_cuda_freeze_audit_h7vvrr_v1"
t=root/"transport_h7vvrr_v1"
req=root/"server_readonly_h7vvrr_v1/EJTC_P1_CUDA_execution_request_h7vvrr_v1.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def obj(p):return json.loads(p.read_bytes())
def close(x,y):return math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-12)
q=obj(req); rid=sha(req)
assert rid=="1cb96ed253b91cf9248b768934da3f8e48276ca160aa74d9efa8fcb76e4b8a80"
m=t/"EJTC_P1_CUDA_h7vvrr_install_mapping_v1.json"
mapping=obj(m)
assert sha(m)=="43ccb0e4656ad30727f1b5ac624fee600783dda69988505db7c5dc92e372c8d9"
invent=obj(a/"remote_inventory_before.json")
assert invent==obj(a/"remote_inventory_after.json") and invent["host"]==q["identity"]["hostname"] and invent["uid"]==1000
assert invent["worker_absent"] and invent["session_absent"]
controls={"authorization_v1.json","runtime_v1.json","single_attempt.log","exit_code.txt"}
outfiles={"completion.json","events.jsonl"}
installed={r[0]:r[1:] for r in invent["installed"] if len(r)==3}
output={r[0]:r[1:] for r in invent["output"] if len(r)==3}
expected={r["member"]:[r["bytes"],r["sha256"]] for r in mapping["files"]}
assert len(expected)==43 and set(installed)==set(expected)|controls
assert all(installed[p]==v for p,v in expected.items())
assert set(output)==outfiles
assert {r[0] for r in invent["installed"] if len(r)==2}=={"labels"}
assert {r[0] for r in invent["output"] if len(r)==2}=={"TMPDIR","XDG_CACHE_HOME","MPLCONFIGDIR","TRITON_CACHE_DIR","HF_HOME"}
for f in controls|outfiles:
 assert [(a/f).stat().st_size,sha(a/f)]==(installed|output)[f]
assert (a/"exit_code.txt").read_bytes().strip()==b"0"
auth=obj(a/"authorization_v1.json");runtime=obj(a/"runtime_v1.json")
claim=obj(t/"cuda_launch_claim_v1.json")
launch=obj(t/"cuda_launch_attempt_v1.json")
assert claim==dict(request_sha256=rid,authorization_sha256=sha(a/"authorization_v1.json"),runtime_sha256=sha(a/"runtime_v1.json"),attempts=1)
assert auth["request_sha256"]==rid and auth["explicit_user_authorization"] is True
assert runtime==dict(schema="bcsp-development-runtime-v1",request_sha256=rid,authorization_sha256=claim["authorization_sha256"])
assert launch["returncode"]==0 and json.loads(launch["stdout"])["started"]
done=obj(a/"completion.json")
assert done["status"]=="P1_CUDA_CONTRACT_PASS" and done["request_sha256"]==rid
events=[json.loads(line) for line in (a/"events.jsonl").read_bytes().splitlines()]
by={}
for e in events:
 by.setdefault(e["event"],[]).append(e)
assert set(by)=={"resources","attempt","restoration","timing","calibration","native","model_state","initial_resources","equivalence","lambda"}
for i,(attempt,expected_row) in enumerate(zip(by["attempt"],q["schedule"]),1):
 assert attempt==dict(event="attempt",index=i,**expected_row)
assert len(by["attempt"])==len(q["schedule"])==53
assert Counter(r["phase"] for r in by["attempt"])=={"equivalence":1,"calibration":10,"timing":39,"native":3}
assert [r["index"] for r in by["restoration"]]==list(range(1,54))
assert all(r["buffers_flags_grad_restored"] is True and r["rng_restored"] is True for r in by["restoration"])
equiv,=by["equivalence"]
assert equiv["loss_abs"]<=1e-7 and equiv["grad_abs"]<=1e-7
state_h,state_i=by["model_state"]
assert state_h["state"]=="historical" and state_i["state"]=="initial"
assert done["initial_state"]==done["restored_state"]==state_i["sha256"]!=state_h["sha256"]
assert [(n["index"],n["arm"]) for n in by["native"]]==[(51,"R"),(52,"T"),(53,"J")]
trace=by["native"][0]["trace"]
assert all(n["trace"]==trace for n in by["native"])
assert trace["ssm_calls"]==36 and trace["monitored_attention_calls"]==0

prep=obj(root/"local_preparation_v1.json")
labels={}
for cid,value in prep["inputs"].items():
 f=Path(value["local_label_path"])
 assert sha(f)==q["inputs"][cid]["labels"]["sha256"]
 with np.load(f,allow_pickle=False) as z:
  labels[cid]=z["labels_G"].astype(bool)

cal=by["calibration"]
assert [(c["state"],c["batch"]) for c in cal]==[(state,b) for state in ("initial","historical") for b in q["batches"]]
init=[o for c in cal[:5] for o in c["arms"].values()]
max_v=max(o["value_ratio"] for o in init)
max_g=max(o["ratios"]["P"] for o in init)
lam=min(.1,.2/max_v,.25/max_g)
assert lam==done["lambda_value"] and lam>=.001
lambda_row,=by["lambda"]
assert lambda_row["lambda_value"]==lam
checks={"lambda_floor": True}
hist_tv=[]
types=set()
weighted={}
for state,section,cap_v,cap_p,cap_other in (("initial",cal[:5],.20,.25,.50),("historical",cal[5:],.40,.50,1.0)):
 for arm in "TJ":
  values=[];ratios=[]
  for row in section:
   o=row["arms"][arm]
   assert math.isfinite(row["base_loss"]) and row["base_loss"]>0
   assert float(np.float32(o["aux"])/np.float32(row["base_loss"]))==o["value_ratio"]
   assert set(o["gradients"])==set(o["ratios"])=={"P","Q","Encoder","OASG","LQI","FC"}
   for part,g in o["gradients"].items():
    na,nb,dot=g["base"],g["aux"],g["dot"]
    assert na>0 and nb>0 and all(map(math.isfinite,g.values()))
    assert abs(g["cosine"])<=1+1e-10 and close(g["cosine"],dot/na/nb)
    assert close(g["ratio"],nb/na) and g["ratio"]==o["ratios"][part]
    assert close(g["combined"],math.sqrt(max(0,na**2+(lam*nb)**2+2*lam*dot)))
   values.append(lam*o["value_ratio"])
   ratios.append({n:lam*r for n,r in o["ratios"].items()})
  p=[x["P"] for x in ratios]
  other=[v for x in ratios for n,v in x.items() if n!="P"]
  weighted[state+"_"+arm]={"max_value":max(values),"max_P":max(p),"median_P":statistics.median(p),"max_Q_or_parameter":max(other)}
  checks[state+"_"+arm+"_values"]=max(values)<=cap_v+1e-6
  checks[state+"_"+arm+"_P"]=max(p)<=cap_p+1e-6
  checks[state+"_"+arm+"_Q_and_parameters"]=max(other)<=cap_other+1e-6
  if state=="initial": checks[state+"_"+arm+"_median"]=statistics.median(p)>=.01-1e-6
 for row in section:
  assert [v["case_id"] for v in row["manipulation"]]==row["batch"]
  for rec in row["manipulation"]:
   cid=rec["case_id"];j=labels[cid]
   T,E,J=(np.array(rec[k],dtype=int) for k in ("T","E","J"))
   assert all(len(x)==len(set(x)) and np.all((x>=0)&(x<8192)) for x in (T,E,J))
   n_j=int(j.sum())
   assert len(T)==820 and len(E)==(8192-n_j+9)//10 and len(J)==(n_j+9)//10
   assert not j[E].any() and j[J].all()
   wt=np.zeros(8192);wj=np.zeros(8192)
   wt[T]=1/len(T);wj[E]=.5/len(E);wj[J]=.5/len(J)
   tv=.5*np.abs(wj-wt).sum()
   assert close(tv,rec["TV"]) and close(wt[j].sum(),rec["T_J_mass"]) and close(wj[j].sum(),rec["J_J_mass"])
   if state=="historical":
    hist_tv.append(tv)
    if tv>=.10:types.add(cid.split("__")[-1])
checks["TV_count"]=len(hist_tv)==40 and int(sum(x>=.10 for x in hist_tv))>=32
checks["TV_each_type"]=types=={"bilateral","frontoorbital","parietotemporal","random_1","random_2"}
assert checks==lambda_row["gates"]==done["gates"] and all(checks.values())

times={a:[] for a in "RTJ"}
allocated={a:[] for a in "RTJ"};reserved={a:[] for a in "RTJ"}
for v,row in zip(by["timing"],q["schedule"][11:50]):
 assert v["event"]=="timing" and v["index"]==12+sum(len(x) for x in allocated.values())
 assert v["arm"]==row["arm"] and v["warmup"]==row["warmup"]
 assert v["allocated"]>0 and v["reserved"]>=v["allocated"] and v["ms"]>0 and math.isfinite(v["loss"])
 allocated[v["arm"]].append(v["allocated"])
 reserved[v["arm"]].append(v["reserved"])
 if not v["warmup"]:times[v["arm"]].append(v["ms"])
assert len(by["timing"])==39 and all(len(v)==10 for v in times.values())
# Independent operation recount from the journal phase/arm schedule and the frozen worker call sites.
counts=dict(forward=len(by["attempt"]),base_loss=2+len(cal)+len(by["timing"]),
 auxiliary=2*len(cal)+sum(r["arm"]!="R" for r in by["timing"]),
 autograd_grad=2+3*len(cal),backward=len(by["timing"]),optimizer_steps=0)
assert counts==done["counts"]==q["counts"]
p50={k:statistics.median(v) for k,v in times.items()}
p95={k:float(np.quantile(v,.95)) for k,v in times.items()}
peaks={k:max(v) for k,v in allocated.items()}
assert p50==done["p50_ms"] and peaks==done["peak_allocated"] and all(close(p95[k],done["p95_ms"][k]) for k in p95)
rg={z:p50[z]/p50["R"]<=1.5 and peaks[z]/peaks["R"]<=1.25 for z in "TJ"}
assert all(rg.values()) and rg==done["resource_gates"]
resources=by["initial_resources"]+by["resources"]
lim=q["resources"]
assert all(r["used_MiB"]<=lim["device_used_MiB"] and r["rss_bytes"]<=lim["rss_bytes"] and
 r["disk_free_bytes"]>=lim["minimum_disk_bytes"] and r["output_bytes"]<=lim["output_bytes"] for r in resources)
assert max(r["used_MiB"] for r in resources)==done["max_sampled_SMI_MiB"]
assert max(peaks.values())<=lim["torch_peak_bytes"]
floor=sum(p50.values())*3900/1000
assert close(floor,done["model_only_floor_seconds"])
result={
 "status":"EJTC_P1_FORMAL_READ_ONLY_FREEZE_AUDIT_PASS",
 "d1_status":"P1_PASS_D1_PREPARATION_READY",
 "d1_start_status":"PENDING_COMPLETE_GROUP_BUDGET_AND_TRAINING_REQUEST",
 "request_sha256":rid,"mapping_sha256":sha(m),"hostname":invent["host"],
 "readback_sha256":{f:sha(a/f) for f in sorted(controls|outfiles)},
 "stable_remote_inventories_sha256":sha(a/"remote_inventory_before.json"),
 "verified_installed_files":43,"verified_operational_controls":4,
 "counts":counts,"numeric_equivalence":equiv,"lambda":lam,"calibration_max_raw":{"value_ratio":max_v,"P_gradient_ratio":max_g},
 "weighted_gradients_summary":weighted,"calibration_gates":checks,
 "historical_TV_count":len(hist_tv),"historical_TV_at_least_point1":int(sum(x>=.10 for x in hist_tv)),
 "historical_TV_min":float(min(hist_tv)),"historical_TV_max":float(max(hist_tv)),
 "p50_ms":p50,"p95_ms":p95,"peak_allocated_bytes":peaks,
 "peak_reserved_bytes":{k:max(v) for k,v in reserved.items()},
 "max_sampled_SMI_MiB":done["max_sampled_SMI_MiB"],"resource_samples":len(resources),
 "resource_gates":rg,"model_only_floor_seconds":floor,"model_only_with_25pct_seconds":floor*1.25,
 "state":{"initial_and_restored_sha256":state_i["sha256"],"historical_sha256":state_h["sha256"],
          "per_call_RNG_and_buffer_flags_verified_from_journal":53,"native_trace":trace},
 "limits":["Counter reconstruction matches logged attempts and frozen call sites. There is no raw CUDA trace.",
           "Restoration evidence consists of recorded per-call assertions and state hashes.",
           "Timing covers forward/loss/backward. Optimizer, real input pipeline, final saves and scoring are outside this estimate.",
           "GPU availability for a separate full D1 group remains to be confirmed."],
 "server_writes":0,"new_model_calls":0,"training_started":False
}
result_bytes=json.dumps(result,indent=2,allow_nan=False)+"\n"
with (a/"formal_post_cuda_freeze_audit_v1.json").open("x",encoding="utf-8") as f:f.write(result_bytes)
assert obj(a/"formal_post_cuda_freeze_audit_v1.json")==result
print(json.dumps({k:result[k] for k in ("status","d1_status","lambda","historical_TV_at_least_point1","historical_TV_min","calibration_max_raw","p50_ms","peak_reserved_bytes","model_only_with_25pct_seconds")}))

