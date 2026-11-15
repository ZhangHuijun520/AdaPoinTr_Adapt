"""Finite versioning of the proven byte-preserving launch controller for Sref_D."""
from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent;S=R/'local_tools'
src=(S/'execute_RF_Static_C_training_once_v1.py').read_text(encoding='utf-8-sig')
changes=[('scq_rf_Static_C_implementation_20261114_v1','scq_rf_Sref_D_implementation_20261114_v1'),('a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f','888ad3b1a519d26ba907b061643e602aafe42df0e0006c7d0606d242e9a5c00d'),('SCQ_RF_Static_C_training_execution_request_v1.json','SCQ_RF_Sref_D_training_execution_request_v1.json'),('bcsp_scq_rf_Static_C_training_entry_v1.py','bcsp_scq_rf_Sref_D_training_entry_v1.py'),("len(mp['files'])==8","len(mp['files'])==11"),('len(lines)==len(expected)==9','len(lines)==len(expected)==12'),('len(ms)==9 and len({m.name for m in ms})==9','len(ms)==12 and len({m.name for m in ms})==12'),('members=9','members=12'),('len(rows)==8','len(rows)==11'),('EIGHT_FILES_EXCLUSIVE_INSTALL_PASS','ELEVEN_FILES_EXCLUSIVE_INSTALL_PASS'),('files=8','files=11'),("['folds']['C']","['folds']['D']"),('SINGLE_RF_STATIC_C_TRAINING','SINGLE_RF_SREF_D_TRAINING'),("arm='RF-Static',fold='C'","arm='S-ref',fold='D'")]
for old,new in changes:
 assert old in src,old
 src=src.replace(old,new)
ast.parse(src)
with (S/'execute_RF_Sref_D_training_once_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(src)
obs=(S/'observe_RF_Static_C_training_v1.py').read_text(encoding='utf-8-sig')
for old,new in [changes[0],changes[2]]:obs=obs.replace(old,new)
ast.parse(obs)
with (S/'observe_RF_Sref_D_training_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(obs)
print('SREF_D_EXECUTION_AND_READONLY_OBSERVER_PREPARED')
