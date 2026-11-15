"""Bind local call adaptation to pending v3 without altering request or runtime code."""
from pathlib import Path

R=Path(__file__).resolve().parent.parent
S=R/'local_tools'
oldsha='09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf'
newsha='8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac'
code=(S/'execute_scq_rf_cuda_once_v2.py').read_text(encoding='utf-8')
changes=[('scq_rf_cuda_preparation_20261114_v2','scq_rf_initialization_loader_20261114_v2'),
         ('pending_transport_v2','pending_transport_v3'),('authorized_execution_v2','authorized_execution_v3'),
         ('authorized_execution_static_v2','authorized_execution_static_v3'),(oldsha,newsha),
         ('SCQ_RF_artificial_cuda_execution_request_v2.json','SCQ_RF_artificial_cuda_execution_request_v3.json'),
         ('installation_mapping_v2.json','installation_mapping_v3.json'),('pending_delivery_v2.json','pending_delivery_v3.json'),
         ("len(mp['files'])==7","len(mp['files'])==8"),('len(lines)==len(expected)==8','len(lines)==len(expected)==9'),
         ('len(ms)==8 and len({m.name for m in ms})==8','len(ms)==9 and len({m.name for m in ms})==9'),
         ('members=8','members=9'),('len(rows)==7','len(rows)==8'),('SEVEN_FILES_EXCLUSIVE_INSTALL_PASS','EIGHT_FILES_EXCLUSIVE_INSTALL_PASS'),
         ('files=7','files=8'),('authorization_v2.json','authorization_v3.json'),('runtime_v2.json','runtime_v3.json'),('launch_once_v2.sh','launch_once_v3.sh')]
for a,b in changes:
    assert a in code,a
    code=code.replace(a,b)
old="spec=importlib.util.spec_from_file_location('RF_launcher_renderer_only',B/'bcsp_scq_rf_cuda_admission_v2.py')"
new="renderer=R/'outputs/scq_rf_cuda_preparation_20261114_v2/bcsp_scq_rf_cuda_admission_v2.py'\nassert sha(renderer)==q['entry']['sha256']\nspec=importlib.util.spec_from_file_location('RF_launcher_renderer_only',renderer)"
assert old in code;code=code.replace(old,new)
target=S/'execute_scq_rf_cuda_once_v3.py';compile(code,str(target),'exec')
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(code)
observer=(S/'observe_scq_rf_cuda_v2.py').read_text(encoding='utf-8')
for a,b in changes[:6]:
    if a in observer:observer=observer.replace(a,b)
observer=observer.replace('SCQ_RF_artificial_cuda_execution_request_v2.json','SCQ_RF_artificial_cuda_execution_request_v3.json')
target=S/'observe_scq_rf_cuda_v3.py';compile(observer,str(target),'exec')
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(observer)
print('V3_LOCAL_CALL_ADAPTATION_PREPARED')
