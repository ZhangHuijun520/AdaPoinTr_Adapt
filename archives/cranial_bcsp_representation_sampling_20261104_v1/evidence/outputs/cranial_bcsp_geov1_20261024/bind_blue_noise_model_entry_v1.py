"""Finalize only local new-stage contract/runtime/entry after data preparation."""
import ast,hashlib,json,shutil,sys
from pathlib import Path
B=Path(__file__).resolve().parent;ROOT=B.parents[1];O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1'
OLD=B/'sampling_model_AB_foldC_seed0_20261103_v1/implementation';I=O/'implementation';STAGE='BCSP_BLUE_NOISE_AB_V1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def textsha(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
def write(p,s):
    with p.open('x',encoding='utf-8',newline='') as f:f.write(s)
def dump(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False))

def main():
    completion=json.loads((O/'data_preparation_completion.json').read_text())
    assert completion['status']=='PAIRED_FOLD_C_DATA_PREPARED_NOT_TRAINING_AUTHORIZED'
    manifest=json.loads((O/'data_artifact_manifest.json').read_text())
    assert all(sha(O/p)==v['sha256'] for p,v in manifest.items())
    parent=json.loads((B/'sampling_model_AB_foldC_seed0_20261103_v1/V1_training_entry_request_v1.json').read_text())
    for role in ['contract','runtime','entry']:
        assert sha(OLD/('bcsp_sampling_training_'+role+'_v1.py'))==parent['implementation'][role]['sha256']
    assert not I.exists();I.mkdir()
    runtime=(OLD/'bcsp_sampling_training_runtime_v1.py').read_text(encoding='utf-8').replace('BCSP_SAMPLING_AB_V1',STAGE)
    write(I/'bcsp_blue_noise_training_runtime_v1.py',runtime)
    contract=(OLD/'bcsp_sampling_training_contract_v1.py').read_text(encoding='utf-8')
    contract=contract.replace('BCSP_SAMPLING_AB_V1',STAGE).replace("ARMS=('V1','Morton_area_stratified8k')","ARMS=('Euclidean_elimination','surface_graph')")
    contract=contract.replace('bcsp-sampling-','bcsp-blue-noise-').replace("q['arm']=='V1'","q['arm']==ARMS[0]")
    contract=contract.replace('bcsp_sampling_ab_foldC_V1_in8192_out8192_seed0_train_v1','bcsp_blue_noise_foldC_Euclidean_elimination_in8192_out8192_seed0_train_v1')
    anchor="    require(set(records)==set(ARMS),'exact two sampler arms')"
    assert contract.count(anchor)==1
    contract=contract.replace(anchor,anchor+"\n    require(qc.get('stage')==STAGE and qc.get('comparison_split')=='train','new-stage training receipt only')")
    anchor="            require(r['sampler_arm']==a and r['sampling_seed']==0,'fixed sampler identity')"
    assert contract.count(anchor)==1
    contract=contract.replace(anchor,anchor+"\n            require(r.get('comparison_stage')==STAGE and r.get('comparison_split')=='train','new-stage train records only')")
    anchor="def validate_rebind(record,scope_record,gpu_record):\n"
    assert contract.count(anchor)==1
    contract=contract.replace(anchor,anchor+"    value=IMMUTABLE['resource_binding']\n    require(isinstance(value,str) and len(value)==64 and set(value)<=set('0123456789abcdef'),'current server resource binding not finalized')\n")
    contract=contract[:contract.index('IMMUTABLE = ')]
    imm={'static_config':sha(O/'static_training_config_v1.json'),'order_plan':sha(O/'shared_order_foldC_seed0_v1.json'),
         'training_runtime':textsha(runtime),'resource_binding':'UNBOUND_PENDING_CURRENT_SERVER_READINESS'}
    contract+='IMMUTABLE = '+repr(imm)+'\n'
    write(I/'bcsp_blue_noise_training_contract_v1.py',contract)
    entry=(OLD/'bcsp_sampling_training_entry_v1.py').read_text(encoding='utf-8')
    entry=entry.replace('bcsp_sampling_training_contract_v1.py','bcsp_blue_noise_training_contract_v1.py')
    module=ast.parse(entry)
    constants={'CONTRACT_SHA':textsha(contract),'QC_SHA':sha(O/'paired_train_data_receipt.json'),
               'FOLD_SHA':sha(B/'consolidated_binding_v1/fold_binding.json')}
    for node in reversed(module.body):
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in constants:
            name=node.targets[0].id;lines=entry.splitlines(keepends=True);lines[node.lineno-1:node.end_lineno]=[name+' = '+repr(constants[name])+'\n'];entry=''.join(lines)
    write(I/'bcsp_blue_noise_training_entry_v1.py',entry)
    test=ROOT/'local_test_drivers/test_blue_noise_pair_entry_v1.py';shutil.copyfile(test,I/test.name)
    for p in I.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
    oldcfg=json.loads((B/'sampling_model_AB_foldC_seed0_20261103_v1/static_training_config_v1.json').read_text())
    newcfg=json.loads((O/'static_training_config_v1.json').read_text());assert {k:v for k,v in oldcfg.items() if k!='stage'}=={k:v for k,v in newcfg.items() if k!='stage'}
    assert not any('Morton_area_stratified8k' in p.read_text() for p in I.glob('bcsp_blue_noise*.py'))
    dump(O/'local_entry_binding.json',{'status':'LOCAL_CANDIDATE_BOUND_SERVER_RESOURCE_PENDING','stage':STAGE,
      'arms':['Euclidean_elimination','surface_graph'],'counts':newcfg['counts'],
      'immutable_local_data':imm,'entry_constants':constants,
      'implementation':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(I.glob('*.py'))},
      'parent_sources':{p.name:sha(p) for p in sorted(OLD.glob('bcsp_sampling*.py'))},
      'historical_parent_request_sha256':sha(B/'sampling_model_AB_foldC_seed0_20261103_v1/V1_training_entry_request_v1.json'),
      'changes':['new stage/arms/schema names','train/dev metadata identity','same initialization receipt now references fresh Euclidean baseline','final data/config/order/runtime hashes','bootstrap contract sibling/hash'],
      'unchanged':['model config','optimizer groups and schedules','exact training loop and3900 counting','FP32/TF32/AMP policy','memory thresholds','PID diagnostic-only policy','one-way authorization'],
      'execution_blocker':'resource_binding intentionally unbound until separately scoped current server readiness; no old GPU identity reuse',
      'no_request_runtime_launcher_or_real_authorization_created':True})
    print('LOCAL_ENTRY_STATIC_BINDING_PASS_SERVER_RESOURCE_PENDING')

if __name__=='__main__':main()
