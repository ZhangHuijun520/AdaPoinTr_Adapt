from pathlib import Path
import json,hashlib
V=Path(__file__).resolve().parent;O=V/'CPU_batch_v1';d=json.loads((O/'failure.json').read_text(encoding='utf-8'))
assert len(d['checks'])==7 and 'FileNotFoundError' in d['error']
files=[p for p in O.rglob('*') if p.is_file()]
result=dict(status='CPU_BATCH_FAILED_STOP_BEFORE_CHECK8_FACTORY_G1_LOCAL_PATH',passed_checks=7,failed_check=8,cause='Artificial test supplies remote mother_source.path directly to real factory.install. Entry exact() remaps reads, but factory directly opens its source argument. Local fixture must supply the same-hash local mother-source record.',suggested_minimal_scope='Only adjust artificial build fixture q copy mother_source to exact local record; production entry/scientific sources unchanged. Perform static review and one new versioned CPU batch after separate authorization, then P3/request only if passed.',entry_sha256=hashlib.sha256((V/'bcsp_spcg_sixmodel_native_predict_v1.py').read_bytes()).hexdigest(),test_sha256=hashlib.sha256((V/'test_spcg_native_CPU_v1.py').read_bytes()).hexdigest(),artifacts={str(p.relative_to(O)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files},synthetic630_started=False,server_operations=0,GPU=0,real_checkpoint_loads=0,real_payload_reads=0,CPU_retry=False,P3_created=False,execution_request_created=False)
(V/'CPU_failure_freeze_v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
report='''# SPCG六模型预测入口实施与首批CPU验证状态

2026-11-17。已新增隔离预测入口，复用既有Native630尝试／资源／状态与RNG／归档函数，接入G0、G1、G2构建与coarse/dense-only输出，绑定六组冻结权重及210份唯一输入元数据。未部署服务器或运行真实预测。

唯一一批24项人工CPU验证在第8项实际G1 factory构建期间停止，前7项通过：六份冻结证据、630索引与来源分折、manifest／坐标绑定、异常索引拒绝、授权链和身份／预算拒绝。G0人工模型构造、人工checkpoint严格加载和一次人工forward已执行；未完成三臂构建检查，未进入630次人工循环。

限定原因：factory.replace_forward直接按source参数打开源码；测试传入的q仍含服务器mother_source.path，而其他exact读取已由本机别名映射。于是factory试图在Windows打开/home/jovyan/.../models/AdaPoinTr.py，产生FileNotFoundError。这是人工fixture路径适配遗漏，没有证据支持科研模型或CUDA失败。

最小后续范围：仅在人工build fixture的q副本中将mother_source替换为同哈希本机record，再做静态复核和一次新的版本化CPU批次。生产入口、factory、模型及冻结服务器路径保持不变。先获得该限定修订及新版CPU批次授权，不能复用失败批次。

失败产物和哈希保存在CPU_batch_v1及CPU_failure_freeze_v1.json。本次未自动修改或重跑；CPU验证未通过，未汇总通过P3，未生成最终execution request、运输包或执行内容。
'''
(V/'首批CPU失败冻结与限定后续范围_zh_v1.md').write_text(report,encoding='utf-8');print('CPU_FAILURE_FROZEN_NO_RETRY_NO_REQUEST')
