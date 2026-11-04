import ast,hashlib,io,json,os,shlex,sys,tarfile,unittest
from pathlib import Path
from unittest.mock import patch
N=Path(__file__).resolve().parent;sys.path.insert(0,str(N))
import development_controller_template_v1 as c
F=N/'ctrlcpu2';F.mkdir(exist_ok=False)
class Controller(unittest.TestCase):
 def test_01_materials_acyclic(self):
  q=dict(control='/p/control',output='/p/output',limits=dict(wall_seconds=7200),identity=dict(python_realpath='/env/python'),entry=dict(path='/p/entry.py'),environment=dict(CUDA_VISIBLE_DEVICES='GPU-test',TMPDIR='<owned_output>/tmp'))
  raw=c.raw_json(q);m=c.materials(q,raw,'artificial grant only');a=json.loads(m['authorization']);r=json.loads(m['runtime'])
  self.assertNotIn('runtime_sha256',a);self.assertEqual(r['authorization_sha256'],c.h(m['authorization']))
  self.assertEqual(a['request_sha256'],c.h(raw))
 def test_02_launcher_exact_arguments(self):
  q=dict(control='/p/control',output='/p/output',limits=dict(wall_seconds=7200),identity=dict(python_realpath='/env/python'),entry=dict(path='/p/entry.py'),environment={})
  text=c.materials(q,c.raw_json(q),'fixture')['launcher'].decode();line=next(x for x in text.splitlines() if x.startswith('/usr/bin/timeout '));parts=shlex.split(line)
  self.assertEqual(parts[:8],['/usr/bin/timeout','--signal=TERM','--kill-after=5s','7200s','/env/python','-I','-S','-B'])
  self.assertIn('--authorization-sha256',parts);self.assertIn('exit "$eval_rc"',text)
 def test_03_exclusive_create_no_overwrite(self):
  p=F/'one.txt'
  # Windows lacks O_NOFOLLOW: emulate only the flag constant for this fixture.
  # Production retains O_NOFOLLOW and Linux path checks; this is not a Linux symlink proof.
  with patch.object(c.os,'O_NOFOLLOW',getattr(c.os,'O_NOFOLLOW',0),create=True):
   c.create(p,b'original')
   with self.assertRaises(FileExistsError):c.create(p,b'changed')
  self.assertEqual(p.read_bytes(),b'original')
 def test_04_transport_exact_members(self):
  b=io.BytesIO()
  with tarfile.open(fileobj=b,mode='w:gz') as t:
   for name,data in [('entry.py',b'code'),('index.json',b'{}')]:
    m=tarfile.TarInfo(name);m.size=len(data);t.addfile(m,io.BytesIO(data))
  mapping=[dict(member=n,target='/p/'+n,bytes=len(d),sha256=c.h(d)) for n,d in [('entry.py',b'code'),('index.json',b'{}')]]
  self.assertEqual(c.archive_members(b.getvalue(),mapping)['/p/entry.py'],b'code')
  mapping[0]['sha256']='bad'
  with self.assertRaises(RuntimeError):c.archive_members(b.getvalue(),mapping)
 def test_05_extra_transport_member_denied(self):
  b=io.BytesIO()
  with tarfile.open(fileobj=b,mode='w:gz') as t:
   for n in ['one','two','extra']:
    x=tarfile.TarInfo(n);x.size=1;t.addfile(x,io.BytesIO(b'x'))
  with self.assertRaises(RuntimeError):c.archive_members(b.getvalue(),[dict(member='one'),dict(member='two')])
 def test_06_no_implicit_main(self):
  tree=ast.parse(Path(c.__file__).read_text())
  self.assertFalse(any(isinstance(n,ast.If) and '__main__' in ast.dump(n) for n in tree.body))
 def test_07_missing_full_SHA_denied_before_mutation(self):
  with self.assertRaises(RuntimeError):c.run(b'{}','bad',b'{}','fixture')
 def test_08_empty_grant_denied_before_mutation(self):
  raw=c.raw_json(dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False))
  with self.assertRaises(RuntimeError):c.run(raw,c.h(raw),b'{}','')
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controller))
 with (N/'controller_CPU_result_v2.json').open('x') as f:json.dump(dict(status='PASS' if result.wasSuccessful() else 'FAILED_STOP',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),server_calls=0,production_authorization_materialized=False,source_sha256=hashlib.sha256(Path(c.__file__).read_bytes()).hexdigest()),f,indent=2)
 raise SystemExit(0 if result.wasSuccessful() else 1)
