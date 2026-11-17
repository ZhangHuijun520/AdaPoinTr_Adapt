from pathlib import Path
import json,hashlib
V=Path(__file__).resolve().parent
index=json.loads((V/'SPCG_sixmodel_input_index_draft_v1.json').read_text(encoding='utf-8'))
table='\n'.join('| '+r['label']+' | '+str(len(r['dev_case_ids']))+' | '+r['checkpoint']['sha256']+' |' for r in index['runs'])
s='''# SPCG六模型Native预测入口复核与待授权范围

2026-11-17。本轮只读本机冻结元数据及现有源码，未连接服务器、加载checkpoint、读取真实NPZ或运行forward，未修改预测实现。

## 六运行证据

分别核验六组正式训练后冻结结果的通过状态、完整checks、request哈希和3900步／100轮／31200曝光／300drop计数。各自最终checkpoint绑定如下；这些哈希来自正式审计，本轮未再次读取服务器权重。

| 模型 | 预定Native病例数 | 最终checkpoint SHA256 |
| --- | ---: | --- |
'''+table+'''

逐模型及病例精确记录见SPCG_sixmodel_input_index_draft_v1.json。共630条预测索引、210份唯一输入，每折21开发来源／105病例，每模型只预测其对应折。病例未依照训练loss筛选或改动。

本轮继承已核验历史索引的精确输入路径、bytes及SHA256，并与冻结8192 manifest逐行核对病例、来源、SHA256、归一化和点数。原manifest没有文件bytes字段，bytes来自所绑定历史索引，不能表述为本轮重新实测。

**路径特别说明：C折开发点集在foldd训练点集目录中，D折开发点集在foldc目录中。** 两折互补时这是预期的数据存储方式。执行前应按逐病例精确路径核验，不能用待评价fold名称拼接训练根目录。此时只复用元数据，未重新认证服务器当前路径／大小／哈希。

## Native范围草案

- 顺序：G0_C、G1_C、G2_C、G0_D、G1_D、G2_D，串行模型、batch1。
- 630次完整forward上限，每模型105例；零loss、backward、optimizer、BNCal、warmup、TTA、retry。
- 正式执行授权后才可按精确哈希读取最终checkpoint；weights_only=True、epoch99／update3900及严格state_dict检查，不允许部分加载或fallback。
- eval＋inference_mode，FP32及既有确定性／TF32合同，逐模型记录参数／BN状态和RNG前后指纹并要求一致。
- 保存630份预测，每份prediction[8192,3]和coarse[256,3]；保留D-only center/scale供后续统一CPU评分，不在推理中使用GT、Oracle配准或后处理。
- 不保存context cache、完整decoder trace或RF专用Qraw／delta／stage数组。记录manifest、尝试journal、几何摘要、资源、完成状态及归档四文件。
- 拟限7200秒、8GiB RSS、20GiB Torch、22528MiB SMI、1GiB输出；启动6GiB、运行期间4GiB。此为本次范围草案，执行前仍需实测可用空间，不自动放宽限制。
- 拟统一在yxwd3w-0及G1_D/G2_D当前GPU上评价；身份有变化时先核验，不推断旧身份仍有效。

## 兼容性结论与最小实施缺口

现有RF六模型入口可作为630次计数、资源、状态/RNG、失败即停及归档机制的参考，但模型常量、SCQ/RF builder、校验和RF专用数组读取均不兼容SPCG。

需要新增专用SPCG预测入口，G0保留原coarse_pred，G1/G2经冻结SPCG factory替换为spcg_head；严格加载checkpoint前必须构造对应结构。精确绑定head、factory、U/H、母版及真实加载链源码，继承UTC-first和异常收尾，不扩展通用框架。

下一步限定implementation-only：专用六模型入口＋一批人工CPU验证＋P3，覆盖六个模型身份、严格权重加载、G0/G1/G2构建、630次计数、输入路径、状态/RNG和失败归档。CPU通过后才能创建绑定最终实现哈希的待授权execution request；无需重复GPU准入。

## 解释与权限边界

统一推理设备不能消除历史训练设备差异。C折三臂同原GPU，D折G1/G2同新GPU，G0_D仍为跨设备参照。保留有限梯度非确定性、seed0和开发数据已曝光限制，不按结果重新选病例或模型。

当前状态为DRAFT_NOT_EXECUTABLE_PENDING_IMPLEMENTATION_CPU_P3。没有最终execution request、运输包或真实授权回执/runtime/launcher。不得把范围草案当作预测执行授权，也未计算比较结果。
'''
(V/'六模型Native预测入口复核与待授权范围_zh_v1.md').write_text(s,encoding='utf-8')
files=[p for p in V.iterdir() if p.is_file()]
(V/'local_evidence_SHA256_v1.json').write_text(json.dumps({p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files},ensure_ascii=False,indent=2),encoding='utf-8')
print('LOCAL_PREPARATION_REPORT_SAVED_NO_EXECUTION')
