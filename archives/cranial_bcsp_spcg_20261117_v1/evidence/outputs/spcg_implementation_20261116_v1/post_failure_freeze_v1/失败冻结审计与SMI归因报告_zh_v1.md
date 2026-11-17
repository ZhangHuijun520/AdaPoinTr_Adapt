# SPCG单次CUDA启动失败：只读冻结审计与SMI归因

日期：2026-11-16。request SHA256：`00a69c5cc3d42e04f4caa3c21650dd58db5d8c1b446741a1b42caf6730213d0f`。

## 结论

失败证据已只读回收并冻结。14个安装文件的完整集合、大小和SHA256均匹配冻结映射；授权回执、runtime单向绑定、单次claim均一致；固定tmux会话不存在，当前容器未发现匹配worker。进程退出码1，失败发生于模型导入与worker.pid创建之前，forward/loss/backward/optimizer step均为0。本request已消耗，未重试。

确认请求生成存在跨字段绑定遗漏：identity.gpu_uuid已更新，environment.CUDA_VISIBLE_DEVICES却沿用旧请求。部署launcher原样导出了该旧值；helper.smi明确将环境值作为nvidia-smi的--id。该错误由本轮请求生成造成，CPU测试没有覆盖最终request两个字段的一致性。

## 精确查询命令

由已核验helper源码、request和已部署launcher还原的argv为：

```text
/usr/bin/nvidia-smi
--id=GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed
--query-gpu=uuid,name,driver_version,memory.total,memory.used
--format=csv,noheader,nounits
```

当前request身份及此前启动前资源查询确认的分配GPU：

```text
GPU-c25d6be2-173c-031a-89c6-b96e0f5f8190
```

两者不一致。以上命令是依据绑定源码和launcher重建，不是本轮重新执行或从原始argv事件文件读取。本轮没有调用nvidia-smi。

## 错误输出的证据限度

原launch.log只保存如下异常摘要及调用栈：

```text
bcsp_spcg_cuda_entry_v1.py:141 -> helper.smi(...)
bcsp_artificial_gpu_preflight_v3.py:400 -> _smi_once(...)
bcsp_artificial_gpu_preflight_v3.py:386 -> raise MonitorQueryFailure(details)
MonitorQueryFailure: monitor query NONZERO_EXIT: ChildNonzeroExit
```

helper异常对象的details原本含command、returncode、stdout和stderr，但此处_MONITOR=None，且入口的try/except尚未建立，details没有落盘。因此**无法从既有文件恢复原始SMI stdout、stderr及其数字退出码**。不能把入口退出码1冒充SMI子进程退出码，也不能编造“未找到设备”的原始stderr文本。可确认选择器绑定错误及查询非零；其他同时发生的原因无法由遗留信息排除。

## 完整产物与人工复核

输出目录实际仅三项：`launcher.pid`、`launch.log`、`exit_code.txt`。control目录四项为授权、runtime、launcher和单次claim。

本次自动审计辅助脚本错误预期输出只有log和exit，因额外的launcher.pid触发集合断言，故该脚本本身没有输出自动PASS。只读检查已经回传的完整证据，并对照冻结render_launcher，确认launcher.pid是其明确写入的合法产物，不是额外模型执行证据。此处记录人工集合核对结论；没有修改审计脚本或重跑服务器审计，不将原断言冒称通过。

server_evidence.json保留全部14项指纹、四个control原文和三个输出原文，stdout.bin/stderr.bin保留原始传输字节。当前容器procfs检查不代表宿主机全命名空间检查。

## 后续最小修订建议（未实施）

1. 新版request显式令environment.CUDA_VISIBLE_DEVICES绑定identity.gpu_uuid；在最终request审查与入口启动前检查两者一致，避免只测人工mock而漏掉最终生成物。
2. 在首次SMI查询前建立启动失败详情落盘路径，保存异常details中的真实command、returncode、stdout/stderr、阶段与时间；日志保留现有长度上限，不放宽资源或重试规则。
3. 加入“identity已换而环境仍旧”的针对性CPU拒绝回归及启动错误详情回归；完成新P3和全新版本request后再等待单独执行授权。

保持模型、U/H字节、provider、完整loss、GPU显存阈值、SMI超时预算及11forward/3loss/3backward/0step不变。不重编译、不重装、不自动重跑CPU/GPU。本轮没有修改服务器或生产代码。
