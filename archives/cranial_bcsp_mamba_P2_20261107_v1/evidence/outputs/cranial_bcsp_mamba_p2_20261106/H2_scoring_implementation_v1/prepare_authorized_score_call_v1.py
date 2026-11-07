"""Freeze unique local invocation for the authorized H2 score hash. Never invokes scoring itself."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;H=S.parent/'H1_scoring_implementation_20261107_v1'
t=(H/'execute_H1_M0_local_score_once_v1.py').read_text(encoding='utf-8')
t=t.replace('a962c57510371c880fa3510a56c2ffe4081537201797210a5769558dd07f94ab','3531fa8ca3282a7896be7df2b501be0ec1687f0448ebe7a613d2414e32d4f2b3').replace('model_rows=420,shared_control_rows=420,case_score_rows=840,source_score_rows=168','model_rows=630,shared_control_rows=420,case_score_rows=1050,source_score_rows=210').replace('840case rows168source rows','1050case rows210source rows').replace('UNIQUE_LOCAL_H1_M0_CPU_SCORING_STARTED','UNIQUE_LOCAL_H2_M0_CPU_SCORING_STARTED').replace('LOCAL_H1_M0_TWOFOLD_CPU_SCORING_COMPLETE','LOCAL_H2_M0_THREE_ARM_TWOFOLD_CPU_SCORING_COMPLETE').replace("done['model_predictions']==420","done['model_predictions']==630").replace("done['score_rows']==840","done['score_rows']==1050").replace("done['source_rows']==168","done['source_rows']==210")
t=t.replace(" text='单独授权上述完整哈希，启动唯一一次真实CPU评分；'"," text='下一步对上述完整哈希单独授权，即可启动唯一一次本机 CPU 评分：630行模型＋420行共享控制，共1050行。' ")
anchor=" A.mkdir()"
gate=""" assert Path(q['output']).resolve()==(S/'unified_scores_v1').resolve() and S.resolve() in Path(q['output']).resolve().parents
 version_code='import sys,json,importlib.metadata as m; print(json.dumps(dict(python=sys.version,packages={n:m.version(n) for n in '+repr(list(q['environment']['packages']))+'})))'
 probe=subprocess.run([q['environment']['python']['path'],'-I','-B','-c',version_code],capture_output=True,timeout=15,env={**os.environ,**q['invocation_contract']['environment']})
 assert probe.returncode==0;versions=json.loads(probe.stdout);assert versions['packages']==q['environment']['packages'] and versions['python']==q['environment']['python_version'],'CPU environment drift'
"""
assert t.count(anchor)==1;t=t.replace(anchor,gate+anchor)
ast.parse(t)
with (S/'execute_H2_M0_local_score_once_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(t)
q=S/'local_scoring_execution_request_v1.json';assert hashlib.sha256(q.read_bytes()).hexdigest()=='3531fa8ca3282a7896be7df2b501be0ec1687f0448ebe7a613d2414e32d4f2b3'
review=dict(status='AUTHORIZED_LOCAL_H2_SCORE_INVOCATION_STATIC_PASS',request_sha256=hashlib.sha256(q.read_bytes()).hexdigest(),wrapper_sha256=hashlib.sha256(t.encode()).hexdigest(),exact1050_case210_source_scope=True,full_bound_file_rehash_before_materialization=True,CPU_environment_prechecked=True,no_retry=True,backup_writes=0,server_or_GPU_calls=0,scorer_source_unchanged=True)
with (S/'authorized_invocation_static_review_v1.json').open('x',encoding='utf-8') as f:json.dump(review,f,indent=2)
print(review['status'])
