from pathlib import Path
import json,hashlib
V=Path(__file__).resolve().parent;d=json.loads((V/'formal_freeze_result_v1.json').read_text(encoding='utf-8'));assert all(d['checks'].values())
download='\n'.join('| '+Path(x['path']).name+' | '+str(x['bytes'])+' | '+x['sha256']+' |' for x in d['download_files'])
report=f'''# SPCG六模型630次Native预测：正式只读冻结审计

2026-11-17。结论：{d['status']}，{len(d['checks'])}项检查全部通过。

## 审计范围

当前容器yxwd3w-0。绑定request SHA256 `{d['request_sha256']}`。本次逐份读取预测字节及归档，不反序列化checkpoint、不读取GT、不加载模型、不调用forward、不使用GPU、不下载或评分。服务器写入为零，证据保存到本机。

审计前后所有输出文件集合、大小及SHA256完全一致；mtime/inode稳定检查未发现读取期间替换。读取可能改变atime，未将其误认为内容变化。

## 计数、清单与权限

退出码0，worker和固定tmux已退出；有效预测630份，forward尝试630次。顺序为G0_C、G1_C、G2_C、G0_D、G1_D、G2_D，各105例，210份唯一输入。

逐条核对630行manifest、forward-attempt journal、几何摘要和冻结输入索引，病例、折、来源、点数、坐标归一化、输入哈希、checkpoint哈希及预测路径一致；预测文件实测哈希和bytes与manifest一致。没有额外RF输出、context cache、decoder trace或GT数组。

16个安装文件及其映射、真实授权回执、单向runtime绑定、固定launcher和唯一attempt claim均通过。不存在额外控制文件。完成记录中的训练更新、BNCal、loss和backward均为0。

## 数组与状态/RNG

全部630份NPZ仅包含prediction和coarse，形状分别为[8192,3]、[256,3]，dtype为little-endian FP32，无NaN或Inf。本次使用标准库读取预测数组格式及数值，不导入PyTorch或运行模型。几何摘要通过有限值及病例对应检查；本轮未重新计算模型性能或完整几何统计。

六模型完成记录均为eval/inference_mode，每模型105例；各自state_before等于state_after，RNG_before等于RNG_after，包含CPU/CUDA及Python/NumPy记录。构建身份与各模型arm一致且不是人工fixture。该核验结合冻结入口predict_once的eval断言及已执行清单，不能替代跨设备数值等价证明。

## 资源与归档

1267条资源记录按6次model_start、每例before/after以及最后all_complete逐条核对，相位及计数无遗漏。资源数值依据冻结阈值重新检查，全部通过。记录最大RSS {d['resources']['RSS_bytes']} bytes、GPU占用{d['resources']['device_MiB']} MiB、Torch allocated {d['resources']['peak_allocated']} bytes、reserved {d['resources']['peak_reserved']} bytes；all_complete记录的elapsed约{d['resources']['elapsed_seconds']:.3f}秒。该时间是既有资源记录时间，不作为标准推理速度基准。

压缩包重新实测{d['archive']['bytes']} bytes，SHA256 `{d['archive']['sha256']}`。

归档成员精确为635个普通文件：630份预测，以及manifest、尝试journal、几何摘要、inference_complete和resources。全部成员逐个重算哈希，与归档内容清单和服务器对应文件一致，无目录、符号链接或额外成员。三个校验文件内容和各自哈希均通过。

## 四文件下载清单

服务器目录：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_sixmodel_native_development_20261117_v1/`

| 文件 | bytes | 本次实测SHA256 |
| --- | ---: | --- |
{download}

建议本机保存位置：`E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SPCG/2026-11-17_native_development_eval`。这是建议目录，不代表文件已经下载或在本机核验。

## 解释与后续

本次仅确认预测执行和归档完整，不证明某个模型更优。保留seed0、开发数据已曝光、有限梯度非确定性以及G0_D跨训练设备限制；统一推理设备不消除训练设备差异。Native预测未做Oracle配准或后处理。

下一步下载上述四文件，完成本机大小/SHA256/归档成员核验，再核对既有CPU评分入口兼容性并准备统一评分。评分定义和阈值应沿用原协议，不根据本次预测调整；若需SPCG三臂两折入口适配，先完成限定CPU验证/P3和待授权request。本次未自动启动评分。

本目录保留六阶段只读脚本、原始stdout/stderr、结构化结果、正式冻结JSON和本机证据哈希。
'''
(V/'正式预测后冻结审计与下载清单_zh_v1.md').write_text(report,encoding='utf-8')
(V/'download_manifest_v1.json').write_text(json.dumps(dict(files=d['download_files'],suggested_local_directory='E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SPCG/2026-11-17_native_development_eval',local_download_verified=False),ensure_ascii=False,indent=2),encoding='utf-8')
files=[p for p in V.iterdir() if p.is_file()]
(V/'local_evidence_SHA256_v1.json').write_text(json.dumps({p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files},ensure_ascii=False,indent=2),encoding='utf-8')
print('REPORT_AND_DOWNLOAD_MANIFEST_SAVED',len(d['checks']))
