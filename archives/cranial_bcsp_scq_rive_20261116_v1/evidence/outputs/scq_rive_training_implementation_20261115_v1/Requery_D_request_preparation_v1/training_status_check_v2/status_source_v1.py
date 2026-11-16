import pathlib, json, socket, subprocess, os
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
run = 'SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1'
out = P('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba') / run
r = dict(status='READONLY_STARTUP_OBSERVATION', session_live=subprocess.run(['tmux', 'has-session', '-t', '=' + run], capture_output=True).returncode == 0, output_exists=out.is_dir())
if out.is_dir():
    r['files'] = sorted((x.name for x in out.iterdir()))
    for name in ('worker.pid', 'exit_code.txt', 'failure.json', 'startup_failure.json', 'startup_monitor_failure.json', 'completion.json'):
        p = out / name
        if p.is_file():
            r[name] = p.read_text()[:12000]
    p = out / 'metrics.jsonl'
    if p.is_file():
        lines = p.read_text().splitlines()
        r['metric_records'] = len(lines)
        if lines:
            try:
                r['last_metric'] = json.loads(lines[-1])
            except json.JSONDecodeError:
                r['last_metric_incomplete'] = True
    p = out / 'launch.log'
    if p.is_file():
        with p.open('rb') as f:
            f.seek(max(0, p.stat().st_size - 6000))
            r['log_tail'] = f.read().decode('utf-8', errors='replace')
    if 'worker.pid' in r:
        pid = int(r['worker.pid'].strip())
        r['worker_visible'] = P('/proc/' + str(pid)).exists()
print(json.dumps(r))
