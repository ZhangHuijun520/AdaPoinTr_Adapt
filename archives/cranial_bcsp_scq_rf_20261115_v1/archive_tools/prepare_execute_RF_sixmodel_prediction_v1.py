from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
s=(R/'local_tools/execute_scq_BS_CD_prediction_once_v2.py').read_text(encoding='utf-8')
s=s.replace('outputs/cranial_bcsp_scq_BS_CD_native_prediction_preparation_20261114_v1/implementation_v1/resource_rebind_v2','outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1')
s=s.replace("B=S/'pending_request_v2'", "B=S/'pending_request_v1'")
s=s.replace('ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a','b503b487e2ed3a00b60400f2e71c98a2d56931dbdf25a77ff32e717b4ff1e561')
for a,b in [('SCQ_BS_CD_native_prediction_execution_request_v2.json','SCQ_RF_sixmodel_native_prediction_execution_request_v1.json'),('installation_mapping_v2.json','installation_mapping_v1.json'),('delivery_receipt_v2.json','delivery_receipt_v1.json'),('SCQ_BS_CD_input_index_v2.json','RF_sixmodel_input_index_v1.json'),('bcsp_scq_fourmodel_native_predict_v2.py','bcsp_scq_rf_sixmodel_native_predict_v1.py'),('local_mirror_v2.json','local_mirror_v1.json'),('preexecution_static_v2','preexecution_static_v1'),('review_v2.json','review_v1.json'),('authorization_v2.json','authorization_v1.json'),('runtime_v2.json','runtime_v1.json'),('launch_once_v2.sh','launch_once_v1.sh'),('launch_receipt_v2.json','launch_receipt_v1.json')]:s=s.replace(a,b)
s=s.replace('420','630').replace('len(ms)==len(expected)==19','len(ms)==len(expected)==17').replace('len({m.name for m in ms})==19','len({m.name for m in ms})==17').replace('members=19','members=17').replace('len(rows)==18','len(rows)==16').replace('EIGHTEEN_FILES_EXCLUSIVE_INSTALL_PASS','SIXTEEN_FILES_EXCLUSIVE_INSTALL_PASS').replace('files=18','files=16').replace('len(runs)==4','len(runs)==6')
# Read frozen scope through its verified local mirror, without assuming another experiment folder.
s=s.replace("scopepath=R/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/artificial_gpu_zero_update_frozen_scope_v3.json'", "scopepath=Path(mirror[q['preflight_scope']['path']])")
# Perform cheaper input availability check before full dependencies/checkpoints or any mutation.
s=s.replace("if '--static' in sys.argv:", "scripts.sort(key=lambda row: 0 if row[0]=='identity_resources' else 1 if row[0]=='upload' else 2 if row[0]=='inputs210' else 3)\nif '--static' in sys.argv:")
ast.parse(s)
p=R/'local_tools/execute_RF_sixmodel_prediction_once_v1.py'
with p.open('x',encoding='utf-8') as f:f.write(s)
print(p)
