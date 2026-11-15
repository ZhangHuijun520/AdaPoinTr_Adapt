"""Local audit of downloaded immutable CUDA evidence; no model or new tests."""
import ast,hashlib,importlib.util,json,math
from pathlib import Path,PurePosixPath
F=Path(__file__).resolve().parent;S=F.parent;O=F/'downloads/output';I=F/'downloads/installed';C=I/'control';checks={}
QH='d1324b1b754e2eea91e00ea5ede802c6bd506815b82db82f3c41a070811e9812'
def read(p):return json.loads(p.read_bytes())
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def check(n,v):
 if not v:raise AssertionError(n)
 checks[n]=True
def main():
 qfile=I/'LQI_artificial_cuda_execution_request_v1.json';q=read(qfile);check('01 request exact authorized hash',sha(qfile)==QH)
 before=read(F/'inventory_before_result_v1.json');after=read(F/'inventory_after_result_v1.json');check('02 complete content fingerprints stable excluding atime',before==after)
 outnames={'launch.log','worker.pid','events.jsonl','resources.jsonl','construction.json','completion.json','payload_manifest.json','exit_code.txt'}
 check('03 exact8 output files6 directories',set(before['output']['files'])==outnames and set(before['output']['directories'])=={'.','cache','hf_cache','mplconfig','tmp','triton_cache'})
 mapping=read(S/'pending_transport_v1/installation_mapping_v1.json');controls={'authorization_v1.json','runtime_v1.json','launch_once_v1.sh','launch_attempt_v1.json','readiness_and_installation_receipt_v1.json','startup_receipt_v1.json'}
 check('04 exact8 install6 control files2 dirs',set(before['install']['files'])=={PurePosixPath(r['target']).name for r in mapping['files']}|{'control/'+x for x in controls} and set(before['install']['directories'])=={'.','control'})
 hb=read(F/'hashes_before_result_v1.json')['files'];ha=read(F/'hashes_after_result_v1.json')['files'];hm={r['name']:r for r in hb}
 check('05 independent before after hashes all equal',hb==ha and set(hm)==outnames)
 check('06 all installed bytes match frozen mapping',all(sha(I/PurePosixPath(r['target']).name)==r['sha256'] and (I/PurePosixPath(r['target']).name).stat().st_size==r['bytes'] for r in mapping['files']))
 md=read(F/'metadata_result_v1.json')['files'];check('07 all downloaded bytes match independent hashes',all(sha(F/'downloads'/n)==r['sha256'] for n,r in md.items()) and all(hm[n.split('/',1)[1]]['sha256']==r['sha256'] for n,r in md.items() if n.startswith('output/')))
 check('08 exit0 worker and tmux absent',(O/'exit_code.txt').read_text().strip()=='0' and read(F/'finished_result_v1.json')['status']=='EXIT0_WORKER_TMUX_ABSENT')
 auth=read(C/'authorization_v1.json');runtime=read(C/'runtime_v1.json');check('09 explicit authorization exact request',auth['explicit_user_authorization'] is True and auth['request_sha256']==QH and QH in auth['user_authorization_text'])
 check('10 runtime one way binding',runtime==dict(schema='bcsp-lqi-cuda-runtime-v1',request_sha256=QH,authorization_sha256=sha(C/'authorization_v1.json')))
 entry=I/'bcsp_lqi_cuda_admission_v1.py';sp=importlib.util.spec_from_file_location('inert_lqi_formal_audit',entry);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e);e.authorize(q,QH,auth,sha(C/'authorization_v1.json'),runtime)
 check('11 inert entry actual authorization contract',True)
 check('12 launcher exact original renderer',(C/'launch_once_v1.sh').read_text()==e.render_launcher(q,QH,sha(C/'authorization_v1.json'),sha(C/'runtime_v1.json')))
 check('13 unique claim',read(C/'launch_attempt_v1.json')==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH))
 startup=read(C/'startup_receipt_v1.json');check('14 startup receipt hashes',startup['tmux_returncode']==0 and startup['request_sha256']==QH and startup['authorization_sha256']==sha(C/'authorization_v1.json') and startup['runtime_sha256']==sha(C/'runtime_v1.json') and startup['launcher_sha256']==sha(C/'launch_once_v1.sh'))
 receipt=read(C/'readiness_and_installation_receipt_v1.json');check('15 exclusive install8 no real reads',receipt['status']=='EIGHT_EXCLUSIVE_INSTALL_HASHES_PASS' and receipt['overwritten_files']==receipt['real_data_reads']==receipt['checkpoint_reads']==0)
 am={r['path']:r for r in read(F/'assets_result_v1.json')['records']}
 check('16 inherited sources extensions provider archive fresh hashes',all(am[r['path']]['sha256']==r['sha256'] for r in receipt['read_manifest'] if not r['path'].startswith(q['entry']['path'].rsplit('/',1)[0]+'/')))
 p3=read(I/'entry_P3_v1.json');check('17 final entry model CPU29 P3 hashes',p3['status']=='LQI_CUDA_ENTRY_LOCAL_P3_PASS' and p3['entry_sha256']==sha(entry) and p3['decoder_sha256']==sha(I/'bcsp_lqi_decoder_v1.py') and p3['factory_sha256']==sha(I/'bcsp_lqi_factory_v1.py') and p3['CPU_entry_assertions']==29 and all(p3['checks'].values()))
 done=read(O/'completion.json');expected=dict(full_forward=2,full_backward=2,full_loss=2,decoder_forward=0,decoder_backward=0,optimizer_steps=0)
 check('18 exactly2F2loss2B0step complete',done['status']=='LQI_NATIVE_CUDA_COMPLETE_PENDING_FORMAL_FREEZE_AUDIT' and done['counts']==expected and done['request_sha256']==QH)
 check('19 no optimizer real payload checkpoint BNCal training admission',done['real_data_reads']==done['checkpoint_loads']==0 and done['optimizer_constructed'] is done['training_admission'] is done['BNCal'] is False)
 native=done['native_SSM_calls'];check('20 exact22 native modules72 calls',len(native)==22 and sum(native.values())==72 and all(v==(2 if '.cond_ssm' in n else 4) for n,v in native.items()))
 ev=rows(O/'events.jsonl');claims=[r for r in ev if r.get('kind')=='ATTEMPT_BEFORE_CALL'];phases=[r for r in ev if 'phase' in r];check('21 exact6 claims2 phase records1 restoration',len(ev)==9 and [r['operation'] for r in claims]==['full_forward','full_loss','full_backward']*2 and claims[-1]['counts']==expected and [(r['phase'],r['batch']) for r in phases]==[('eval_1',1),('train_1',8)])
 names=['base_model.coarse_pred.','base_model.decoder.coordinate_pe.','reduce_map.']+['base_model.encoder.blocks.blocks.'+str(i)+'.attn.mixer.' for i in range(6)]+['base_model.decoder.blocks.'+str(i)+'.'+s+'.' for i in range(8) for s in ('self_ssm','cond_ssm')]+['base_model.decoder.blocks.'+str(i)+'.norm_v.' for i in range(8)]+['increase_dim.','decode_head.']
 for r in phases:
  g=r['gradients'];check(r['phase']+' all403 recorded gradients finite',len(g['parameter_norms'])==403 and all(math.isfinite(v) and v>=0 for v in g['parameter_norms'].values()))
  check(r['phase']+' all35 groups nonzero independently summed',set(g['module_norm_sums'])==set(names) and all(v>0 and math.isclose(v,sum(x for n,x in g['parameter_norms'].items() if n.startswith(k)),rel_tol=1e-12,abs_tol=1e-12) for k,v in g['module_norm_sums'].items()))
 check('22 both full losses finite no weight update',all(math.isfinite(r['loss']) and r['parameters_unchanged'] for r in phases))
 check('23 BN only permitted train changes',not phases[0]['BN_changed'] and len(phases[1]['BN_changed'])==3 and all(n.endswith(('running_mean','running_var','num_batches_tracked')) for n in phases[1]['BN_changed']))
 check('24 both per-phase RNG records unchanged',all(r['RNG_before']==r['RNG_after'] and set(r['RNG_before'])=={'CPU','CUDA','Python','numpy'} and all(len(bytes.fromhex(r['RNG_before'][k]))==32 for k in ('CPU','CUDA')) for r in phases))
 check('25 final full state RNG mode restoration assertions',ev[-1]==dict(kind='FULL_RESTORATION',state_restored=True,RNG_restored=True,modes_restored=True))
 construction=read(O/'construction.json');factory=construction['factory'];check('26 actual candidate native version construction',factory['version']=='F0-LQI-implementation-v1' and factory['variant']=='F0-LQI-v1' and factory['artificial_fixture'] is False and factory['additional_learned_parameters']==0)
 check('27 exact native origins and no registered attention',len(construction['native_origins'])==7 and set(construction['native_origins'])<={r['path'] for r in q['dependencies']} and done['attention_registered']['forbidden_registered_modules']==[])
 rs=rows(O/'resources.jsonl');L=q['limits']
 check('28 all numeric resources within original budgets',all(all(r['checks'].values()) and not r['failed_checks'] and r['values']['RSS_bytes']<=L['RSS_bytes'] and r['values']['device_MiB']<=L['device_MiB'] and r['values']['peak_allocated']<=L['torch_peak_bytes'] and r['values']['peak_reserved']<=L['torch_peak_bytes'] and r['values']['output_bytes']<=L['output_bytes'] and r['values']['elapsed_seconds']<=L['wall_seconds'] and r['values']['free_disk_bytes']>=L['minimum_free_disk_bytes'] for r in rs) and rs[-1]['phase']=='complete')
 manifest=read(O/'payload_manifest.json');check('29 exact4 payload manifest records',len(manifest)==4 and {r['name'] for r in manifest}=={'completion.json','construction.json','events.jsonl','resources.jsonl'} and all(hm[r['name']]==r for r in manifest))
 check('30 final total output and disk budget',sum(r['bytes'] for r in hb)<=L['output_bytes'] and read(F/'finished_result_v1.json')['free_disk_bytes']>=L['minimum_free_disk_bytes'])
 peak={k:max(r['values'][k] for r in rs) for k in ('RSS_bytes','device_MiB','peak_allocated','peak_reserved','elapsed_seconds')}
 result=dict(status='FORMAL_LQI_POST_CUDA_FREEZE_AUDIT_PASS',check_count=len(checks),checks=checks,request_sha256=QH,counts=expected,native_SSM_calls=72,losses=[dict(phase=r['phase'],batch=r['batch'],loss=r['loss']) for r in phases],gradient_parameters_per_phase=403,positive_gradient_module_groups_per_phase=35,resources_peak=peak,output_hashes=hb,server_writes=0,new_model_calls=0,read_only=True,training_authorized=False,limits=['Synthetic tensors and existing cdist backend only; no Native accuracy or clinical geometry evidence.','Final restoration is verified from assertions of hash-bound runtime source; raw before/after restoration fingerprints were not both emitted independently.','No bitwise gradient repeat test; accepted finite nondeterminism is preserved.','Known dispatched attention-op audit cannot prove opaque extension internals have no attention semantics.'])
 with (F/'formal_post_CUDA_freeze_audit_result_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,ensure_ascii=False)
 report=f'''# F0-LQI正式只读post-CUDA冻结审计

结论：**通过，{len(checks)}项核验通过**。本轮没有运行模型、forward、测试、checkpoint加载或服务器写入。

完整清单为8个输出文件及6个目录，安装区域8个文件及6个控制凭据；前后内容相关指纹和SHA256一致。授权链、单次claim、原launcher字节、安装映射及既有资产重新核验通过。

计数：2次完整forward、2次原完整loss、2次backward、0step；22个原生Mamba模块共72次forward钩子调用。无额外decoder-only、warmup、真实数据、checkpoint、BNCal或开发集评价。

两阶段分别为eval batch1及训练模式batch8。人工loss为{phases[0]['loss']:.9f}和{phases[1]['loss']:.9f}，仅证明有限可反传，不作科研性能解释。每阶段403个已记录参数梯度范数有限，35组必须活跃模块范数均非零，审计独立重新求和一致。没有要求梯度逐位确定性。

eval无BN变更；训练模式仅3个BN缓冲发生预期临时变化。两阶段RNG记录前后一致，最终state/RNG/mode恢复断言全部为true。恢复证据由已绑定源码在运行时计算；原入口没有独立输出最终恢复前后两个原始哈希，本审计不能凭空补出，亦未为此重跑。

记录到的最大SMI显存{peak['device_MiB']}MiB，Torch峰值allocated {peak['peak_allocated']/2**30:.3f}GiB、reserved {peak['peak_reserved']/2**30:.3f}GiB，RSS {peak['RSS_bytes']/2**30:.3f}GiB。最大记录耗时{peak['elapsed_seconds']:.3f}秒。各条实际数值与冻结预算独立比较均通过；这些是监测记录，不宣称连续硬隔离或精准正式计时。

该结果仅为当前容器、人工输入、原生Mamba/provider、现有cdist完整loss的零更新准入。尚无LQI真实数据效果或训练成功证据；不自动授权训练。

下一步可准备LQI首个Fold C配对训练范围，保持已冻结F0初始化、数据、顺序、8k→8k及3900步合同。先核查现有训练入口能否正确分派LQI及记录交错trace语义，必要时仅做最小入口适配并创建待授权request；不得把旧F0路径直接当作LQI已支持。

完整机器可读证据：`formal_post_CUDA_freeze_audit_result_v1.json`。
'''
 with (F/'LQI_正式只读postCUDA冻结审计报告_zh_v1.md').open('x',encoding='utf-8') as f:f.write(report)
 with (F/'audit_artifact_manifest_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status=result['status'],files=[rec(p) for p in sorted(F.rglob('*')) if p.is_file() and p.name!='audit_artifact_manifest_v1.json']),f,indent=2,ensure_ascii=False)
 print(json.dumps(dict(status=result['status'],checks=len(checks),peak=peak)))
if __name__=='__main__':main()
