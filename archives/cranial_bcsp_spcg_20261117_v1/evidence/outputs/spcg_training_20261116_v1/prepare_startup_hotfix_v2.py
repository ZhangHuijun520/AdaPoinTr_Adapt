from pathlib import Path
import ast,json,hashlib
S=Path(__file__).resolve().parent;V=S/'startup_chain_hotfix_v2';V.mkdir()
old=(S/'bcsp_spcg_training_entry_v1.py').read_text(encoding='utf-8')
new=old.replace('import argparse,hashlib,','import traceback\nimport argparse,hashlib,',1)
helpers='''
def load_training_chain(q):
    bridge=source('spcg_training_bridge',q['implementation']['bridge'])
    source('bcsp_spcg_head_v1',q['implementation']['head'])
    observe=source('bcsp_spcg_runtime_v1',q['implementation']['observe'])
    runtime=source('spcg_frozen_training_runtime',q['implementation']['training_runtime'])
    return bridge,observe,runtime

def fail_with_traceback(out,exc):
    # Called before finally closes the exact-source FDs; SystemExit suppresses late excepthook.
    formatted=''.join(traceback.format_exception(type(exc),exc,exc.__traceback__))
    emit(out/'training_error_traceback.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),traceback=formatted,phase='GUARD_ACTIVE_BEFORE_CLEANUP'))
    if not (out/'failure.json').exists() and not (out/'startup_failure.json').exists():
        emit(out/'startup_failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc)))
    raise SystemExit(1) from None

'''
new=new.replace('\ndef main():',helpers+'\ndef main():',1)
needle="bridge=source('spcg_training_bridge',q['implementation']['bridge']);observe=source('bcsp_spcg_runtime_v1',q['implementation']['observe']);runtime=source('spcg_frozen_training_runtime',q['implementation']['training_runtime'])"
assert new.count(needle)==1;new=new.replace(needle,'bridge,observe,runtime=load_training_chain(q)')
needle="        if not (out/'failure.json').exists():emit(out/'startup_failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(ex)))\n        raise"
assert new.count(needle)==1;new=new.replace(needle,'        fail_with_traceback(out,ex)')
p=V/'bcsp_spcg_training_entry_v2.py';ast.parse(new);p.write_text(new,encoding='utf-8')
scope=dict(status='FROZEN_BEFORE_SINGLE_CPU_CHILD_BATCH',checks=['entry limited AST change','unchanged scientific constants and bridge','real bridge head observe runtime import order under audit','real observation function tensor paths','bound source writes denied','neighbor source reads denied','head hash drift denied','failure trace persisted while guard open','failure child exits1 with no late KeyError','guard closed after formatted failure','G0_C fixed authorization still rejects scope drift','entry plus full dependency source identities frozen'],attempts=1,server_calls=0,CUDA=0,training=0)
(V/'CPU_scope_v2.json').write_text(json.dumps(scope,indent=2),encoding='utf-8');print('V2_STATIC_READY')
