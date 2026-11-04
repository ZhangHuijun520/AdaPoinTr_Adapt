"""Summarize existing transport/install/start receipts locally; no server calls."""
import hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2';A=O/'authorized_execution_v1'
def load(n):return json.loads((A/n).read_bytes())
def last(text):
    rows=[]
    for line in (text or '').splitlines():
        try:rows.append(json.loads(line))
        except ValueError:pass
    return rows[-1] if rows else None
q=json.loads((O/'Euclidean_training_execution_request_v1.json').read_bytes())
installation=load('install_execute_once_observation.json');launch=load('materialize_execute_once_observation.json');v=load('startup_observation_v1.json')
assert installation['status']=='INSTALLATION_650_HASH_PASS' and v['tmux_present'] and v['worker_live'] and v['failure'] is None and v['startup_failure'] is None and v['exit_code'] is None
metric=last(v['metrics_tail']);resource=last(v['resource_tail'])
assert metric['step']>0 and metric['optimizer_step_committed'] and resource['resource_guard_passed']
record={'status':'SINGLE_AUTHORIZED_EUCLIDEAN_TRAINING_RUNNING','scope_sha256':hashlib.sha256((O/'Euclidean_training_execution_request_v1.json').read_bytes()).hexdigest(),'run_id':q['run_id'],'installed_files':650,'tmux':q['future_paths']['tmux'],'worker_PID':v['worker_pid'].strip(),'observed_committed_update':metric['step'],'target_updates':3900,'current_loss':metric['loss'],'resource_observation':resource,'authorization_SHA256':launch['authorization_sha256'],'runtime_SHA256':launch['runtime_sha256'],'launcher_SHA256':launch['launcher_sha256'],'graph_training_started':False,'training_completion_claimed':False,'BNCal_evaluation_started':False,'boundary':'Startup observation only; final count/checkpoint SHA256 require separate post-training freeze audit'}
with (A/'execution_start_report_v1.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
report=f'''# 欧氏／表面图采样对照：欧氏臂授权执行启动记录\n\n2026-11-04，状态：训练运行中。用户原文“已上传，按既定边界单独授权上述完整哈希。”解析为scope SHA256 `{record['scope_sha256']}`。\n\n5个上传文件核验通过，650目标在写入前全部不存在；不覆盖安装完成并逐文件核验哈希。随后按授权→runtime→launcher单向顺序材料化，创建单次claim后仅调用一次tmux。固定会话：`{record['tmux']}`，worker PID `{record['worker_PID']}`。\n\n启动后只读观察显示已提交{metric['step']}/3900次更新，tmux和worker存活，未见退出码、completion或失败文件。显存SMI {resource['device_MiB']}MiB，Torch峰值allocated {resource['peak_allocated']/1024**3:.2f}GiB，RSS {resource['RSS']/1024**3:.2f}GiB，记录的资源断言通过。SMI/容器PID不同仍按既定diagnostic-only合同记录，不新增PID所有权阻断。\n\n仍为FoldC、seed0、8k→8k、63来源315病例、100遍历、3900更新、31200曝光和300丢弃；本轮未启动图距离臂、开发评价、BNCal或其他实验。后续按独立只读训练后审计核验最终计数、初始化、批次与checkpoint SHA256；本记录不代替该审计。\n\n调用过程的本机静态换行检查先误写9行而实际为8行，修正断言后完成静态检查；该阶段未连接服务器或消耗训练attempt。真正的三个服务器执行阶段均仅执行一次且返回通过。\n\n服务器输出：`{q['future_paths']['output']}`。\n'''
with (A/'execution_start_report_zh_v1.md').open('x',encoding='utf-8') as f:f.write(report)
manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in A.iterdir() if p.is_file()}
with (A/'execution_start_artifact_manifest_v1.json').open('x') as f:json.dump(manifest,f,indent=2)
print(json.dumps({'status':record['status'],'observed_committed_update':metric['step'],'target':3900,'installed_files':650}))
