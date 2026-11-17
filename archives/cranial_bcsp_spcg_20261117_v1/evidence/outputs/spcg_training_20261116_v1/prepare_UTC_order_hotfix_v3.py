from pathlib import Path
import ast,json,hashlib
S=Path(__file__).resolve().parent;V=S/'UTC_order_hotfix_v3';assert V.is_dir()
old=(S/'startup_chain_hotfix_v2/bcsp_spcg_training_entry_v2.py').read_text(encoding='utf-8')
needle='                if isinstance(filename,int):return\n                if guard.allow(filename,write):return'
assert old.count(needle)==1
new=old.replace(needle,'                if isinstance(filename,int):return\n                if utc.allow(filename,write):return\n                if guard.allow(filename,write):return')
p=V/'bcsp_spcg_training_entry_v3.py';assert not p.exists();ast.parse(new);p.write_text(new,encoding='utf-8')
scope=dict(status='FROZEN_BEFORE_SINGLE_UTC_ORDER_CPU_BATCH',attempts=1,checks=['only UTC dispatch line inserted','science resources and other functions unchanged','UTC read handled before source clean','UTC write denied before source','UTC validation failures propagate','unrelated links still rejected','bound source read and write guard unchanged','unlisted NPZ denied','integer FD bypass retained','real inherited policy ordering consistent','exception handler and lifecycle unchanged','frozen UTC source and production parents unchanged'],entry_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),server_calls=0,GPU=0)
(V/'CPU_scope_v3.json').write_text(json.dumps(scope,indent=2),encoding='utf-8');print('UTC_ORDER_V3_STATIC_READY')
