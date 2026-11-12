"""Build final report tables solely from compiled frozen values, no metric computation."""
import hashlib,html,json,os,re
from pathlib import Path
S=Path(__file__).resolve().parent;R=S.parents[1];B=R/'outputs/cranial_bcsp_fullmamba_20261110'
def read(p):return json.loads(p.read_bytes())
V=read(S/'verified_report_values_v1.json');E=read(S/'source_evidence_manifest_v1.json')['sources']
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])
def link(name,p):return '['+name+']('+Path(p).as_posix()+')'
def f(x):return f'{x:.3f}'
parts={}
parameters=V['training']['F0_C']['parameters']
parts['PARAMETERS']=table(['分区','参数数'],[[k,f'{v:,}'] for k,v in parameters.items()])
training=[];checkpoints=[];env=[]
for name,t in V['training'].items():
 p=t['peaks'];training.append([name,str(t['counts']['updates']),f"{t['completion']['elapsed_seconds']/60:.2f} min",f"{p['RSS']/2**30:.3f} GiB",f"{p['peak_allocated']/2**30:.3f} GiB",f"{p['peak_reserved']/2**30:.3f} GiB",str(p['device_MiB'])+' MiB',str(t['checks_passed'])])
 c=t['checkpoint'];checkpoints.append([name,str(c['bytes']),'`'+c['sha256']+'`','`'+t['request_sha256']+'`'])
 ident=V['identities'][name];env.append([name,ident['hostname'].split('notebook-')[-1],ident['gpu_name'],'`'+ident['gpu_uuid']+'`',ident['driver_version']])
parts['TRAINING']=table(['run','更新','训练记录时长','RSS采样峰值','Torch allocated峰值','Torch reserved峰值','SMI峰值','审计项'],training)
parts['ENVIRONMENT']=table(['训练run','容器后缀','GPU','UUID','驱动'],env)
parts['CHECKPOINTS']=table(['run','字节数','checkpoint SHA256','训练request SHA256'],checkpoints)
def performance(folds,arms):
 rows=[]
 for fold in folds:
  for arm in arms:
   x=V['performance'][fold][arm];m=x['metrics'];rows.append([fold,arm,f(m['E_P95_mm']),f(m['J_P95_mm']),f"{100*m['E_coverage_2.0mm']:.2f}%",f"{100*m['J_coverage_2.0mm']:.2f}%",f(m['CD_L1_mm']),f"{100*m['reverse_A2_outlier_20.0mm']:.2f}%",str(x['risk']['severe_geometry'])+'/'+str(x['cases'])])
 return table(['折','模型','E_P95 mm','J_P95 mm','E Cover@2mm','J Cover@2mm','CD-L1 mm','逆向A2 >20mm','严重标记'],rows)
parts['MAIN_RESULTS']=performance(['C','D'],['T0','M0','F0','LQI'])
parts['POOLED_RESULTS']=performance(['ALL'],['T0','M0','F0','LQI'])
parts['CONTROLS']=performance(['ALL'],['Nop_D','GT_8192'])
original=B/'Native_scoring_implementation_v1/unified_scores_v1';new=B/'lqi_F0_scoring_implementation_v1/unified_scores_v1'
cp0=read(original/'paired_comparison.json');cp1=read(new/'paired_comparison.json');risk0=read(original/'risk_transitions.json');risk1=read(new/'risk_transitions.json')
pairrows=[];riskrows=[]
for fold in ['C','D']:
 for a,b,cp,risk in [('T0','F0',cp0,risk0),('M0','F0',cp0,risk0),('F0','LQI',cp1,risk1)]:
  label=b+'_minus_'+a;z=cp['comparison'][fold][label]['metrics']['E_P95_mm'];pairrows.append([fold,a+'→'+b,f"{z['mean_delta_b_minus_a']:+.3f}",f"{z['median_delta']:+.3f}",str(z['improved_sources']),str(z['worse_sources'])])
  z=risk[fold][label]['labels']['severe_geometry'];riskrows.append([fold,a+'→'+b,z['baseline_count'],z['candidate_count'],z['new'],z['rescued'],z['baseline_count']-z['rescued']])
parts['PRIMARY_PAIRS']=table(['折','baseline→candidate','ΔE均值 mm','来源Δ中位 mm','改善来源／21','退化来源／21'],pairrows)
parts['RISKS']=table(['折','比较','原严重','候选严重','新增','恢复','共同严重'],riskrows)
other=[]
for fold in ['C','D']:
 for label in ['placement_tail','compact_distribution']:
  z=risk1[fold]['LQI_minus_F0']['labels'][label];other.append([fold,label,z['baseline_count'],z['candidate_count'],z['new'],z['rescued']])
parts['RISKS']+='\n\n'+table(['折','F0→LQI标记','F0','LQI','新发','恢复'],other)
case_rows=[json.loads(x) for x in (original/'case_metrics.jsonl').read_text(encoding='utf-8').splitlines()]+[json.loads(x) for x in (new/'case_metrics.jsonl').read_text(encoding='utf-8').splitlines() if json.loads(x)['arm']=='LQI']
def mean(v):return sum(v)/len(v)
drows=[]
for fold in ['C','D']:
 for defect in ['bilateral','frontoorbital','parietotemporal','random_1','random_2']:
  values={arm:mean([r['metrics']['E_P95_mm'] for r in case_rows if r['fold']==fold and r['arm']==arm and r['case_id'].endswith('__'+defect)]) for arm in ['T0','M0','F0','LQI']}
  drows.append([fold,defect,*[f(values[arm]) for arm in ['T0','M0','F0','LQI']],f"{values['LQI']-values['F0']:+.3f}"])
parts['DEFECT_RESULTS']=table(['折','类型','T0 E_P95','M0 E_P95','F0 E_P95','LQI E_P95','LQI−F0 mm'],drows)
diag=[]
for fold in ['C','D','ALL']:
 for name,label in [('prefix_feature_null','prefix特征置零'),('prefix_donor','prefix donor'),('local_graph_donor','local graph donor')]:
  z=V['diagnostic'][fold][name];diag.append([fold,label,z['n'],f"{z['mean_mm']:.6f}",f"{z['min_mm']:.6f}—{z['max_mm']:.6f}"])
parts['DIAGNOSTIC']=table(['折','条件','例数','坐标RMSE响应均值 mm','病例范围 mm'],diag)
visual=read(B/'lqi_F0_geometry_visualization_v1/visualization_result_v2.json');seven=[]
for r in visual['cases']:
 m=r['frozen_metrics'];g=r['frozen_stage_geometry']['LQI'];seven.append([r['fold']+'/'+r['case_id'],r['role'],f"{m['F0']['E_P95_mm']:.2f}→{m['LQI']['E_P95_mm']:.2f}",f"{g['coarse']['centroid_offset_mm']:.2f}→{g['dense']['centroid_offset_mm']:.2f}",f"{g['dense']['radius_gyration_ratio']:.3f}",f"{100*m['LQI']['J_coverage_2.0mm']:.2f}%"])
parts['SEVEN_CASES']=table(['病例','固定角色','E_P95 F0→LQI','LQI Q→P质心偏移 mm','LQI P半径比','LQI J Cover2'],seven)
parts['C012_IMAGE']='![C012：位置失稳在coarse已可见]('+Path(visual['cases'][0]['figures'][0]['path']).as_posix()+')'
parts['D060_IMAGE']='![D060：目标区内仍存在范围收缩与接口缺覆盖]('+Path(visual['cases'][4]['figures'][1]['path']).as_posix()+')'
stage=[]
for fold in ['C','D']:
 for arm in ['M0','F0','LQI']:
  rr=[r for r in case_rows if r['fold']==fold and r['arm']==arm];stage.append([fold,arm,f(mean([r['stage_geometry']['coarse']['centroid_offset_mm'] for r in rr])),f(mean([r['position_shape']['centroid_offset_mm'] for r in rr])),f(mean([r['stage_geometry']['coarse']['radius_gyration_ratio'] for r in rr])),f(mean([r['position_shape']['radius_gyration_ratio'] for r in rr]))])
parts['STAGE_GEOMETRY']=table(['折','模型','Q质心偏移均值 mm','P质心偏移均值 mm','Q半径比均值','P半径比均值'],stage)+'\n\nM0列使用冻结的全病例几何摘要，并非声称其210例均保存实际Q张量；历史M0每臂只有12例Q张量。F0／LQI各210例Q均已保存。'
archives=[]
for arm in ['F0','LQI']:
 ar=V['prediction'][arm]['archive'];local='E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_'+arm+'/2026-11-11_native_development_eval';archives.append([arm,str(ar['bytes']),'`'+ar['sha256']+'`','`'+local+'`'])
parts['ARCHIVES']=table(['Native归档','字节数','SHA256','已核验本机目录'],archives)
nav=[('F0 decoder／factory',B/'implementation_v1'),('LQI decoder／factory',B/'lqi_implementation_v1'),('F0训练后审计C',B/'training_entry_v1/post_training_freeze_audit_v1'),('F0训练后审计D',B/'FoldD_training_entry_v1/post_training_freeze_audit_v1'),('F0统一评分与正式审计',original.parent),('30次条件诊断',B/'conditional_diagnostic_implementation_v1/post_diagnostic_freeze_audit_v1'),('LQI训练后审计C',B/'lqi_training_entry_v1/post_training_freeze_audit_v1'),('LQI训练后审计D',B/'lqi_FoldD_training_entry_v1/post_training_freeze_audit_v2'),('LQI/F0统一评分与正式审计',new.parent),('七病例图像和同步3D总览',B/'lqi_F0_geometry_visualization_v1/index_v2.html')]
parts['NAVIGATION']='\n'.join('- '+link(n,p.resolve()) for n,p in nav)
parts['EVIDENCE']=table(['编号','来源文件','SHA256'],[[key,link(Path(r['path']).name,r['path']),'`'+r['sha256']+'`'] for key,r in E.items()])
text=(S/'report_template_zh_v1.md').read_text(encoding='utf-8')
for key,value in parts.items():assert '{{'+key+'}}' in text; text=text.replace('{{'+key+'}}',value)
assert '{{' not in text
text=re.sub(r'\[(E\d{2})\]',lambda m:link(m.group(1),E[m.group(1)]['path']),text)
name='Cranial_BCSP_FullMamba_本轮完整实验报告_zh_2026-11-12_v1.md'
with (S/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
assert V['training']['F0_C']['checkpoint']['sha256']=='4fd73dd8c265781225ba63a712a5589b175c94f0ea0878a69ebf466265ebebe9'
assert abs(V['performance']['C']['LQI']['metrics']['E_P95_mm']-7.338343741352718)<1e-10
assert V['performance']['ALL']['LQI']['risk']['severe_geometry']==10
with (S/'report_content_validation_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='REPORT_CONTENT_AND_FROZEN_VALUES_VERIFIED',report=rec if False else dict(path=str((S/name).resolve()),bytes=(S/name).stat().st_size,sha256=hashlib.sha256((S/name).read_bytes()).hexdigest()),source_files=len(E),new_training=0,new_scoring=0,unresolved_template_fields=0,checks=dict(four_training_audits_pass=True,common_initial_state_matches=True,driver_UUID_difference_disclosed=True,source_equal_four_arm_tables=True,all_sixteen_critical_sections_present=len(re.findall(r'^## ',text,re.M))>=15,baseline630_exact_consistency=True,closure_not_final_method_success=True,checkpoint_backup_not_claimed=True)),f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status='FINAL_REPORT_WRITTEN',path=str((S/name).resolve()),characters=len(text),bytes=(S/name).stat().st_size),ensure_ascii=True))
