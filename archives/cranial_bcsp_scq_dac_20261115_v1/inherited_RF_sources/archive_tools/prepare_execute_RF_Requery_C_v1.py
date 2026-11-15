"""Reuse the verified finite installation/launch controller for Requery_C."""
from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent;S=R/'local_tools'
src=(S/'execute_RF_Static_C_training_once_v1.py').read_text(encoding='utf-8-sig')
for old,new in [('scq_rf_Static_C_implementation_20261114_v1','scq_rf_Requery_C_implementation_20261114_v1'),('a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f','27ef5aaa1c5aa1cc246e8c45597981d0233651dfbacf7621637a8a7b367a9497'),('SCQ_RF_Static_C_training_execution_request_v1.json','SCQ_RF_Requery_C_training_execution_request_v1.json'),('bcsp_scq_rf_Static_C_training_entry_v1.py','bcsp_scq_rf_Requery_C_training_entry_v1.py'),("len(mp['files'])==8","len(mp['files'])==9"),('len(lines)==len(expected)==9','len(lines)==len(expected)==10'),('len(ms)==9 and len({m.name for m in ms})==9','len(ms)==10 and len({m.name for m in ms})==10'),('members=9','members=10'),('len(rows)==8','len(rows)==9'),('EIGHT_FILES_EXCLUSIVE_INSTALL_PASS','NINE_FILES_EXCLUSIVE_INSTALL_PASS'),('files=8','files=9'),('SINGLE_RF_STATIC_C_TRAINING','SINGLE_RF_REQUERY_C_TRAINING'),("arm='RF-Static'","arm='RF-Requery'")]:
 assert old in src,old
 src=src.replace(old,new)
ast.parse(src)
with (S/'execute_RF_Requery_C_training_once_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(src)
obs=(S/'observe_RF_Static_C_training_v1.py').read_text(encoding='utf-8-sig').replace('scq_rf_Static_C_implementation_20261114_v1','scq_rf_Requery_C_implementation_20261114_v1').replace('SCQ_RF_Static_C_training_execution_request_v1.json','SCQ_RF_Requery_C_training_execution_request_v1.json')
ast.parse(obs)
with (S/'observe_RF_Requery_C_training_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(obs)
print('REQUERY_C_EXECUTION_AND_READONLY_OBSERVER_PREPARED')
