import pathlib,json,hashlib,itertools,socket
assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0"
P=pathlib.Path;base=P("/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba");s=base/"SCQ_RIVE_Static_foldC_seed0_train_20261115_v1";r=base/"SCQ_RIVE_Requery_foldC_seed0_train_20261115_v1"
identical=[]
for n in ("initialization.json","order_plan.json","exposure.json","optimizer_actual_defaults.json","optimizer_parameter_groups.json"):
 assert (s/n).read_bytes()==(r/n).read_bytes(),n;identical.append(n)
load=lambda p:json.loads(p.read_bytes())
si=load(s/"run_identity.json");ri=load(r/"run_identity.json");assert si["arm"]=="RF-Static" and ri["arm"]=="RF-Requery"
for k in si:
 if k not in ("arm","variant"):assert si[k]==ri[k],k
sm=load(s/"model_construction.json");rm=load(r/"model_construction.json");assert sm["common_initial_state_SHA256"]==rm["common_initial_state_SHA256"]
assert sm["factory"]["parent"]==rm["factory"]["parent"] and sm["new_optimizer_groups"]==rm["new_optimizer_groups"]
for k in sm["factory"]["rf"]:
 if k!="variant":assert sm["factory"]["rf"][k]==rm["factory"]["rf"][k],k
n=0
with (s/"metrics.jsonl").open() as a,(r/"metrics.jsonl").open() as b:
 for x,y in itertools.zip_longest(a,b):
  assert x is not None and y is not None;x=json.loads(x);y=json.loads(y);n+=1
  for k in ("step","epoch","batch","case_ids","source_ids","LR","BN_momentum","clip_max_norm","optimizer_step_committed"):assert x[k]==y[k],(n,k)
assert n==3900
print(json.dumps(dict(status="STATIC_REQUERY_C_FULL_PAIRING_PASS",exact_identical_files=identical,all3900actual_batches_and_schedules_identical=True,same_full_initial_state=True,same_common_factory=True,RF_factory_only_variant_differs=True,same_effective_resources=True,case_exposures_identical=True)))
