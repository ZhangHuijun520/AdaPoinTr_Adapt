"""Local handoff and final consistency readback; no execution."""
import hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;N=B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(r):
 p=Path(r['path']);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];return p
def main():
 c=json.loads((N/'preparation_completion_v1.json').read_bytes());request=check(c['request']);q=json.loads(request.read_bytes());p3=json.loads(check(c['P3']).read_bytes())
 assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
 for key in ['entry_request','controller_template','protocol','local_P3','installation_mapping_record']:check(q[key])
 for r in p3['implementation'].values():check(r)
 for key in ['CPU_tests','controller_readback','derivation','data_receipt','input_index','reference_manifest','protocol']:check(p3[key])
 for r in c['upload_files']:check(r)
 assert not any((N/x).exists() for x in ['authorization.json','runtime.json','evaluate_once.sh','launch_attempt.json'])
 lines=['# Fold C V1／Morton配对开发评价：上传与授权说明','',
 '**本机准备完成，状态 AWAITING_EXPLICIT_USER_AUTHORIZATION。未操作服务器、部署、预测或评分。**','',
 f"request：`{request.name}`",'',f"完整SHA256：`{sha(request)}`",'',
 '固定105例／21来源，每臂一次，共210次native预测，8192输入与输出。两个final checkpoint已由正式训练后审计冻结；本次不重训、不BNCal、不更改采样参数。开发输入保持两臂共同GT、归一化与逐病例点序。', '',
 '主指标：A1未知表面E面积加权P95(mm)；关键次指标：切壁J P95／Cover@2mm、E Cover@2mm及共同GT8192 CD-L1。按来源五缺损平均后等权比较Morton−V1，仅作单折单seed描述性结论。评价协议及后续单独评分边界见 `paired_evaluation_protocol_zh_v1.md`。', '',
 '## 手动上传','',
 '将本目录以下五个文件上传到服务器 `/home/jovyan`。运输包共213成员（210点集＋3个工具／元数据文件），不含checkpoint或原始NRRD。不要上传CPU人工fixture或本机参考库。','',
 '| 文件名 | bytes | SHA256 |','|---|---:|---|']
 for r in c['upload_files']:lines.append(f"| {Path(r['path']).name} | {r['bytes']} | `{r['sha256']}` |")
 lines+=['','## 后续顺序','',
 '上传后，对上述完整request SHA256单独授权。执行前仍须实时重验容器／GPU、两个checkpoint及精确复用资产、上传包、所有新目标不存在和资源；只按冻结映射不覆盖安装、材料化单向授权链，再启动唯一一次210预测。失败即停，不自动重试。当前容器预期为 `shu-common-25721452-notebook-v2iwsa-0`，若身份已变则不能直接复用。', '',
 '预测结束后，另行授权正式只读冻结审计；下载并核验归档后，单独授权统一CPU评分。当前request不授权评分或正式gate。现有旧四模型评分工具不能直接运行两臂数据，评分时只做必要的两臂读取适配，保持当前冻结的指标与参考不变。', '',
 '## 验证证据','',
 '20项CPU合同全部通过，人工Tiny模型及权重只在CPU使用；完整213成员运输包哈希回读通过，缺成员／重复目标均拒绝。P3记录最终实现、数据与父审计哈希。CPU测试不是CUDA通过证明；本轮未发出WSL或服务器调用。']
 out=N/'README_upload_and_authorization_zh_v1.md'
 with out.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
 with (N/'final_readback_v1.json').open('x') as f:json.dump(dict(status='FINAL_PENDING_REQUEST_READBACK_PASS',request_sha256=sha(request),bound_local_files_verified=True,upload_file_count=5,production_materialization=False,server_calls=0,forwards=0,readme_sha256=sha(out)),f,indent=2)
 print('FINAL_PENDING_REQUEST_READBACK_PASS',sha(request))
if __name__=='__main__':main()
