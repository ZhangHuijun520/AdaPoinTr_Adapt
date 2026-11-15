"""Version the proven local exclusive-install/single-launch calls for frozen Requery_D."""
from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent;S=R/'local_tools'
src=(S/'execute_RF_Requery_C_training_once_v1.py').read_text(encoding='utf-8-sig')
changes=[('scq_rf_Requery_C_implementation_20261114_v1','scq_rf_Requery_D_implementation_20261115_v1'),('27ef5aaa1c5aa1cc246e8c45597981d0233651dfbacf7621637a8a7b367a9497','4a79f67d7ce29b453343d9bedc27841030d4c6223eb7bfe02d3af1d1bed9f6ed'),('SCQ_RF_Requery_C_training_execution_request_v1.json','SCQ_RF_Requery_D_training_execution_request_v1.json'),('bcsp_scq_rf_Requery_C_training_entry_v1.py','bcsp_scq_rf_Requery_D_training_entry_v1.py'),("len(mp['files'])==9","len(mp['files'])==10"),('len(lines)==len(expected)==10','len(lines)==len(expected)==11'),('len(ms)==10 and len({m.name for m in ms})==10','len(ms)==11 and len({m.name for m in ms})==11'),('members=10','members=11'),('len(rows)==9','len(rows)==10'),('NINE_FILES_EXCLUSIVE_INSTALL_PASS','TEN_FILES_EXCLUSIVE_INSTALL_PASS'),('files=9','files=10'),("['folds']['C']","['folds']['D']"),('SINGLE_RF_REQUERY_C_TRAINING','SINGLE_RF_REQUERY_D_TRAINING'),("arm='RF-Requery',fold='C'","arm='RF-Requery',fold='D'")]
for a,b in changes:
 assert a in src,a
 src=src.replace(a,b)
ast.parse(src)
with (S/'execute_RF_Requery_D_training_once_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(src)
obs=(S/'observe_RF_Requery_C_training_v1.py').read_text(encoding='utf-8-sig')
for a,b in [changes[0],changes[2]]:obs=obs.replace(a,b)
ast.parse(obs)
with (S/'observe_RF_Requery_D_training_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(obs)
print('REQUERY_D_EXECUTION_AND_READONLY_OBSERVER_PREPARED')
