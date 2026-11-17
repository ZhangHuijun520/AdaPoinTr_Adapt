from pathlib import Path
import ast,json,hashlib
V=Path(__file__).resolve().parent
old=(V/'test_output_policy_cpu_v4.py').read_text(encoding='utf-8')
text=old.replace("O=V/'CPU_batch_v4'","O=V/'CPU_batch_v5'")
needle="g=e.traceback_source_guard(p,q)\nout=Path"
replacement="""g=e.traceback_source_guard(p,q)
# Test-only exact self-source record, frozen by parent after writing child bytes.
self_record=c['self_source'];self_path=p.exact(self_record)
assert self_path==Path(__file__).absolute()
self_fd=p.os.open(self_path,p.os.O_RDONLY|getattr(p.os,'O_NOFOLLOW',0))
g.records[self_path]=self_record;g.fds[self_path]=self_fd;g.verify(self_path)
out=Path"""
assert text.count(needle)==1;text=text.replace(needle,replacement)
text=text.replace("assert reject(lambda:Path(c['neighbor']).read_bytes())","assert reject(lambda:Path(c['neighbor']).read_bytes())\nassert reject(lambda:Path(__file__).open('wb'))\nassert Path(__file__).read_bytes()")
text=text.replace("negative_hash_binding_rejected=True)))","negative_hash_binding_rejected=True,self_source_readonly_verified=True)))")
needle="ch=O/'policy_child.py';ch.write_text(child,encoding='utf-8');r=subprocess.run"
replacement="ch=O/'policy_child.py';ch.write_text(child,encoding='utf-8');config['self_source']=rec(ch);cp.write_text(json.dumps(config),encoding='utf-8');r=subprocess.run"
assert text.count(needle)==1;text=text.replace(needle,replacement)
text=text.replace("result['traceback_sources']==4 and result['compatibility']","result['self_source_readonly_verified'] and result['traceback_sources']==4 and result['compatibility']")
text=text.replace('SPCG_OUTPUT_POLICY_WINDOWS_BINARY_CPU_PASS','SPCG_OUTPUT_POLICY_SELF_BOUND_CPU_PASS')
p=V/'test_output_policy_cpu_v5.py';assert not p.exists();ast.parse(text);p.write_text(text,encoding='utf-8')
scope=json.loads((V/'Windows_CPU_scope_v4.json').read_text());scope.update(output='CPU_batch_v5',test_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),changes='Test fixture only: freeze child source bytes in parent config, extend existing exact-source FD guard with that one read-only record; child-source write rejected; Windows binary compatibility unchanged')
(V/'Windows_CPU_scope_v5.json').write_text(json.dumps(scope,indent=2),encoding='utf-8');print('SELF_BINDING_V5_STATIC_READY')
