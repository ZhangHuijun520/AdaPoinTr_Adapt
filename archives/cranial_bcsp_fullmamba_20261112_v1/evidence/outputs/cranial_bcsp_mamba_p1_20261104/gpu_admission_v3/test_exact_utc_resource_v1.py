"""Artificial link metadata + real local read-only fd hashing; no native package imports."""
import ast,copy,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('exact_utc',HERE/'exact_utc_resource_v1.py');utc=importlib.util.module_from_spec(spec);spec.loader.exec_module(utc)
OUT=HERE/'CPU_timezone_contracts_v1'


def main():
    OUT.mkdir();checks=[]
    def check(n,v):assert v,n;checks.append(n)
    def reject(n,f):
        try:f()
        except (RuntimeError,OSError):checks.append(n)
        else:raise AssertionError(n)
    try:
        target=OUT/'fixture_target';data=b'TZif2'+b'\0'*113
        target.write_bytes(data);source=OUT/'fixture_UTC_link';other=OUT/'unrelated_link'
        binding=dict(link=str(source.resolve()),link_text='Etc/UTC',target=str(target.resolve()),bytes=118,sha256=hashlib.sha256(data).hexdigest())
        st=target.stat();good=dict(link_is_symlink=True,link_text='Etc/UTC',resolved_target=binding['target'],target_is_regular=True,target_has_link_ancestor=False,link_has_link_ancestor=False,bytes=118,device=st.st_dev,inode=st.st_ino)
        check('production binding equals audited exact path/hash',utc.UTC_RESOURCE==dict(link='/usr/share/zoneinfo/UTC',link_text='Etc/UTC',target='/usr/share/zoneinfo/Etc/UTC',bytes=118,sha256='ab1ddb33c7187e56408033a8165ea3b1432e024710e7ab2aafec036a8bd7f09a'))
        utc.validate_metadata(binding,good);checks.append('matching link metadata accepted')
        for key,value,name in [('link_is_symlink',False,'regular source rejected'),('link_text','other','changed link text rejected'),('resolved_target','/outside','target escape rejected'),('target_is_regular',False,'nonregular target rejected'),('target_has_link_ancestor',True,'target link chain rejected'),('link_has_link_ancestor',True,'source ancestor link rejected'),('bytes',119,'wrong size rejected')]:
            modified=dict(good,**{key:value});reject(name,lambda modified=modified:utc.validate_metadata(binding,modified))
        with patch.object(utc,'inspect_binding',return_value=good):
            reader=utc.ExactUTCReader(binding)
            check('constructor verifies real fixture bytes through fd',reader.read_checks==1)
            # Verification after hook installation must never open a pathname recursively.
            with patch.object(utc.os,'open',side_effect=AssertionError('unexpected recursive open')):
                check('exact source readonly admitted without recursive open',reader.allow(binding['link']))
                check('exact target readonly admitted without recursive open',reader.allow(binding['target']))
            check('bytes filename accepted for exact source',reader.allow(os.fsencode(binding['link'])))
            check('unknown path not handled',not reader.allow(str(other)))
            check('directory and alternate alias not handled',not reader.allow(str(target.parent)) and not reader.allow(binding['link']+'/../UTC'))
            reject('source write refused',lambda:reader.allow(binding['link'],True))
            reject('target write refused',lambda:reader.allow(binding['target'],True))
            check('fd metadata event not generalized into exception',reader.allow(reader.fd) is False)
            for kind,changed in [('retarget',dict(good,resolved_target='/outside')),('inode',dict(good,inode=st.st_ino+1))]:
                with patch.object(utc,'inspect_binding',return_value=changed):reject(kind+' drift after initialization rejected',lambda:reader.allow(binding['link']))
            target.write_bytes(b'X'+data[1:])
            reject('same-size content hash drift rejected',lambda:reader.allow(binding['target']))
            target.write_bytes(data)
            check('fixture hash intact after restoration',hashlib.sha256(target.read_bytes()).hexdigest()==binding['sha256'])
            # Exercise the actual nested Policy.check from the candidate entry.
            candidate=ast.parse((HERE/'bcsp_p1_gpu_admission_v3.py').read_text(encoding='utf-8'))
            policy=next(n for n in ast.walk(candidate) if isinstance(n,ast.ClassDef) and n.name=='Policy')
            calls=[]
            class DenyBase:
                def check(self,filename,write=False):calls.append((filename,write));raise RuntimeError('unchanged general policy rejects')
            def clean(p):return Path(p).absolute()
            namespace=dict(helper=types.SimpleNamespace(FilePolicy=DenyBase,PAYLOAD={'.npz','.pth'}),timezone_guard=reader,allowed=set(),clean=clean,os=os,require=utc.require)
            exec(compile(ast.Module(body=[policy],type_ignores=[]),'<actual_candidate_Policy>','exec'),namespace)
            obj=namespace['Policy']()
            check('actual Policy admits only bound source/target before generic guard',obj.check(binding['link']) is None and obj.check(binding['target']) is None and not calls)
            reject('actual Policy refuses exact resource writes',lambda:obj.check(binding['link'],True))
            reject('actual Policy preserves other-path rejection',lambda:obj.check(str(other)))
            reject('actual Policy preserves unknown NPZ guard',lambda:obj.check(str(OUT/'forbidden.npz')))
            reject('actual Policy preserves checkpoint-write guard',lambda:obj.check(str(OUT/'forbidden.pth'),True))
            reader.close();reject('closed fd exception cannot be reused',lambda:reader.allow(binding['link']))
        # Production inspect does not pretend a regular local file is a symlink.
        regular_binding=dict(binding,link=str(target.resolve()))
        reject('real local non-symlink source fails production inspect',lambda:utc.ExactUTCReader(regular_binding))
        old=HERE.parents[0]/'gpu_admission_v2/transport_payload/bcsp_p1_gpu_admission_v1.py'
        parent=ast.parse(old.read_text(encoding='utf-8'))
        for name in ('clean','admit_model','outputs','gradient_summary','authorize','counters'):
            a=next(n for n in parent.body if isinstance(n,ast.FunctionDef) and n.name==name)
            b=next(n for n in candidate.body if isinstance(n,ast.FunctionDef) and n.name==name)
            check('unchanged execution/general guard AST: '+name,ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False))
        result=dict(status='EXACT_UTC_READONLY_CPU_CONTRACTS_PASS',count=len(checks),checks=checks,artificial_symlink_metadata=True,actual_fixture_fd_hashing=True,real_system_timezone_reads=0,WSL_calls=0,server_calls=0,GPU_calls=0,forward_calls=0,backward_calls=0,limitations='Windows test uses artificial link metadata; actual UTC provenance inherited from formal server audit. No production import/CUDA execution.')
        with (OUT/'result_v1.json').open('x') as f:json.dump(result,f,indent=2)
        print(json.dumps(result))
    except BaseException as exc:
        with (OUT/'failure_v1.json').open('x') as f:json.dump(dict(status='FAILED_STOP',checks=checks,error=repr(exc)),f,indent=2)
        raise


if __name__=='__main__':main()
