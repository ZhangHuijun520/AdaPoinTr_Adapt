"""Limited local request-reader review with RAM grants, no model or server calls."""
import ast,copy,hashlib,importlib.util,json
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2';C=O/'graph_request_v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def main():
    req=C/'candidate_training_execution_request_v1.json';s=json.loads(req.read_bytes());q=json.loads((C/'training_entry_request_v1.json').read_bytes());base=json.loads((O/'Euclidean_training_entry_request_v1.json').read_bytes())
    prior=json.loads((O/'Euclidean_training_execution_request_v1.json').read_bytes());af=O/'post_Euclidean_training_freeze_audit_v1/audit_report_v1.json';audit=json.loads(af.read_bytes());pair=json.loads((C/'paired_initialization_receipt_v1.json').read_bytes())
    assert sha(req)=='1072fad5cbbb970fe37cf6300445d705b8dc99a38aba3fc20cb70cac6cf227d5'
    assert sha(af)==s['parent_baseline_audit']['sha256']==pair['baseline_freeze_audit_sha256'] and all(audit['checks'].values())
    assert s['status']==q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and s['execution_authorized'] is False
    same=['stage','fold','n_input','identity','implementation','static_config','order_plan','model_root','resource_rebind','preflight_scope','GPU_audit','preflight_request_sha256']
    assert all(q[k]==base[k] for k in same) and s['resources_per_run']==prior['resources_per_run'] and s['training_counts']==prior['training_counts']
    assert q['arm']=='surface_graph' and q['paired_initialization']==s['paired_initialization'] and q['output']!=base['output'] and q['launch_attempt']!=base['launch_attempt']
    mappings=json.loads((O/'non_overwrite_installation_mapping_v1.json').read_bytes())['assets']
    local={r['destination']:Path(r['local_path']) for r in mappings}
    fresh=json.loads((C/'non_overwrite_control_installation_mapping_v1.json').read_bytes())['files']
    assert len(fresh)==3 and not any(r['destination'] in local for r in fresh)
    local.update({r['destination']:Path(r['local_path']) for r in fresh})
    local[q['preflight_scope']['path']]=B/'gpu_preflight_plotting_lazy_v3/artificial_gpu_zero_update_frozen_scope_v3.json'
    local[q['GPU_audit']['path']]=next(p for p in B.rglob('post_preflight_freeze_audit_report_v1.json') if sha(p)==q['GPU_audit']['sha256'])
    graph=[r for r in mappings if r['destination'].startswith(q['data_root']+'/points/')]
    installed=json.loads((O/'authorized_execution_v1/install_execute_once_observation.json').read_bytes())
    assert len(graph)==315 and installed['status']=='INSTALLATION_650_HASH_PASS'
    records=[json.loads(x) for x in local[q['QC']['manifests']['surface_graph']['path']].read_text(encoding='utf-8').splitlines()]
    assert {r['destination']:r['sha256'] for r in graph}=={q['data_root']+'/'+r['point_path']:r['sha256'] for r in records}
    spec=importlib.util.spec_from_file_location('graph_request_metadata_contract',O/'implementation/bcsp_blue_noise_training_contract_v1.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
    checks={'exact_parent_audit_and_initialization_bound':True,'same_scientific_code_environment_order_resources':True,'three_new_control_files_only':True,'315_graph_files_match_initial_installation_selection':True}
    original_exact=c.exact;original_json=c.json_bound
    auth={'schema':'bcsp-training-authorization-v1','request_sha256':s['inner_request']['sha256'],'explicit_user_authorization':True,'user_authorization_text':'ARTIFICIAL RAM REQUEST READER CHECK ONLY'}
    runtime={'schema':'bcsp-training-runtime-v1','request_sha256':s['inner_request']['sha256'],'authorization_sha256':'2'*64}
    def exact(r):
        p=local[r['path']];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];return p
    def js(r):
        if r['path']=='RAM:auth':return copy.deepcopy(auth)
        if r['path']=='RAM:runtime':return copy.deepcopy(runtime)
        return json.loads(exact(r).read_bytes())
    c.exact=exact;c.json_bound=js
    try:
        got,cfg=c.authorize(s['inner_request'],{'path':'RAM:auth','sha256':'2'*64},{'path':'RAM:runtime','sha256':'3'*64});assert got==q
        checks['full_authorize_and_resource_rebind_RAM_only']=True
        rows,fold=c.verify_qualified_receipt(js(q['QC']['qualified_receipt']),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'C',8192,'surface_graph');assert len(rows)==315
        checks['actual_metadata_reader_315_training_only']=True
        plan=c.validate_order(js(q['order_plan']),fold['train_case_ids']);canonical=c.canonical_sha(plan)
        c.validate_pair_initialization(pair,q,audit['initialization']['parameter_sha256'],audit['initialization']['persistent_state_sha256'],canonical)
        checks['paired_initialization_accepts_frozen_fingerprints']=True
        try:c.validate_pair_initialization(pair,q,'0'*64,audit['initialization']['persistent_state_sha256'],canonical)
        except ValueError:checks['different_initialization_rejected_before_update']=True
        else:raise AssertionError('different initialization accepted')
        auth['explicit_user_authorization']=False
        try:c.authorize(s['inner_request'],{'path':'RAM:auth','sha256':'2'*64},{'path':'RAM:runtime','sha256':'3'*64})
        except ValueError:checks['false_authorization_rejected']=True
        else:raise AssertionError('false authorization accepted')
    finally:c.exact=original_exact;c.json_bound=original_json
    assert len(checks)==9 and all(checks.values())
    assert not any(p.name in ('authorization_v1.json','runtime_v1.json','launch_once_v1.sh','launch_attempt_v1.json') for p in C.rglob('*'))
    result={'status':'LOCAL_GRAPH_REQUEST_READER_REVIEW_PASS','checks':checks,'request_sha256':sha(req),'server_calls':0,'model_calls':0,'real_authorization_runtime_launcher_created':0,'RAM_grants_only':True,'remaining_execution_gates':['current hostname/GPU/provider and free resources','all three targets plus control/output/tmux absent','all upload hashes','315 installed graph NPZ stream hashes','baseline frozen evidence and paired initialization contract']}
    dump(C/'local_request_reader_review_v1.json',result)
    lines=['# 图距离臂 Fold C：待授权训练 request v1','','2026-11-04。状态：**AWAITING_EXPLICIT_USER_AUTHORIZATION**。本轮只在本机准备与核对，没有服务器调用、安装或模型执行。','',
    '固定surface_graph、Fold C、seed0、输入8192／输出8192。复用与欧氏臂逐字节相同的模型／训练实现、环境身份、配置、批次顺序及资源阈值，保持batch8、100次遍历、3900次更新、31200次曝光及300次丢弃。','',
    '初始化从scratch seed0创建，在首个更新前比较参数与持久buffer指纹。绑定欧氏臂39项正式冻结审计、实测checkpoint身份、初始化及顺序；不读取或加载欧氏臂最终权重作为初始化。绑定checkpoint哈希用于溯源，不是resume。','',
    '只运输3个新控制文件：paired_initialization_receipt_v1.json、qualified_training_receipt_v1.json、training_entry_request_v1.json。点集、源码、provider不重新运输或修改。315份图距离训练点集已在最初650文件安装时核验；欧氏训练后审计未重新读取图距离NPZ，因此本request明确要求执行前重新流式核验全部315份，不能把安装记录冒充最新实测。','',
    '9项本机限定读取检查通过，包括实际完整authorize/rebind路径、315训练元数据、初始化一致性接受、不同初始化拒绝及未授权拒绝。授权与runtime仅在RAM中模拟，未写真实执行文件。','',
    '新控制目录：`'+s['future_paths']['control']+'`。','新输出：`'+q['output']+'`。','固定tmux：`'+s['future_paths']['tmux']+'`。','',
    '预算保持24小时、RSS8GiB、设备22528MiB、Torch峰值20GiB、输出2GiB及可用磁盘至少4GiB；监测式停止，不保证专属cgroup。失败即停，不自动重试／resume。开发评价、BNCal、其他fold／seed及额外训练仍不授权。','',
    '运输文件见本目录transport_v1的5个文件，上传到/home/jovyan。request完整SHA256：','',sha(req),'',
    '只有对完整request哈希的后续单独执行授权，才可执行上传／就绪核验、3文件不覆盖安装，以及授权→runtime→launcher的单向材料化和唯一一次图距离训练。当前没有这些执行内容。','',
    '准备过程曾遇到旧长文件名触发Windows路径长度限制，失败目录保留；本版只缩短本机目录及运输文件名，没有改变服务器路径、生产实现或科学合同。']
    with (C/'candidate_request_preparation_report_zh_v1.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
    dump(C/'candidate_artifact_manifest_v1.json',{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in C.rglob('*') if p.is_file()})
    print(json.dumps({'status':result['status'],'checks':len(checks),'request_sha256':sha(req),'transport':str(C/'transport_v1')}))
if __name__=='__main__':main()
