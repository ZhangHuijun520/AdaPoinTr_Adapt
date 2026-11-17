from pathlib import Path
import ast,json,hashlib
V=Path(__file__).resolve().parent
source=(V/'test_startup_chain_CPU_v2.py').read_text(encoding='utf-8')
new=source.replace("O=V/'CPU_batch_v2'","O=V/'CPU_batch_v3'")
needle="policy=parent.make_policy(helper,[],out,[],[],[],UTC(),g)";assert new.count(needle)==1
new=new.replace(needle,"policy=parent.make_policy(helper,[Path(sys.prefix).resolve()],out,[],[],[],UTC(),g)")
# These are rejection probes under the same inherited policy, not permissions added.
needle="assert reject(lambda:Path(c['neighbor']).read_bytes())";assert new.count(needle)==1
new=new.replace(needle,needle+"\n assert reject(lambda:Path(R['entry']['path']).open('wb'))\n assert reject(lambda:Path(torch.__file__).open('wb'))\n assert reject(lambda:(out/'unlisted.npz').open('wb'))")
new=new.replace('SPCG_G0C_STARTUP_CHAIN_CPU_PASS','SPCG_G0C_STARTUP_CHAIN_ENV_CPU_PASS')
p=V/'test_startup_chain_CPU_v3.py';assert not p.exists();ast.parse(new);p.write_text(new,encoding='utf-8')
scope=json.loads((V/'CPU_scope_v2.json').read_text());scope.update(status='FROZEN_BEFORE_SINGLE_CPU_ENV_ROOT_BATCH',output='CPU_batch_v3',attempts=1,change='Artificial child read roots=[current CPU sys.prefix]; no individual dependency exemptions; source/env writes and unlisted NPZ remain denied',test_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),production_entry_sha256=hashlib.sha256((V/'bcsp_spcg_training_entry_v2.py').read_bytes()).hexdigest())
(V/'CPU_environment_scope_v3.json').write_text(json.dumps(scope,indent=2),encoding='utf-8');print('CPU_ENV_FIXTURE_V3_STATIC_READY')
