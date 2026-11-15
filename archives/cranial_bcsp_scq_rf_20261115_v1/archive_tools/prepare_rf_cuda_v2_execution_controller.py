"""Adapt only local installation/observation calls to the frozen v2 request."""
from pathlib import Path
import ast

R=Path(__file__).resolve().parent.parent
S=R/'local_tools'
oldsha='85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32'
newsha='09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf'
code=(S/'execute_scq_rf_cuda_once_v1.py').read_text(encoding='utf-8')
for old,new in [('scq_rf_cuda_preparation_20261114_v1','scq_rf_cuda_preparation_20261114_v2'),
                ('pending_transport_v1','pending_transport_v2'),('authorized_execution_v1','authorized_execution_v2'),
                ('authorized_execution_static_v1','authorized_execution_static_v2'),(oldsha,newsha),
                ('SCQ_RF_artificial_cuda_execution_request_v1.json','SCQ_RF_artificial_cuda_execution_request_v2.json'),
                ('installation_mapping_v1.json','installation_mapping_v2.json'),('pending_delivery_v1.json','pending_delivery_v2.json'),
                ('bcsp_scq_rf_cuda_admission_v1.py','bcsp_scq_rf_cuda_admission_v2.py'),
                ("len(mp['files'])==12","len(mp['files'])==7"),('len(lines)==len(expected)==13','len(lines)==len(expected)==8'),
                ('len(ms)==13 and len({m.name for m in ms})==13','len(ms)==8 and len({m.name for m in ms})==8'),
                ('members=13','members=8'),('len(rows)==12','len(rows)==7'),('TWELVE_FILES_EXCLUSIVE_INSTALL_PASS','SEVEN_FILES_EXCLUSIVE_INSTALL_PASS'),
                ('files=12','files=7'),('authorization_v1.json','authorization_v2.json'),('runtime_v1.json','runtime_v2.json'),
                ('launch_once_v1.sh','launch_once_v2.sh')]:
    assert old in code,old
    code=code.replace(old,new)
target=S/'execute_scq_rf_cuda_once_v2.py';compile(code,str(target),'exec')
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(code)
observer=(S/'observe_scq_rf_cuda_v1.py').read_text(encoding='utf-8')
for old,new in [('scq_rf_cuda_preparation_20261114_v1','scq_rf_cuda_preparation_20261114_v2'),
                ('authorized_execution_v1','authorized_execution_v2'),('pending_transport_v1','pending_transport_v2'),
                ('SCQ_RF_artificial_cuda_execution_request_v1.json','SCQ_RF_artificial_cuda_execution_request_v2.json'),(oldsha,newsha)]:
    assert old in observer;observer=observer.replace(old,new)
target=S/'observe_scq_rf_cuda_v2.py';compile(observer,str(target),'exec')
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(observer)
print('V2_LOCAL_CALLS_PREPARED_NOT_EXECUTED')
