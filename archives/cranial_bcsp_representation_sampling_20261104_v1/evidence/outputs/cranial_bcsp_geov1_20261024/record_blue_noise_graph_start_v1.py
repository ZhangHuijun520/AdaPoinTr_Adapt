"""Record existing graph startup evidence locally; no server calls."""
import hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;C=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2/graph_request_v2';A=C/'authorized_execution_v1'
def read(n):return json.loads((A/n).read_bytes())
def last(text):
    values=[]
    for line in text.splitlines():
        try:values.append(json.loads(line))
        except ValueError:pass
    return values[-1]
def dump(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
q=json.loads((C/'candidate_training_execution_request_v1.json').read_bytes());v=read('graph_start_observation_v1.json');pair=json.loads((C/'paired_initialization_receipt_v1.json').read_bytes())
assert read('install_execute_once_observation.json')['status']=='INSTALLATION_3_HASH_PASS'
assert v['tmux_present'] and v['worker_live'] and v['exit_code'] is None and v['failure'] is None and v['startup_failure'] is None
metric=last(v['metrics_tail']);resource=last(v['resource_tail']);init=json.loads(v['initialization'])
assert metric['optimizer_step_committed'] and metric['step']>0 and resource['resource_guard_passed']
assert all(init[k]==pair[k] for k in ('seed','parameter_sha256','persistent_state_sha256')) and init['order_sha256']==pair['order_canonical_sha256']
result={'status':'SINGLE_AUTHORIZED_GRAPH_TRAINING_RUNNING','scope_sha256':hashlib.sha256((C/'candidate_training_execution_request_v1.json').read_bytes()).hexdigest(),'run_id':q['run_id'],'new_control_files_installed':3,'reused_graph_files_rehashed':315,'observed_committed_update':metric['step'],'target_updates':3900,'initialization_record_matches_frozen_Euclidean':True,'initialization':init,'resource':resource,'worker_PID':v['worker_pid'].strip(),'tmux':q['future_paths']['tmux'],'completion_claimed':False,'BNCal_evaluation_started':False,'baseline_retrained':False,'launch_receipt':read('materialize_execute_once_observation.json')}
dump(A/'execution_start_report_v1.json',result)
report=f'''# Fold C 图距离臂：唯一一次授权训练启动记录

2026-11-04，训练运行中。用户原文“已上传，单独授权上述完整哈希”，解析为完整scope SHA256 `{result['scope_sha256']}`。

5个上传文件与3个新控制文件映射核验通过，315份图距离训练NPZ重新流式核验哈希；欧氏臂completion、initialization及checkpoint重新按冻结大小／哈希核验。3个新控制文件以不覆盖方式安装，未修改数据、生产源码、provider或欧氏结果。

按授权回执→其SHA256→runtime→launcher顺序材料化，创建一次claim后仅启动一次固定tmux。会话 `{result['tmux']}`，worker PID `{result['worker_PID']}`。观察到{metric['step']}/3900个已提交更新，未见退出码或失败文件。初始化参数、持久buffer、seed和顺序指纹与冻结欧氏证据完全匹配；真实入口在首更新前执行相等性断言，没有加载欧氏最终权重。

本轮资源观察：SMI {resource['device_MiB']}MiB，Torch allocated峰值 {resource['peak_allocated']/1024**3:.2f}GiB，RSS {resource['RSS']/1024**3:.2f}GiB，原阈值检查通过。PID仍按既定diagnostic-only合同记录。

训练保持8k输入／8k输出、同初始化与批次顺序、100遍历、3900步、31200曝光和300丢弃。未进入BNCal、开发评价、额外训练或自动重试。完成后仍须单独正式只读冻结审计及两臂配对核验，本记录不代替最终审计。

输出：`{q['future_paths']['output']}`。
'''
with (A/'execution_start_report_zh_v1.md').open('x',encoding='utf-8') as f:f.write(report)
dump(A/'execution_start_artifact_manifest_v1.json',{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in A.iterdir() if p.is_file()})
print(json.dumps({'status':result['status'],'observed_step':metric['step'],'paired_initialization_equal':True}))
