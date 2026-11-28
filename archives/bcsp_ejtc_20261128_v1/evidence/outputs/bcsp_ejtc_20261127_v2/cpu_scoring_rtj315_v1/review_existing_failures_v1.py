"""Bounded review of frozen scores and prediction arrays. No new distance score/forward."""
from pathlib import Path
import hashlib,io,json,tarfile
import numpy as np
d=Path(__file__).resolve().parent;e=d/'bounded_failure_review_v1';e.mkdir(exist_ok=False)
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
q=load(d/'EJTC_RTJ_D_CPU_scoring_execution_request_v1.json');audit=d/'post_score_freeze_audit_v1/formal_score_freeze_audit_v1.json'
assert load(audit)['status']=='FORMAL_READ_ONLY_EJTC_SCORE315_POST_SCORING_FREEZE_AUDIT_PASS'
scorepath=d/'cpu_scored_once_v1/model_scores.jsonl';summarypath=d/'cpu_scored_once_v1/paired_summary.json';rows=[json.loads(x) for x in scorepath.read_bytes().splitlines()];summary=load(summarypath)
for p in (scorepath,summarypath):assert h(p)==load(audit)['output_hashes'][p.name]['sha256']
by={(r['arm'],r['case_id']):r for r in rows};s=summary['J_minus_T']['summary'];sources=s['source_ids']
far=s['metrics']['coarse']['far20']['by_source'];cover=s['metrics']['dense']['E_Cover_at_2']['by_source']
topfar=sorted(range(21),key=lambda j:(-far[j],sources[j]))[:3];topcover=sorted(range(21),key=lambda j:(cover[j],sources[j]))[:3]
selected=sorted({sources[j] for j in topfar+topcover});assert selected==['train:004','train:037','train:068','train:093','train:095','train:101']
caseids=[cid for cid in q['case_ids'] if by['J',cid]['source_id'] in selected];assert len(caseids)==30
severe=sorted(set(summary['J_minus_R']['summary']['severe_case_ids']['new']+summary['J_minus_T']['summary']['severe_case_ids']['new']));assert severe==['train__093__parietotemporal']
def delta(cid,stage,k):return by['J',cid][stage][k]-by['T',cid][stage][k]
focal=sorted(set(severe+[max([c for c in caseids if by['J',c]['source_id']==sources[j]],key=lambda c:delta(c,'coarse','far20')) for j in topfar]+[min([c for c in caseids if by['J',c]['source_id']==sources[j]],key=lambda c:delta(c,'dense','E_Cover_at_2')) for j in topcover]))
scope=load(d.parent/'native_rtj315_preparation_v1/EJTC_RTJ_D_native315_scope_v2.json');norm={r['case_id']:r['normalization'] for r in scope['inputs']}
listing=load(Path(q['member_listing']['path']));stamps={r['name']:r for r in listing}
archive=Path(q['archive']['path']);assert h(archive)==q['archive']['sha256'];arrays={}
with tarfile.open(archive,'r:gz') as a:
 for cid in focal:
  arrays[cid]={}
  for arm in ('R','T','J'):
   name=f'predictions/{arm}_D__{cid}.npz';raw=a.extractfile(name).read();assert hashlib.sha256(raw).hexdigest()==stamps[name]['sha256']
   with np.load(io.BytesIO(raw),allow_pickle=False) as z:S=z['S'].astype(np.float64);Q=z['coarse'].astype(np.float64);P=z['prediction'].astype(np.float64);delta0=z['delta'].astype(np.float64)
   scale=norm[cid]['scale'];relative=P.reshape(256,32,3)-Q[:,None,:]
   arrays[cid][arm]=dict(delta_mm_p50_p95=np.percentile(np.linalg.norm(delta0,axis=1)*scale,[50,95]).tolist(),child_offset_mm_p50_p95=np.percentile(np.linalg.norm(relative,axis=2)*scale,[50,95]).tolist(),S_centroid_normalized=S.mean(axis=0).tolist(),Q_centroid_normalized=Q.mean(axis=0).tolist(),P_centroid_normalized=P.mean(axis=0).tolist(),Q_bbox_extent_mm=((Q.max(axis=0)-Q.min(axis=0))*scale).tolist(),P_bbox_extent_mm=((P.max(axis=0)-P.min(axis=0))*scale).tolist())
source_review=[]
for j,src in enumerate(sources):
 if src not in selected:continue
 cs=[c for c in caseids if by['J',c]['source_id']==src]
 source_review.append(dict(source_id=src,coarse_far20_delta_pp=far[j],dense_E_cover_delta_pp=cover[j],contribution_to_global_far20_pp=far[j]/21,contribution_to_global_E_cover_pp=cover[j]/21,
  cases=[dict(case_id=c,coarse_far20_delta_pp=100*delta(c,'coarse','far20'),dense_far20_delta_pp=100*delta(c,'dense','far20'),coarse_E_cover_delta_pp=100*delta(c,'coarse','E_Cover_at_2'),dense_E_cover_delta_pp=100*delta(c,'dense','E_Cover_at_2')) for c in cs]))
without={k:float(np.delete(v,sources.index('train:093')).mean()) for k,v in [('coarse_far20_delta_pp',far),('dense_E_cover_delta_pp',cover)]}
focus=[]
for cid in focal:
 focus.append(dict(case_id=cid,source_id=by['J',cid]['source_id'],arms={arm:{k:by[arm,cid][k] for k in ('coarse','dense','geometry','severe_geometry','diagnostics')} for arm in ('R','T','J')},array_observation=arrays[cid]))
result=dict(status='BOUNDED_EXISTING_PREDICTION_REVIEW_COMPLETE',selection_rule='Union of top three J-T coarse far20 increasing sources and top three J-T dense E Cover@2 decreasing sources; five fixed defects each; focus on worst case per selected source/criterion plus new severe case',selected_sources=selected,reviewed_case_pairs=30,deep_review_cases=focal,new_severe_cases=severe,source_review=source_review,focus=focus,leave_out_093_descriptive_only=without,score_audit_sha256=h(audit),new_forward=0,new_distance_scores=0,training=0,threshold_changes=0,limitations=['Existing arrays do not identify the first internal learned feature or token where error occurs','S to Q displacement is descriptive, not a GT-aligned anchor error; no Qraw exists in this OASG output','Source selection is post-hoc and cannot alter original gate or remove cases','Observed tradeoffs cannot establish the causal loss gradient mechanism'])
with (e/'bounded_review_evidence_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
lines=['# EJTC D1：既有预测的有界失败复核','', '## 范围与方法','', '仅使用正式冻结的315行评分及已有预测。按 J−T 粗 far20 增量、密 E Cover@2 降幅各取最差3个来源，合并为6来源30例；逐例比较已存指标，重点回读下表病例的三臂 coarse／S／delta／dense 数组。没有新 forward、距离评分、配准、删点或训练。所有差值均为 J−T；覆盖与 far20 使用百分点。','', '## 来源贡献','', '| 来源 | 粗 far20变化 pp | 密 E Cover@2变化 pp | 对全折粗 far20贡献 pp |','|---|---:|---:|---:|']
for r in source_review:lines.append(f"| {r['source_id']} | {r['coarse_far20_delta_pp']:+.4f} | {r['dense_E_cover_delta_pp']:+.4f} | {r['contribution_to_global_far20_pp']:+.4f} |")
lines+=['','## 固定重点病例','', '| 病例 | T→J 粗 far20 % | T→J 密 far20 % | T→J 密 E Cover@2 % | T→J 密 E P95 mm |','|---|---:|---:|---:|---:|']
for cid in focal:
 t,j=by['T',cid],by['J',cid]
 lines.append(f"| {cid} | {100*t['coarse']['far20']:.3f}→{100*j['coarse']['far20']:.3f} | {100*t['dense']['far20']:.3f}→{100*j['dense']['far20']:.3f} | {100*t['dense']['E_Cover_at_2']:.3f}→{100*j['dense']['E_Cover_at_2']:.3f} | {t['dense']['E_P95_mm']:.3f}→{j['dense']['E_P95_mm']:.3f} |")
lines+=['','## 判读边界','',f"仅描述性去除来源093后，粗 far20 的 J−T 均值为 {without['coarse_far20_delta_pp']:+.4f} pp，密 E Cover@2 为 {without['dense_E_cover_delta_pp']:+.4f} pp。这不是重判、也不允许据此删来源；原全量 FAIL_STOP 不变。",'', 'coarse 与 dense 的误差阶段只能在已保存端点之间定位。远端父点并不意味着其子点必然远端；父子远端计数及每例 delta、子点相对位移详见 JSON。仅凭这些端点不能认定 Mamba、256点数量或某一损失梯度为因果根因。', '', '新增严重病例、粗远端比例和自由表面覆盖应分别判断；E P95 变好仍可同时出现 Cover@2 下降。不得以均值距离或切壁收益抵消预注册保护门。','', '```mermaid','flowchart LR','  accTitle: EJTC 有界复核证据边界','  accDescr: 已有粗密端点可定位表现阶段，但不识别内部因果机制','  A[冻结 coarse 与 dense] --> B[来源贡献与病例端点变化]','  B --> C[原 FAIL_STOP 保持]','  B --> D[内部生成与梯度机制保留未决]','```','', '## 下一步','', '本次复核后停止扩展诊断；形成结题报告并归档。未经新协议与单独授权，不改变权重、λ、点数、门槛或病例，也不启动 C1／D2／SkullFix。']
report=e/'EJTC_D1_有界失败复核_zh_v1.md';report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(status=result['status'],selected_sources=selected,focal_cases=focal,leave_out_093=without,report=str(report)),ensure_ascii=False))
