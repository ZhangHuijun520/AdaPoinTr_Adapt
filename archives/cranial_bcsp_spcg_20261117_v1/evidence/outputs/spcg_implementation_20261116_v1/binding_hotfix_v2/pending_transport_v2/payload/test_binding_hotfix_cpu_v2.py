"""One stdlib artificial regression batch; no SMI/model/server calls."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,traceback
V=Path(__file__).resolve().parent;S=V.parent;O=V/'CPU_batch_v2'
def load(p):
    sp=importlib.util.spec_from_file_location('hotfix_cpu_'+p.stem,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    O.mkdir();checks=[];scope=json.loads((V/'CPU_scope_v2.json').read_text());e=load(V/'bcsp_spcg_cuda_entry_v2.py');old=load(S/'bcsp_spcg_cuda_entry_v1.py');q=json.loads((V/'candidate_request_before_P3_v2.json').read_text(encoding='utf-8'));previous=os.environ.get('CUDA_VISIBLE_DEVICES')
    def check(n,v):assert v,scope['tests'][n-1];assert len(checks)==n-1;checks.append(scope['tests'][n-1])
    def rejected(fn):
        try:fn()
        except (ValueError,RuntimeError):return True
        return False
    try:
        check(1,e.validate_request_gpu(q)==q['identity']['gpu_uuid'])
        ab,rb=e.materialization(q,'a'*64,'ARTIFICIAL_ONLY');a=json.loads(ab);r=json.loads(rb);ah=hashlib.sha256(ab).hexdigest();bad=copy.deepcopy(q);bad['environment']['CUDA_VISIBLE_DEVICES']='GPU-stale'
        check(2,rejected(lambda:e.authorize(bad,'a'*64,a,ah,r)))
        check(3,rejected(lambda:e.render_launcher(bad,'a'*64,'b'*64,'c'*64)))
        class Helper:
            calls=0
            def smi(self,*args):self.calls+=1;raise AssertionError('unexpected query')
        h=Helper();os.environ['CUDA_VISIBLE_DEVICES']='GPU-other'
        out=O/'mismatch';out.mkdir();check(4,rejected(lambda:e.startup_query(h,q,out)) and h.calls==0 and not list(out.iterdir()))
        os.environ['CUDA_VISIBLE_DEVICES']=q['identity']['gpu_uuid']
        class QueryFailure(RuntimeError):
            def __init__(self,details):self.details=details;super().__init__('ARTIFICIAL_QUERY_FAILURE')
        class FailureHelper:
            def __init__(self,out,status):self.out=out;self.status=status;self.calls=0
            def smi(self,query):
                self.calls+=1;assert (self.out/'worker.pid').read_text()==str(os.getpid());assert (self.out/'startup_query_attempt.json').is_file()
                raise QueryFailure(dict(status=self.status,command=['nvidia-smi','--id='+q['identity']['gpu_uuid']],returncode=6,stdout=dict(text='OUT',bytes_total=3,truncated=False),stderr=dict(text='ERR',bytes_total=3,truncated=False),timeout_seconds=10,query_attempts=1))
        out=O/'nonzero';out.mkdir();h=FailureHelper(out,'NONZERO_EXIT');failed=rejected(lambda:e.startup_query(h,q,out));d=json.loads((out/'startup_failure.json').read_text())
        check(5,failed and (out/'worker.pid').read_text()==str(os.getpid()) and d['counts']['full_forward']==0)
        check(6,d['details']['returncode']==6 and d['details']['stderr']['text']=='ERR' and d['details']['stdout']['text']=='OUT' and d['phase']=='STARTUP_SMI_BEFORE_MODEL_IMPORT')
        out=O/'timeout';out.mkdir();ht=FailureHelper(out,'TIMEOUT');assert rejected(lambda:e.startup_query(ht,q,out));dt=json.loads((out/'startup_failure.json').read_text());check(7,dt['details']['status']=='TIMEOUT' and dt['details']['timeout_seconds']==10)
        check(8,h.calls==ht.calls==1)
        out=O/'success';out.mkdir()
        class Success:
            calls=0
            def smi(self,*args):self.calls+=1;return ['GPU-x, card, driver, 24564, 1']
        hs=Success();rows=e.startup_query(hs,q,out);check(9,rows==['GPU-x','card','driver','24564','1'] and hs.calls==1 and json.loads((out/'startup_query_result.json').read_text())['status']=='OK')
        check(10,e.authorize(q,'a'*64,a,ah,r) is q and 'runtime_sha256' not in a and r['authorization_sha256']==ah)
        check(11,q['science']==old.SCIENCE==e.SCIENCE and q['limits']==old.LIMITS==e.LIMITS and q['fixture']==old.FIXTURE==e.FIXTURE and all('_v2' in q['launch_contract'][k] for k in ['request_path','authorization_path','runtime_path','launcher_path','launch_attempt_path']) and q['output'].endswith('_v2'))
        def functions(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
        f0=functions(S/'bcsp_spcg_cuda_entry_v1.py');f2=functions(V/'bcsp_spcg_cuda_entry_v2.py');changed={n for n in f0 if f0[n]!=f2[n]};original=json.loads((S/'artificial_cpu_batch_v1/result.json').read_text(encoding='utf-8'))
        check(12,changed=={'authorize','render_launcher','main'} and set(f2)-set(f0)=={'validate_request_gpu','startup_query'} and all(sha(S/n)==original['source_sha256'][n] for n in ['bcsp_spcg_head_v1.py','bcsp_spcg_factory_v1.py','bcsp_spcg_runtime_v1.py']))
        (O/'result.json').write_text(json.dumps(dict(status='SPCG_BINDING_HOTFIX_CPU_PASS',count=len(checks),checks=checks,entry_sha256=sha(V/'bcsp_spcg_cuda_entry_v2.py'),test_sha256=sha(Path(__file__)),scope_sha256=sha(V/'CPU_scope_v2.json'),changed_original_functions=sorted(changed),server_calls=0,SMI_calls=0,model_calls=0,CUDA=0),indent=2),encoding='utf-8');print('PASS12_NO_SERVER_NO_GPU')
    except BaseException as ex:(O/'failure.json').write_text(json.dumps(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(ex),traceback=traceback.format_exc()),indent=2),encoding='utf-8');raise
    finally:
        if previous is None:os.environ.pop('CUDA_VISIBLE_DEVICES',None)
        else:os.environ['CUDA_VISIBLE_DEVICES']=previous
if __name__=='__main__':main()
