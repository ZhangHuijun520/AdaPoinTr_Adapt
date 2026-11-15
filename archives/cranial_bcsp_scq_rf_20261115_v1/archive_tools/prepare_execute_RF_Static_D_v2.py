"""Version only local transport/install/launch calls for separately authorized v2."""
from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent;S=R/'local_tools'
src=(S/'execute_RF_Static_D_training_once_v1.py').read_text(encoding='utf-8-sig')
changes=[("outputs/scq_rf_Static_D_implementation_20261115_v1'","outputs/scq_rf_Static_D_implementation_20261115_v1/selector_diagnostic_hotfix_v2'"),('b89d2b8d1fea63bcc4fb0478dce4d283a57b6b774beb7ccd7fe0403ceb71b6d6','9d7ac459e9a969c36df67ddaee4c5c0aaac2c68b322dcf58097c54f59caa402b'),('pending_transport_v1','pending_transport_v2'),('authorized_execution_v1','authorized_execution_v2'),('authorized_execution_static_v1','authorized_execution_static_v2'),('SCQ_RF_Static_D_training_execution_request_v1.json','SCQ_RF_Static_D_training_execution_request_v2.json'),('installation_mapping_v1.json','installation_mapping_v2.json'),('delivery_v1.json','delivery_v2.json'),('bcsp_scq_rf_Static_D_training_entry_v1.py','bcsp_scq_rf_Static_D_training_entry_v2.py'),('authorization_v1.json','authorization_v2.json'),('runtime_v1.json','runtime_v2.json'),('launch_once_v1.sh','launch_once_v2.sh'),("len(mp['files'])==13","len(mp['files'])==8"),('len(lines)==len(expected)==14','len(lines)==len(expected)==9'),('len(ms)==14 and len({m.name for m in ms})==14','len(ms)==9 and len({m.name for m in ms})==9'),('members=14','members=9'),('len(rows)==13','len(rows)==8'),('THIRTEEN_FILES_EXCLUSIVE_INSTALL_PASS','EIGHT_FILES_EXCLUSIVE_INSTALL_PASS'),('files=13','files=8'),('已上传，单独授权上述完整哈希。','已上传，单独授权该完整哈希。')]
for a,b in changes:
 assert a in src,a
 src=src.replace(a,b)
ast.parse(src)
with (S/'execute_RF_Static_D_training_once_v2.py').open('x',encoding='utf-8',newline='\n') as f:f.write(src)
obs=(S/'observe_RF_Static_D_training_v1.py').read_text(encoding='utf-8-sig')
for a,b in [changes[0],changes[2],changes[3],changes[5]]:obs=obs.replace(a,b)
obs=obs.replace("['completion.json','failure.json','startup_failure.json']","['completion.json','failure.json','startup_failure.json','startup_monitor_failure.json']")
ast.parse(obs)
with (S/'observe_RF_Static_D_training_v2.py').open('x',encoding='utf-8',newline='\n') as f:f.write(obs)
print('STATIC_D_V2_EXECUTION_AND_READONLY_OBSERVER_PREPARED')
