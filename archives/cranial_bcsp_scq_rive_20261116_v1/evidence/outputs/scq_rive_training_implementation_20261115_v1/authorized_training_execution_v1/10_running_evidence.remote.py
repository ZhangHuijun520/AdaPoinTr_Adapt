import pathlib,json,socket,os
P=pathlib.Path;assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==1000
out=P("/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Static_foldC_seed0_train_20261115_v1")
r={}
for name in ("initialization.json","run_identity.json","model_construction.json"):
 p=out/name;assert p.is_file() and p.stat().st_size<=2097152
 a=json.loads(p.read_bytes())
 if name=="model_construction.json":r[name]=dict(common=a["common_initial_state_SHA256"],arm=a["arm"],variant=a["variant"],rf=a["factory"]["rf"])
 else:r[name]=a
last=None;n=0
with (out/"resources.jsonl").open() as f:
 for line in f:
  try:last=json.loads(line);n+=1
  except json.JSONDecodeError:pass
r["resource_records_observed"]=n;r["latest_resource"]=last;r["failure_files_present"]=[x.name for x in out.iterdir() if x.name in ("failure.json","startup_failure.json","startup_monitor_failure.json")]
print(json.dumps(dict(status="READONLY_RUNNING_EVIDENCE",evidence=r)))
