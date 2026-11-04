"""Local operational completion record; explicitly not a formal freeze audit."""
import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent/'blue_pair_eval_v1';A=N/'authorized_execution_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
v=json.loads((A/'prediction_observation_2_result.json').read_bytes());s=json.loads((N/'development_execution_request_v1.json').read_bytes());execution=json.loads((A/'execute_once_result.json').read_bytes())
assert execution['status']=='CONFIRMED' and v['exit_code']=='0' and v['prediction_records']==210 and not v['session_alive'] and not v['worker_alive'] and v['failure'] is None
done=v['inference_complete'];assert done['status']=='BLUE_NOISE_PAIR_210_FORWARD_COMPLETE' and done['forwards']==210
assert len(done['models'])==2 and all(m['forwards']==105 and m['state_before']==m['state_after'] and m['CPU_rng_before']==m['CPU_rng_after'] and m['CUDA_rng_before']==m['CUDA_rng_after'] and m['Python_numpy_RNG_unchanged'] for m in done['models'])
assert all(done[k]==0 for k in ('training_updates','BNCal','loss','backward'))
result={'status':'PREDICTION_BATCH_COMPLETED_FORMAL_AUDIT_PENDING','scope_sha256':sha(N/'development_execution_request_v1.json'),'predictions':210,'per_arm':105,'exit_code':0,'parameters_BN_and_RNG_unchanged_reported':True,'reported_archive':v['completion_archive'],'resource_observation':v['last_resources'],'formal_freeze_audit':False,'scoring_executed':False,'single_controller_execution':True}
with (A/'execution_completion_record_v1.json').open('x') as f:json.dump(result,f,indent=2)
report=f'''# 欧氏／图距离两臂：开发预测执行记录

2026-11-04。状态：**210预测已完成，正式冻结审计待单独授权。**

本次授权scope SHA256 `{result['scope_sha256']}`。执行前核验当前hostname／GPU／Python、两个已冻结checkpoint、固定复用资产、5个上传文件和全部213目标／新目录不存在性；随后按冻结映射不覆盖安装，单向材料化授权、runtime、launcher及claim，仅启动一次固定tmux。

只读完成观察显示：欧氏105例＋图距离105例，共210条预测记录；退出码0，tmux与worker退出，无failure。两模型各自参数／BN状态、CPU／CUDA RNG与Python／NumPy RNG前后保持一致。training_updates、BNCal、loss和backward均为0。未进行本机评分、统计比较或额外训练。

完成记录报告归档：`{v['completion_archive']['path']}`，{v['completion_archive']['bytes']:,} bytes，SHA256 `{v['completion_archive']['sha256']}`。这些是当前完成记录与状态观察，尚未独立重算归档哈希、逐预测核验或完整冻结；不能替代正式审计，也不据此判断采样胜负。

下一步应单独授权正式只读预测后冻结审计，核验210份预测、归档／内容清单、状态／RNG、调用计数及资源证据；通过后再手动下载并核验，随后单独授权统一CPU评分。当前没有下载、评分或正式gate。
'''
with (A/'execution_completion_report_zh_v1.md').open('x',encoding='utf-8') as f:f.write(report)
with (A/'execution_artifact_manifest_v1.json').open('x') as f:json.dump({p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in A.iterdir() if p.is_file()},f,indent=2)
print(json.dumps({'status':result['status'],'predictions':210,'exit_code':0}))
