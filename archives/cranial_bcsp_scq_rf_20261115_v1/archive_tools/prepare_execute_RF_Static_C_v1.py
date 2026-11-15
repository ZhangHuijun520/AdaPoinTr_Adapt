"""Version the proven local byte-preserving controller for the authorized Static_C request."""
from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent;S=R/'local_tools'
src=(S/'execute_rf_Sref_C_training_once_v3.py').read_text(encoding='utf-8-sig')
changes=[("outputs/scq_rf_Sref_C_training_implementation_20261114_v1/startup_chain_binding_v3","outputs/scq_rf_Static_C_implementation_20261114_v1"),
('pending_transport_v3','pending_transport_v1'),('authorized_execution_v3','authorized_execution_v1'),('authorized_execution_static_v3','authorized_execution_static_v1'),
('6370a9887893b510c95850616eb664198982131df67d5e9a06ae725f9b860a88','a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f'),
('SCQ_RF_Sref_C_training_execution_request_v3.json','SCQ_RF_Static_C_training_execution_request_v1.json'),('installation_mapping_v3.json','installation_mapping_v1.json'),('delivery_v3.json','delivery_v1.json'),
('bcsp_scq_rf_Sref_C_training_entry_v3.py','bcsp_scq_rf_Static_C_training_entry_v1.py'),('authorization_v3.json','authorization_v1.json'),('runtime_v3.json','runtime_v1.json'),('launch_once_v3.sh','launch_once_v1.sh'),
("len(mp['files'])==7","len(mp['files'])==8"),('len(lines)==len(expected)==8','len(lines)==len(expected)==9'),('len(ms)==8 and len({m.name for m in ms})==8','len(ms)==9 and len({m.name for m in ms})==9'),('members=8','members=9'),('len(rows)==7','len(rows)==8'),('SEVEN_FILES_EXCLUSIVE_INSTALL_PASS','EIGHT_FILES_EXCLUSIVE_INSTALL_PASS'),('files=7','files=8'),
('SINGLE_RF_SREF_C_TRAINING_SUBMITTED','SINGLE_RF_STATIC_C_TRAINING_SUBMITTED'),('SINGLE_RF_SREF_C_TRAINING_ATTEMPT_SUBMITTED','SINGLE_RF_STATIC_C_TRAINING_ATTEMPT_SUBMITTED'),("arm='S-ref'","arm='RF-Static'"),
('已上传，对上述完整哈希单独执行授权。上下文完整SHA256：','已上传，单独授权上述完整哈希。上下文完整SHA256：')]
for a,b in changes:
 assert a in src,a
 src=src.replace(a,b)
ast.parse(src)
p=S/'execute_RF_Static_C_training_once_v1.py'
with p.open('x',encoding='utf-8',newline='\n') as f:f.write(src)
obs=(S/'observe_rf_Sref_C_training_v3_readonly_v2.py').read_text(encoding='utf-8-sig')
for a,b in changes[:2]+changes[2:3]+changes[5:6]:obs=obs.replace(a,b)
assert 'SCQ_RF_Static_C_training_execution_request_v1.json' in obs and 'startup_chain_binding_v3' not in obs
ast.parse(obs)
p=S/'observe_RF_Static_C_training_v1.py'
with p.open('x',encoding='utf-8',newline='\n') as f:f.write(obs)
print('STATIC_C_EXECUTION_AND_READONLY_OBSERVER_PREPARED')
