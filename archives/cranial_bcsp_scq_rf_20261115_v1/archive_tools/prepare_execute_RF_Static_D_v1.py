"""Frozen Static_D execution calls on the specifically accepted new device."""
from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent;S=R/'local_tools'
src=(S/'execute_RF_Requery_D_training_once_v1.py').read_text(encoding='utf-8-sig')
changes=[('scq_rf_Requery_D_implementation_20261115_v1','scq_rf_Static_D_implementation_20261115_v1'),('4a79f67d7ce29b453343d9bedc27841030d4c6223eb7bfe02d3af1d1bed9f6ed','b89d2b8d1fea63bcc4fb0478dce4d283a57b6b774beb7ccd7fe0403ceb71b6d6'),('SCQ_RF_Requery_D_training_execution_request_v1.json','SCQ_RF_Static_D_training_execution_request_v1.json'),('bcsp_scq_rf_Requery_D_training_entry_v1.py','bcsp_scq_rf_Static_D_training_entry_v1.py'),("len(mp['files'])==10","len(mp['files'])==13"),('len(lines)==len(expected)==11','len(lines)==len(expected)==14'),('len(ms)==11 and len({m.name for m in ms})==11','len(ms)==14 and len({m.name for m in ms})==14'),('members=11','members=14'),('len(rows)==10','len(rows)==13'),('TEN_FILES_EXCLUSIVE_INSTALL_PASS','THIRTEEN_FILES_EXCLUSIVE_INSTALL_PASS'),('files=10','files=13'),('SINGLE_RF_REQUERY_D_TRAINING','SINGLE_RF_STATIC_D_TRAINING'),("arm='RF-Requery'","arm='RF-Static'")]
for a,b in changes:
 assert a in src,a
 src=src.replace(a,b)
src=src.replace('automatic_retry=False))','automatic_retry=False,cross_device_D_comparison=True,historical_identity=q[\'historical_identity\'],execution_identity=q[\'identity\']))')
ast.parse(src)
with (S/'execute_RF_Static_D_training_once_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(src)
obs=(S/'observe_RF_Requery_D_training_v1.py').read_text(encoding='utf-8-sig')
for a,b in [changes[0],changes[2]]:obs=obs.replace(a,b)
ast.parse(obs)
with (S/'observe_RF_Static_D_training_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(obs)
print('STATIC_D_EXECUTION_AND_READONLY_OBSERVER_PREPARED')
