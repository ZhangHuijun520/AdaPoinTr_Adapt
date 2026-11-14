"""Derive a dedicated F0/T0/M0 entry; parent and metric remain immutable."""
import ast,json,hashlib
from pathlib import Path
S=Path(__file__).resolve().parent;R=S.parents[2]
P=R/'outputs/cranial_bcsp_mamba_p2_20261106/H2_scoring_implementation_v1/bcsp_p2_h2_M0_three_arm_score_v1.py'
old=P.read_text(encoding='utf-8');tree=ast.parse(old);replacement=(S/'scorer_adaptations_source_v1.txt').read_text(encoding='utf-8')
custom=ast.parse(replacement);overrides={n.name:ast.get_source_segment(replacement,n) for n in custom.body if isinstance(n,ast.FunctionDef)}
result=[];modified=[]
for n in tree.body:
 code=ast.get_source_segment(old,n)
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):code='"""F0/T0/M0 CPU-only Native scoring. Inert with respect to real scores until separate authorization."""'
 elif isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='ARMS' for x in n.targets):code="ARMS=['T0','M0','F0']"
 elif isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PAIRS' for x in n.targets):code="PAIRS=[('M0','F0'),('T0','F0'),('T0','M0')]"
 elif isinstance(n,ast.FunctionDef) and n.name in overrides:code=overrides.pop(n.name);modified.append(n.name)
 elif isinstance(n,ast.FunctionDef) and n.name=='h2_offline_geometry':continue
 elif isinstance(n,ast.FunctionDef) and n.name=='run_scoring':
  code=code.replace('guard,start):','guard,start,prediction_bindings):')
  code=code.replace("coarse=pro['coarse_tensor_cases_by_fold'] if k=='H2' else {spec['fold']:pro['coarse_tensor_cases']}","coarse={f:[r['case_id'] for r in predindex['inputs'] if r['fold']==f] for f in ['C','D']} if k=='F0' else {spec['fold']:pro['coarse_tensor_cases']}")
  anchor="  for case in cases:"
  inserted="""  frozen={(r['fold'],r['arm'],r['case_id']):r for r in prediction_bindings}
  require(set(frozen)==set(lookup) and len(frozen)==len(prediction_bindings)==630,'all630 frozen prediction identities')
  for key,r in lookup.items():
   b=frozen[key];require(b['archive_key']==r['archive_key'] and b['member']==r['prediction']['name'] and b['bytes']==r['prediction']['bytes'] and b['sha256']==r['prediction']['sha256'] and b['coarse_saved']==r['coarse_expected'],'frozen member binding')
"""
  assert anchor in code;code=code.replace(anchor,inserted+anchor)
  code=code.replace("status='H2_THREE_ARM_TWOFOLD_SINGLE_SEED_DESCRIPTIVE_COMPARISONS',primary_comparison='H2_COUPLE_minus_H2_AUX',secondary_comparisons=['H2_COUPLE_minus_M0','H2_AUX_minus_M0']","status='F0_T0_M0_TWOFOLD_SINGLE_SEED_DESCRIPTIVE_COMPARISONS',fixed_comparisons=['F0_minus_M0','F0_minus_T0','M0_minus_T0'],primary_metric='A1 area-weighted E_P95 mm'")
  code=code.replace("LOCAL_H2_M0_THREE_ARM_TWOFOLD_CPU_SCORING_COMPLETE","LOCAL_F0_T0_M0_THREE_ARM_TWOFOLD_CPU_SCORING_COMPLETE");modified.append(n.name)
 elif isinstance(n,ast.FunctionDef) and n.name=='score_case':
  code='\n'.join(line for line in code.splitlines() if "if arm.startswith('H2_')" not in line);modified.append(n.name)
 result.append(code)
assert not overrides
target=S/'bcsp_f0_T0_M0_three_arm_score_v1.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write('\n\n'.join(result)+'\n')
ast.parse(target.read_text(encoding='utf-8'))
with (S/'source_derivation_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(parent=dict(path=str(P),sha256=hashlib.sha256(P.read_bytes()).hexdigest()),modified_functions=modified,removed_function='h2_offline_geometry',model_arms=['T0','M0','F0'],metric_changed=False),f,indent=2)
print(target)
