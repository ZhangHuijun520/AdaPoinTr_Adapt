"""One CPU metadata/full-authorize batch. RAM grants are not real authorization."""
import ast,copy,hashlib,importlib.util,json,sys,traceback
from pathlib import Path
I=Path(__file__).resolve().parent;O=I.parent;B=O.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def main():
    out=O/'cpu_contract_attempt_v1';out.mkdir(exist_ok=False)
    m=load('blue_noise_contract_fixture',I/'bcsp_blue_noise_training_contract_v1.py')
    qc=json.loads((O/'paired_train_data_receipt.json').read_text())
    records={a:[json.loads(s) for s in (O/a/'train_manifest_8192.jsonl').read_text().splitlines()] for a in m.ARMS}
    folds=json.loads((B/'consolidated_binding_v1/fold_binding.json').read_text())
    cfg=json.loads((O/'static_training_config_v1.json').read_text());plan=json.loads((O/'shared_order_foldC_seed0_v1.json').read_text())
    results=[]
    def test(name,fn):fn();results.append({'name':name,'status':'PASS'});print('PASS',len(results),name,flush=True)
    def reject(fn):
        try:fn()
        except (ValueError,KeyError):return
        raise AssertionError('invalid contract accepted')
    def call(q=qc,r=records,f=folds,fold='C',n=8192,a=None):return m.metadata_values(q,r,f,fold,n,m.ARMS[0] if a is None else a)
    def mutate_records(field,value):
        r=copy.deepcopy(records);r[m.ARMS[1]][0][field]=value;return r
    def valid():
        for arm in m.ARMS:assert len(call(a=arm)[0])==315
        assert m.validate_static(cfg)==cfg
    test('both new arms, 315 train and exact scientific static config',valid)
    def legacy():
        c=copy.deepcopy(cfg);c['stage']='BCSP_SAMPLING_AB_V1';reject(lambda:m.validate_static(c))
    test('prior sampling stage rejected',legacy)
    test('legacy Morton arm rejected',lambda:reject(lambda:call(a='Morton_area_stratified8k')))
    test('16k input rejected',lambda:reject(lambda:call(n=16384)))
    test('Fold D rejected',lambda:reject(lambda:call(fold='D')))
    def overlap():
        f=copy.deepcopy(folds);f['folds']['C']['dev_sources'][0]=f['folds']['C']['train_sources'][0];reject(lambda:call(f=f))
    test('train-development source overlap rejected',overlap)
    def missing():
        r=copy.deepcopy(records);r[m.ARMS[0]].pop();reject(lambda:call(r=r))
    test('missing training record rejected',missing)
    def duplicate():
        r=copy.deepcopy(records);r[m.ARMS[0]][1]=copy.deepcopy(r[m.ARMS[0]][0]);reject(lambda:call(r=r))
    test('duplicate or reordered training cases rejected',duplicate)
    test('development-labeled record rejected',lambda:reject(lambda:call(r=mutate_records('comparison_split','development'))))
    test('paired target drift rejected',lambda:reject(lambda:call(r=mutate_records('target_array_sha256','f'*64))))
    def frame():
        r=copy.deepcopy(records);r[m.ARMS[1]][0]['normalization']['scale']+=1;reject(lambda:call(r=r))
    test('paired frame drift rejected',frame)
    test('paired point-order drift rejected',lambda:reject(lambda:call(r=mutate_records('common_point_order_sha256','e'*64))))
    test('manifest stage drift rejected',lambda:reject(lambda:call(r=mutate_records('comparison_stage','BCSP_SAMPLING_AB_V1'))))
    def order():
        assert m.validate_order(plan,plan['case_ids'])==plan
        assert sum(len(e['batches']) for e in plan['epochs'])==3900
        assert sum(len(b) for e in plan['epochs'] for b in e['batches'])==31200
        assert sum(len(e['dropped']) for e in plan['epochs'])==300
        p=copy.deepcopy(plan);p['epochs'][0]['batches'].pop();reject(lambda:m.validate_order(p,plan['case_ids']))
    test('exact3900 updates,31200 exposures,300 drops and order rejection',order)
    def full_authorize():
        identity={'hostname':'ARTIFICIAL_RAM_ONLY','project':'/ARTIFICIAL','gpu_uuid':'GPU-ARTIFICIAL','gpu_name':'ARTIFICIAL','driver_version':'0'}
        q={k:{} for k in ['QC','GPU_audit','preflight_scope','resource_rebind']}
        q.update(schema='bcsp-blue-noise-training-request-v1',stage=m.STAGE,status='AWAITING_EXPLICIT_USER_AUTHORIZATION',
          run_id='ARTIFICIAL_MEMORY_NOT_EXECUTABLE',fold='C',n_input=8192,arm=m.ARMS[0],paired_initialization=None,
          static_config={'path':'CFG','sha256':m.IMMUTABLE['static_config']},order_plan={'sha256':m.IMMUTABLE['order_plan']},
          preflight_request_sha256='c'*64,identity=identity,data_root='ARTIFICIAL',model_root='ARTIFICIAL',
          implementation={'runtime':{'sha256':m.IMMUTABLE['training_runtime']}},output='ARTIFICIAL',launch_attempt='ARTIFICIAL')
        q['resource_rebind']={'path':'RESOURCE','sha256':'e'*64};q['preflight_scope']={'path':'SCOPE','sha256':'c'*64};q['GPU_audit']={'path':'GPU','sha256':'d'*64}
        resource={'schema':'bcsp-blue-noise-resource-v1','stage':m.STAGE,'historical_GPU_only':True,'old_scope_sha256':'c'*64,
          'historical_GPU_audit_sha256':'d'*64,'readonly_identity':{'path':'OBSERVED'},'readonly_assets':{'path':'ASSETS'},'new_identity':identity}
        observed={'hostname':identity['hostname'],'uid':1000,'project':identity['project'],'gpu':'GPU-ARTIFICIAL, ARTIFICIAL, 0, 1, 0'}
        grant={'schema':'bcsp-training-authorization-v1','request_sha256':'a'*64,'explicit_user_authorization':True,
          'user_authorization_text':'ARTIFICIAL RAM FIXTURE; NOT USER AUTHORIZATION'}
        rt={'schema':'bcsp-training-runtime-v1','request_sha256':'a'*64,'authorization_sha256':'b'*64}
        values={'Q':q,'A':grant,'R':rt,'CFG':cfg,'RESOURCE':resource,'OBSERVED':observed,'ASSETS':{'status':'SELECTED30_HASH_PASS','assets':[{'fixture':i} for i in range(30)]},
          'SCOPE':{},'GPU':{'status':m.GPU_STATUS}}
        oldjson=m.json_bound;oldresource=m.IMMUTABLE['resource_binding']
        try:
            m.json_bound=lambda r:values[r['path']];m.IMMUTABLE['resource_binding']='e'*64
            authorize=lambda:m.authorize({'path':'Q','sha256':'a'*64},{'path':'A','sha256':'b'*64},{'path':'R','sha256':'f'*64})
            assert authorize()[0]==q # Real authorize -> real validate_rebind; only JSON I/O is RAM mocked.
            m.validate_pair_initialization(None,q,'p','s','o')
            q['arm']=m.ARMS[1];q['paired_initialization']={'path':'ARTIFICIAL_PARENT'};assert authorize()[0]==q
            value={'schema':'bcsp-blue-noise-paired-initialization-v1','stage':m.STAGE,'verified_updates':3900,
              'baseline_run_id':'bcsp_blue_noise_foldC_Euclidean_elimination_in8192_out8192_seed0_train_v1',
              'identity':identity,'static_config_sha256':q['static_config']['sha256'],'runtime_sha256':q['implementation']['runtime']['sha256'],
              'order_plan_sha256':q['order_plan']['sha256'],'order_canonical_sha256':'o','parameter_sha256':'p','persistent_state_sha256':'s'}
            m.validate_pair_initialization(value,q,'p','s','o')
            reject(lambda:m.validate_pair_initialization(value,q,'wrong','s','o'))
            reject(lambda:m.validate_pair_initialization(None,q,'p','s','o'))
            q['paired_initialization']=None;reject(authorize);q['arm']=m.ARMS[0]
            grant['runtime_sha256']='x';reject(authorize);del grant['runtime_sha256']
            rt['request_sha256']='b'*64;reject(authorize);rt['request_sha256']='a'*64
            grant['explicit_user_authorization']=False;reject(authorize);grant['explicit_user_authorization']=True
            observed['hostname']='WRONG';reject(authorize);observed['hostname']=identity['hostname']
            q['stage']='BCSP_SAMPLING_AB_V1';reject(authorize);q['stage']=m.STAGE
            m.IMMUTABLE['resource_binding']=oldresource;reject(authorize)
        finally:m.json_bound=oldjson;m.IMMUTABLE['resource_binding']=oldresource
    test('full authorize with real rebind and matched init; stale/reverse/false/missing rejected in RAM',full_authorize)
    def pending_resource():
        assert m.IMMUTABLE['resource_binding']=='UNBOUND_PENDING_CURRENT_SERVER_READINESS'
        reject(lambda:m.validate_rebind({'sha256':'e'*64},{},{}))
    test('production unbound server resource always blocks execution',pending_resource)
    def real_binding():
        def bound(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
        v=bound(O/'paired_train_data_receipt.json');mm={a:bound(O/a/'train_manifest_8192.jsonl') for a in m.ARMS}
        f=bound(B/'consolidated_binding_v1/fold_binding.json')
        for arm in m.ARMS:
            receipt,rr,_=m.bind_metadata(v,mm,f,'C',8192,arm);assert len(rr)==315
            assert len(m.verify_qualified_receipt(receipt,v,mm,f,'C',8192,arm)[0])==315
        bad=dict(v,sha256='0'*64);reject(lambda:m.exact(bad))
    test('actual finalized metadata hash bindings and both qualified receipts',real_binding)
    def arithmetic():
        old=B/'sampling_model_AB_foldC_seed0_20261103_v1/implementation/bcsp_sampling_training_runtime_v1.py'
        expected=old.read_text(encoding='utf-8').replace('BCSP_SAMPLING_AB_V1',m.STAGE)
        assert (I/'bcsp_blue_noise_training_runtime_v1.py').read_text(encoding='utf-8')==expected
        for p in I.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
        entry=load('blue_noise_entry_bootstrap_fixture',I/'bcsp_blue_noise_training_entry_v1.py')
        assert all(callable(getattr(entry,n)) for n in ['authorize','verify_qualified_receipt','validate_pair_initialization'])
        assert 'torch' not in sys.modules and 'numpy' not in sys.modules
    test('unchanged runtime arithmetic and hash-pinned bootstrap without torch/numpy',arithmetic)
    test('relative point-path traversal rejected',lambda:reject(lambda:call(r=mutate_records('point_path','../../escape.npz'))))
    def data_boundaries():
        dev={a:[json.loads(s) for s in (O/a/'dev_manifest_8192.jsonl').read_text().splitlines()] for a in m.ARMS}
        assert all(len(v)==105 for v in dev.values());reject(lambda:call(r=dev))
        assert sha(O/'shared_order_foldC_seed0_v1.json')==sha(B/'sampling_model_AB_foldC_seed0_20261103_v1/shared_order_foldC_seed0_v1.json')
        prior=json.loads((B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_train_data_receipt.json').read_text())
        oldperm={r['case_id']:r['common_permutation_sha256'] for r in prior['pairs']}
        assert all(r['common_permutation_sha256']==oldperm[r['case_id']] for r in qc['pairs'])
        entry=load('blue_noise_entry_payload_fixture',I/'bcsp_blue_noise_training_entry_v1.py')
        for arm in m.ARMS:
            allowed=entry.payload_paths(O/arm,records[arm]);assert len(allowed)==315
            assert not set(allowed)&{(O/arm/r['point_path']).absolute() for r in dev[arm]}
    test('development denied by train binding; exact batch/point order and315 payload paths',data_boundaries)
    assert len(results)==20
    with (out/'result.json').open('x',encoding='utf-8') as f:json.dump({'status':'PASS','checks':20,'results':results,
      'test_sha256':sha(Path(__file__)),'GPU_model_calls':0,'real_authorization_files_created':0,
      'resource_fixture':'RAM-only; production resource remains unbound'},f,indent=2)
    print('CPU_CONTRACT_20_PASS')

if __name__=='__main__':
    try:main()
    except BaseException:traceback.print_exc();raise
