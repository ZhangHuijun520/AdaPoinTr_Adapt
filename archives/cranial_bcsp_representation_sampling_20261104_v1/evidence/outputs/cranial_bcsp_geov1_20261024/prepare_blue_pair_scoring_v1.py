"""Minimal label/schema adaptation of proven CPU scoring and artificial tests."""
import ast,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;N=B/'blue_pair_eval_v1';S=N/'score_implementation_v1'
OLD=B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1/score_implementation_v1'
v=json.loads((N/'local_download_verification_v1/verification_result_v1.json').read_bytes())
assert v['status']=='LOCAL_DOWNLOADED_PREDICTION_ARCHIVE_VERIFIED' and v['local_backup_verified']
S.mkdir()
changes=[('bcsp-sampling-pair-','bcsp-blue-noise-pair-'),('bcsp_sampling_pair_score_v1','bcsp_blue_pair_score_v1'),('SAMPLING_PAIR_210_FORWARD_COMPLETE','BLUE_NOISE_PAIR_210_FORWARD_COMPLETE'),('mean_delta_Morton_minus_V1','mean_delta_graph_minus_Euclidean'),('mean_V1','mean_Euclidean'),('mean_Morton','mean_graph'),('Nop_D_V1','Nop_D_Euclidean_elimination'),('Morton_area_stratified8k','surface_graph'),("'V1'","'Euclidean_elimination'")]
records=[]
for oldname,newname in [('bcsp_sampling_pair_score_v1.py','bcsp_blue_pair_score_v1.py'),('test_pair_score_contract_v1.py','test_pair_score_contract_v1.py')]:
    p=OLD/oldname;s=p.read_text(encoding='utf-8')
    for old,new in changes:s=s.replace(old,new)
    if newname.startswith('test_'):s=s.replace("N.parents[2]/'development_eval_v1/bcsp_eval_metrics_v1.py'","N.parents[1]/'development_eval_v1/bcsp_eval_metrics_v1.py'")
    ast.parse(s)
    out=S/newname
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
    records.append({'parent':str(p),'parent_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'candidate':str(out),'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
assert (N/'bcsp_eval_metrics_v1.py').read_bytes()==(B/'development_eval_v1/bcsp_eval_metrics_v1.py').read_bytes()
with (S/'implementation_derivation_v1.json').open('x') as f:json.dump({'status':'STATIC_PASS_NO_REAL_SCORING','files':records,'changes':'exact arm/schema/archive status names and descriptive result-key labels; test reference path only','unchanged':['metric source bytes','scoring math and units','five fixed defects then source-equal aggregation','525 score rows including315 CPU controls','all cases retained','no bootstrap/p-values/formal gate','one-way explicit authorization','resource ceilings'],'real_score_calls':0,'server_calls':0},f,indent=2)
print('BLUE_PAIR_CPU_SCORER_STATIC_PASS_NO_REAL_METRIC_CALLS')
