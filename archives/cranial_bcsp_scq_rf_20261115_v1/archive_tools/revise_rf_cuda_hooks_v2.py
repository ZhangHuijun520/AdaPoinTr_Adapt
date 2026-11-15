"""Local-only v2 hook-contract correction; prepares sources, never executes tests."""
from pathlib import Path
import ast
import hashlib
import json

R=Path(__file__).resolve().parent.parent
OLD=R/'outputs/scq_rf_cuda_preparation_20261114_v1'
O=R/'outputs/scq_rf_cuda_preparation_20261114_v2'
O.mkdir()


def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())


audit=json.loads((OLD/'failed_freeze_hook_review_v1/formal_failure_freeze_audit_v1.json').read_bytes())
assert audit['status']=='FORMAL_RF_CUDA_FAILED_RUN_FREEZE_AUDIT_PASS_EXECUTION_REMAINS_FAILED'
entry=OLD/'bcsp_scq_rf_cuda_admission_v1.py';test=OLD/'test_rf_cuda_entry_cpu_v1.py'
assert rec(entry)['sha256']=='a46c10023766933581f7113141db4e31a5c8fb47c107ece82901cdc58cc8dc47'
src=entry.read_text(encoding='utf-8')
helper='''def check_coordinate_consumers(torch,consumers,coarse,dense,event,label):
    """Observe both PE roles, persist all decisions, then assert exact contracts."""
    required=dict(query=1,decoder=1,Memory=1,PE=2,rebuild=1,relative=1)
    calls={k:len(v) for k,v in consumers.items()}
    def snapshot(name,index=0):
        values=consumers.get(name,[])
        return values[index] if len(values)>index else None
    def compare(name,value,expected):
        present=value is not None and expected is not None
        same_shape=present and value.shape==expected.shape
        finite=present and bool(torch.isfinite(value).all()) and bool(torch.isfinite(expected).all())
        exact=bool(same_shape and finite and value.dtype==expected.dtype and value.device==expected.device and torch.equal(value,expected))
        return dict(role=name,present=present,actual_shape=None if value is None else list(value.shape),
                    expected_shape=None if expected is None else list(expected.shape),
                    dtype=None if value is None else str(value.dtype),device=None if value is None else str(value.device),
                    finite=bool(finite),exact_equal=exact,
                    max_abs=float((value-expected).abs().max()) if same_shape and finite and value.device==expected.device else None)
    rows=[compare('query_MLP',snapshot('query'),coarse),compare('decoder_query',snapshot('decoder'),coarse),
          compare('PE_query_first',snapshot('PE',0),coarse),compare('PE_Memory_second',snapshot('PE',1),snapshot('Memory')),
          compare('FC_rebuild',snapshot('rebuild'),coarse)]
    relative=snapshot('relative')
    valid_relative=relative is not None and tuple(relative.shape)==(coarse.shape[0],256,32,3)
    center=(relative+coarse.detach()[:,:,None]).reshape(coarse.shape[0],8192,3) if valid_relative else None
    rows.append(compare('dense_center',dense.detach(),center))
    record=dict(kind='COORDINATE_CONSUMERS_BEFORE_ASSERTIONS',phase=label,call_counts=calls,expected_call_counts=required,
                exact_call_contract=calls==required,relative_shape=None if relative is None else list(relative.shape),comparisons=rows)
    event(record)
    need(calls==required,'actual coordinate consumer call count/role mismatch')
    need(all(row['exact_equal'] for row in rows),'actual coordinate consumer value mismatch')
    return record


'''
assert src.count('def phase_checks(')==1
src=src.replace('def phase_checks(',helper+'def phase_checks(',1)
old="""        hooks=[b.mlp_query.register_forward_pre_hook(lambda m,a:consumers.update(query=a[0][...,-3:].detach().clone())),
               b.decoder.register_forward_pre_hook(lambda m,a,kw:consumers.update(decoder=kw['q_pos'].detach().clone()),with_kwargs=True),
               b.decoder.coordinate_pe.register_forward_pre_hook(lambda m,a:consumers.update(PE=a[0].detach().clone())),
               model.reduce_map.register_forward_pre_hook(lambda m,a:consumers.update(rebuild=a[0][...,-3:].detach().clone())),
               model.decode_head.register_forward_hook(lambda m,a,v:consumers.update(relative=v.detach().clone()))]"""
new="""        def remember(name,value):
            consumers.setdefault(name,[]).append(value.detach().clone())
        def decoder_inputs(m,args,kw):
            remember('decoder',kw['q_pos']);remember('Memory',kw['v_pos'])
        hooks=[b.mlp_query.register_forward_pre_hook(lambda m,a:remember('query',a[0][...,-3:])),
               b.decoder.register_forward_pre_hook(decoder_inputs,with_kwargs=True),
               b.decoder.coordinate_pe.register_forward_pre_hook(lambda m,a:remember('PE',a[0])),
               model.reduce_map.register_forward_pre_hook(lambda m,a:remember('rebuild',a[0][...,-3:])),
               model.decode_head.register_forward_hook(lambda m,a,v:remember('relative',v))]"""
assert src.count(old)==1;src=src.replace(old,new)
old="""            need(set(consumers)=={'query','decoder','PE','rebuild','relative'},'all actual Q2 consumers observed')
            need(all(torch.equal(consumers[k],coarse) for k in ('query','decoder','PE','rebuild')),'actual Q2 consumer mismatch')
            need(torch.equal(dense,(consumers['relative']+coarse.detach()[:,:,None]).reshape(batch,8192,3)),'actual dense Q2 centers')"""
assert src.count(old)==1
src=src.replace(old,"            consumer_record=check_coordinate_consumers(torch,consumers,coarse,dense,event,label)")
src=src.replace('actual_Q2_consumers=True,BN_changed=changes','actual_Q2_consumers=True,coordinate_consumers=consumer_record,BN_changed=changes')
new_entry=O/'bcsp_scq_rf_cuda_admission_v2.py'
compile(src,str(new_entry),'exec')
with new_entry.open('x',encoding='utf-8',newline='\n') as f:f.write(src)

ts=test.read_text(encoding='utf-8').replace("D=O/'cpu_entry_batch_v1'","D=O/'cpu_entry_batch_v2'").replace('bcsp_scq_rf_cuda_admission_v1.py','bcsp_scq_rf_cuda_admission_v2.py')
old='def forward(self,q_pos):return self.coordinate_pe(q_pos)'
new='''def forward(self,q_pos,v_pos):
                query=self.coordinate_pe(q_pos)
                memory=self.coordinate_pe(v_pos)
                return query+memory'''
assert ts.count(old)==1;ts=ts.replace(old,new)
old="b.mlp_query(torch.cat((q0,q2),-1));features=b.decoder(q_pos=q2)"
new="b.mlp_query(torch.cat((q0,q2),-1));features=b.decoder(q_pos=q2,v_pos=x[:,:256]+7.)"
assert ts.count(old)==1;ts=ts.replace(old,new)
anchor="            with torch.random.fork_rng(devices=[]):torch.manual_seed(0);broken=Fixture('RF-Requery',True)"
regressions='''            consumer_events=[v for v in events if v.get('kind')=='COORDINATE_CONSUMERS_BEFORE_ASSERTIONS']
            check('five phases record two PE calls with separate roles',len(consumer_events)==5 and all(v['call_counts']['PE']==2 and all(r['exact_equal'] for r in v['comparisons']) for v in consumer_events))
            check('fixture query Memory same shape but distinct values',all(next(r for r in v['comparisons'] if r['role']=='PE_Memory_second')['actual_shape']==next(r for r in v['comparisons'] if r['role']=='PE_query_first')['actual_shape'] for v in consumer_events))
            cq=torch.zeros(1,256,3);cm=torch.ones_like(cq)*7;rel=torch.zeros(1,256,32,3);dense=torch.zeros(1,8192,3)
            snapshots=dict(query=[cq],decoder=[cq],Memory=[cm],PE=[cq,cm],rebuild=[cq],relative=[rel])
            accepted=[];e.check_coordinate_consumers(torch,snapshots,cq,dense,accepted.append,'standalone_valid')
            check('two distinct PE roles accepted without loosening equality',accepted[0]['exact_call_contract'] and not torch.equal(cq,cm))
            for kind in ('overwritten_last_PE','missing_second_PE','extra_third_PE','swapped_PE_roles','wrong_query_value','wrong_Memory_value'):
                altered={k:list(v) for k,v in snapshots.items()}
                if kind=='overwritten_last_PE':altered['PE']=[cm]
                elif kind=='missing_second_PE':altered['PE']=[cq]
                elif kind=='extra_third_PE':altered['PE']=[cq,cm,cm]
                elif kind=='swapped_PE_roles':altered['PE']=[cm,cq]
                elif kind=='wrong_query_value':altered['query']=[cq+1]
                else:altered['Memory']=[cm+1]
                diagnostics=[]
                reject('consumer regression rejected '+kind,lambda:e.check_coordinate_consumers(torch,altered,cq,dense,diagnostics.append,kind))
                check('per-consumer evidence precedes rejection '+kind,len(diagnostics)==1 and diagnostics[0]['kind']=='COORDINATE_CONSUMERS_BEFORE_ASSERTIONS' and (not diagnostics[0]['exact_call_contract'] or any(not row['exact_equal'] for row in diagnostics[0]['comparisons'])))
                with (D/(kind+'_diagnostic.json')).open('x',encoding='utf-8') as f:json.dump(diagnostics[0],f,indent=2,allow_nan=False)
'''
assert ts.count(anchor)==1;ts=ts.replace(anchor,regressions+anchor)
new_test=O/'test_rf_cuda_entry_cpu_v2.py'
compile(ts,str(new_test),'exec')
with new_test.open('x',encoding='utf-8',newline='\n') as f:f.write(ts)
# Static delta: every existing top-level function except phase_checks is unchanged.
def funcs(raw):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}
original=funcs(entry.read_text(encoding='utf-8'));updated=funcs(src)
assert all(updated[k]==v for k,v in original.items() if k!='phase_checks')
assert set(updated)-set(original)=={'check_coordinate_consumers'}
ip3=json.loads((R/'outputs/scq_rf_implementation_20261114_v1/P3_implementation_v2.json').read_bytes())
preserved=ip3['candidate_sources']+ip3['initialization']
for row in preserved:assert rec(Path(row['path']))==row
assert rec(entry)['sha256']=='a46c10023766933581f7113141db4e31a5c8fb47c107ece82901cdc58cc8dc47'
static=dict(status='RF_CUDA_HOOK_V2_STATIC_PASS_NOT_RUNTIME',entry=rec(new_entry),test=rec(new_test),
            prior_entry=rec(entry),prior_test=rec(test),failure_audit=rec(OLD/'failed_freeze_hook_review_v1/formal_failure_freeze_audit_v1.json'),
            preserved=preserved,checks=dict(syntax=True,only_phase_hook_collection_and_checks_changed=True,
            no_other_original_top_level_function_changed=True,distinct_query_Memory_roles=True,diagnostics_before_assertions=True,
            exact_equality_and_call_counts_preserved=True,CPU_two_call_and_negative_regressions_defined=True,
            original_implementation_initialization_unchanged=True,no_server=True,no_CUDA=True),tests_run=0)
with (O/'static_review_v2.json').open('x',encoding='utf-8') as f:json.dump(static,f,indent=2,allow_nan=False)
print(json.dumps(dict(status=static['status'],entry_SHA256=rec(new_entry)['sha256'],CPU_run=False)))
