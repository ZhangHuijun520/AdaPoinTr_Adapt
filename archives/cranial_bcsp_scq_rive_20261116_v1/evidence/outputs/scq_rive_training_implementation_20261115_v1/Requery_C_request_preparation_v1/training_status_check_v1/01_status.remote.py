import pathlib,json,socket,os,subprocess
P=pathlib.Path;assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==1000
run="SCQ_RIVE_Requery_foldC_seed0_train_20261115_v1";out=P("/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba")/run
r=dict(hostname=socket.gethostname(),tmux_live=subprocess.run(["tmux","has-session","-t","="+run],capture_output=True).returncode==0,output_exists=out.is_dir())
for name in ("exit_code.txt","worker.pid","completion.json","failure.json","startup_failure.json","startup_monitor_failure.json"):
 p=out/name
 if p.is_file():
  assert p.stat().st_size<=65536
  text=p.read_text();r[name]=json.loads(text) if name.endswith("json") else text.strip()
if "worker.pid" in r:r["worker_pid_visible"]=P("/proc/"+r["worker.pid"]).exists()
p=out/"metrics.jsonl";count=0;last=None
if p.is_file():
 with p.open() as f:
  for line in f:
   try:last=json.loads(line);count+=1
   except json.JSONDecodeError:pass
r["metric_records"]=count;r["last_metric"]=last
p=out/"ckpt-last.pth"
r["checkpoint_exists"]=p.is_file()
if p.is_file():r["checkpoint_bytes"]=p.stat().st_size
p=out/"launch.log"
if p.is_file():
 with p.open("rb") as f:f.seek(max(0,p.stat().st_size-3000));r["log_tail"]=f.read().decode("utf-8",errors="replace")
print(json.dumps(r))