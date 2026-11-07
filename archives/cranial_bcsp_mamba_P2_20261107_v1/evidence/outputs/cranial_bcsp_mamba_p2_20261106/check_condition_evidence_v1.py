"""Bounded local saved-evidence check; no model, NPZ decoding or fitting."""
from pathlib import Path
import json,hashlib,math,statistics,tarfile,zipfile,io
P=Path(__file__).resolve().parent;R=P.parents[1];S=P/'H1_scoring_implementation_20261107_v1';F=P/'condition_information_review_20261107_v1'
F.mkdir()
manifest=[]
def load(path,binding=None):
 path=Path(path);raw=path.read_bytes();b=dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 if binding:assert b==binding,(path,'hash mismatch')
 manifest.append(b);return json.loads(raw)
def bound_jsonl(b):
 raw=Path(b['path']).read_bytes();assert len(raw)==b['bytes'] and hashlib.sha256(raw).hexdigest()==b['sha256'];manifest.append(b);return [json.loads(x) for x in raw.decode().splitlines()]
audit=load(S/'post_scoring_freeze_audit_20261107_v1/audit_report_v1.json');assert audit['status']=='FORMAL_POST_SCORING_FREEZE_AUDIT_PASS'
current=bound_jsonl(next(b for b in audit['output_manifest'] if Path(b['path']).name=='case_metrics.jsonl'))
q=load(S/'local_scoring_execution_request_v1.json');idx=load(q['score_case_index']['path'],q['score_case_index']);norm={(r['fold'],r['case_id']):r['normalization'] for r in idx['cases']}
code=load(R/'docs/cranial_bcsp_mamba_p2_20261106/P2A_只读证据核对记录_v1.json')
source_refs=[]
for b in code['evidence']:
 if b['label'] in ['model','factory','encoder']:
  p=Path(b['path']);raw=p.read_bytes();assert len(raw)==b['bytes'] and hashlib.sha256(raw).hexdigest()==b['sha256'];manifest.append({k:b[k] for k in ['path','bytes','sha256']});source_refs.append(b['label'])
rows=[r for r in current if r['arm']=='M_H1']
for fold,sub in [('C','paired_development_evaluator_v2'),('D','FoldD_paired_development_entry_v1')]:
 a=load(R/'outputs/cranial_bcsp_mamba_p1_20261104'/sub/'post_scoring_freeze_audit_v1/audit_report_v1.json');assert a['status']=='FORMAL_POST_SCORING_FREEZE_AUDIT_PASS'
 rows += [r for r in bound_jsonl(next(b for b in a['output_manifest'] if Path(b['path']).name=='case_metrics.jsonl')) if r['arm'] in ['T0','M0']]
result={}
for fold in ['C','D']:
 result[fold]={}
 for arm in ['T0','M0','M_H1']:
  part=[r for r in rows if r['fold']==fold and r['arm']==arm];assert len(part)==105
  records=[]
  for r in part:
   c=r['stage_geometry']['coarse'];d=r['position_shape'];g=d['GT8192_centroid_mm'];o=norm[fold,r['case_id']]['center'];offset=r['stage_geometry']['mean_dense_minus_coarse_mm']
   cvec=[x-y for x,y in zip(c['centroid_mm'],g)];dot=sum(x*y for x,y in zip(cvec,offset));cn=c['centroid_offset_mm'];dn=d['centroid_offset_mm']
   records.append(dict(case_id=r['case_id'],source_id=r['source_id'],coarse_error_mm=cn,dense_error_mm=dn,dense_minus_coarse_error_mm=dn-cn,offset_norm_mm=math.sqrt(sum(x*x for x in offset)),offset_opposes_coarse_error=dot<0,coarse_abs_log_radius=abs(math.log(c['radius_gyration_ratio'])),D_bbox_center_error_mm=math.sqrt(sum((x-y)**2 for x,y in zip(o,g))),normalized_coarse_centroid=[(x-y)/norm[fold,r['case_id']]['scale'] for x,y in zip(c['centroid_mm'],o)]))
  result[fold][arm]=dict(cases=105,sources=21,coarse_centroid_mm=statistics.fmean(v['coarse_error_mm'] for v in records),dense_centroid_mm=statistics.fmean(v['dense_error_mm'] for v in records),coarse_abs_log_radius=statistics.fmean(v['coarse_abs_log_radius'] for v in records),dense_reduces_centroid_count=sum(v['dense_error_mm']<v['coarse_error_mm'] for v in records),offset_opposes_coarse_error_count=sum(v['offset_opposes_coarse_error'] for v in records),coarse_over20_count=sum(v['coarse_error_mm']>20 for v in records),dense_over20_count=sum(v['dense_error_mm']>20 for v in records),D_bbox_center_error_mm=statistics.fmean(v['D_bbox_center_error_mm'] for v in records),normalized_coarse_centroid_axis_std=[statistics.pstdev(v['normalized_coarse_centroid'][i] for v in records) for i in range(3)],records=records)
# Inspect only exact three frozen prediction archives: headers/schema, no arrays decoded.
schemas={}
for key,inp in q['archive_inputs'].items():
 b=inp['archive'];path=Path(b['path']);raw=path.read_bytes();assert len(raw)==b['bytes'] and hashlib.sha256(raw).hexdigest()==b['sha256'];manifest.append(b)
 entries=[];n=0
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tf:
  for m in tf:
   assert n<256;n+=1
   if m.isfile() and m.name.endswith('.npz'):
    assert m.size<1048576
    with zipfile.ZipFile(io.BytesIO(tf.extractfile(m).read())) as z:entries.append(tuple(sorted(z.namelist())))
 schemas[key]=dict(archive_members=n,prediction_NPZ=len(entries),NPZ_schemas=[dict(fields=list(v),count=entries.count(v)) for v in sorted(set(entries))],feature_arrays_present=any(any('feature' in x or 'memory' in x for x in v) for v in entries))
assert all(not s['feature_arrays_present'] for s in schemas.values())
payload=dict(status='SAVED_EVIDENCE_CHECK_COMPLETE_FEATURE_PROBE_NOT_EXECUTED',summary=result,archive_schema_inventory=schemas,source_identity_checked=source_refs,model_loaded=False,forward_calls=0,arrays_decoded=False,probe_fit=False,server_operations=0,H2_selected=False)
with (F/'saved_condition_evidence_v1.json').open('x',encoding='utf-8') as f:json.dump(payload,f,indent=2,allow_nan=False)
lines=['# 输入条件信息与 coarse 坐标头：既有证据复核 v1','','日期：2026-11-07。**当前能确认条件路径存在、coarse随输入变化且存在显著残余误差；尚不能确认编码特征已含有足够定位信息却被坐标头浪费。暂不选择H2。**','','## 1. 已完成的限定检查','','重新核对母版、factory和encoder三份源码身份；读取正式冻结的P1与H1评分。复核3个预测归档的NPZ字段目录，没有解码点数组或载入checkpoint。未连接服务器、forward、拟合读出或改模型。','','## 2. 实际路径及不能据此推出的结论','','```mermaid','flowchart LR','  accTitle: 输入到coarse与dense的实际条件路径','  accDescr: 输入经局部聚合、encoder和全局池化产生coarse，dense还受decoder相对位移影响。','  D[残缺骨输入] --> L[局部聚合与位置嵌入] --> E[T0或M0 encoder] --> Z[逐token投影与max pooling] --> C[coarse_pred输出256点]','  E --> M[decoder memory]','  Z --> Q[query特征]','  C --> Q','  Q --> H[decoder与重建头]','  M --> H','  C --> P[完整骨块dense点集]','  H --> P','```','','`global_feature`为B×1024，`coarse_pred`为1024→1024→768的非线性头，重排为256×3。它不是直接从GT得到的位置；learned_only不使用已计算的输入FPS候选拼成Q。源码可微路径只证明可利用；坐标随病例改变只证明非恒定输出，不证明变化正确，也不能区分encoder、pooling或坐标头瓶颈。','','## 3. 保存统计能回答什么','','各折每来源5例，故下表105例均值等于21来源等权均值。coarse→dense为位置误差，不是表面距离；修正例数不代表覆盖改善。','','| 折 | 模型 | coarse质心误差mm | dense质心误差mm | dense降低位置误差例数 | coarse半径绝对对数误差 |','|---|---|---:|---:|---:|---:|']
for fold in result:
 for arm,z in result[fold].items():lines.append(f"| {fold} | {arm} | {z['coarse_centroid_mm']:.3f} | {z['dense_centroid_mm']:.3f} | {z['dense_reduces_centroid_count']}/105 | {z['coarse_abs_log_radius']:.4f} |")
lines+=['','H1两折的coarse矩改善并未转化为完整形状收益，说明只检验全局矩不够；但不能据此断言encoder已充分识别缺损。dense可修正也可放大位置误差，不能只查看最终输出而跳过Q。完整病例记录与方向分解保存在JSON，不筛选异常后重新计分。','','## 4. 证据缺口与下一步的最小研究问题','','三份冻结预测归档只保存prediction及少量代表例coarse数组，另有全量coarse/dense摘要；没有可用于训练／开发读出的全局特征数组。生产源码虽有full_instrumentation接口，不等于这些特征已持久保存。训练来源全局特征和训练目标矩也不能从开发预测重建。','','因此，本轮不能完成“冻结特征读出是否优于原坐标头”的实证判断，不能把缺失数据写成探针失败，更不能直接宣布H2。建议下一步一次性限定冻结特征提取＋单配置CPU读出对照，详见同目录方案。无需新模型训练、无optimizer step、无需重复GPU preflight。','', '## 5. 明确停止点','','既有证据检查已结束。后续提取需要实际访问该折训练／开发输入及冻结checkpoint，须先绑定数据、设备和预算后单独执行授权；本报告不自动授权这些操作。']
with (F/'输入条件与coarse利用_既有证据复核_zh_v1.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
with (F/'read_evidence_manifest_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(files=manifest,read_only_inputs=True),f,indent=2)
print(json.dumps(dict(status=payload['status'],summary={fold:{arm:{k:v for k,v in z.items() if k!='records'} for arm,z in by.items()} for fold,by in result.items()},archives=schemas),ensure_ascii=True))
