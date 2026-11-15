# SCQ-RF S-ref Fold C：CPU通过、P3与待授权训练说明

2026-11-14。本轮仅补齐测试子进程的`utc`绑定，使用新版本测试及新输出目录执行一次人工CPU批次；入口、bridge、模型、初始化、原训练runtime与metadata contract均未修改。未连接服务器、重复GPU准入或启动训练。

## 1. 本轮完成结果

新版CPU **36项全部通过**，本机P3通过，最终训练request实际`authorize()`元数据路径核验通过。

新增测试仅在人工exec环境中加入已存在的`utc`对象，恢复嵌套Policy类需要的上下文。原v1的35项通过记录、最终NameError及子进程stdout／stderr均保留，没有将旧失败改写为成功。

本次通过的检查包括真实冻结准入／QC／顺序的授权合同、S-ref先行且不依赖旧B、错误设备／fold／variant／seed／哈希等拒绝、315训练路径与越界／重复拒绝、POSIX启动渲染、原no-decay标记、小模型loss／几何分派及3900日志最终化守卫、bridge委托与拒绝，以及实际嵌套文件策略下的源码／初始化读取、训练专属NPZ、最终checkpoint、源文件写入拒绝和整数fd兼容性。

这是人工CPU接入验证：只做一次小模型forward／backward，没有optimizer step或3900步训练；没有访问真实点数组或checkpoint。它不证明完整训练资源／科研效果通过。CUDA原生路径已由独立v3正式冻结审计覆盖，本次不重复GPU。

关键源码哈希保持不变：

| 文件 | SHA256 |
|---|---|
| S-ref_C入口 | `c6e29be6ac73cd0bb191c35115a00874635d0122d22aee334bd7b083324d11a7` |
| bridge | `9f282d1ce07e9c89ba7cac246d99c2c9f0ac2086f1f5de80151ae2a73723c6dd` |
| 原训练runtime | `939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee` |

证据：[CPU结果](cpu_entry_batch_v2/result_v1.json)、[实际文件策略子进程输出](cpu_entry_batch_v2/policy_stdout.bin)、[新P3](training_entry_P3_v1.json)、[最终request授权合同校核](final_authorize_contract_review_v1.json)。最后一项仅使用内存中的人工授权对象作元数据校核，没有落盘真实授权回执／runtime／launcher。

## 2. 首个训练合同

| 项目 | 固定范围 |
|---|---|
| 阶段／模型 | SCQ_RF阶段S-ref_C，原SCQ S结构，40,596,676参数，不安装RF第二头 |
| 数据 | Fold C训练63来源、315病例，每来源五类缺损，原BCSP V1 |
| 点数 | 8192输入→8192完整骨块表面输出，256 coarse |
| 初始化 | 从头seed0，原冻结SCQ初始化；不加载历史checkpoint |
| 计数 | 100遍历×39 full batch×batch8＝3900更新；31,200曝光、300丢弃 |
| 顺序 | 原冻结实际批次计划，canonical SHA256 `349189dcada4c41b9e6b0152fa24695b2c71ce5fce4144865247d03c445f795f` |
| 目标／优化 | 原coarse＋dense loss、AdamW、LR／BN调度、clip10及SSM no-decay例外不变 |
| 数值 | FP32、TF32关闭；保留已披露的有限梯度非位级确定性 |
| 资源 | 24小时、RSS8GiB、torch峰值20GiB、SMI22,528MiB、输出2GiB、空闲磁盘≥4GiB |
| 终点 | 仅固定epoch99／step3900最终checkpoint |
| 禁止 | resume、自动重试、训练内开发选择、BNCal、评价、其他run或重复GPU准入 |

共有完整初态含原SCQ，应匹配已准入S-ref：`b7e5b640c1f0e709ab6697139db1267584266a51b4e0e29f2d5217bfd1236cc5`。

本轮只执行S-ref_C的准备。Static_C／Requery_C及D折后续阶段仍按既定顺序分别授权；不能将本request扩展为六run批量启动。

## 3. 最终待授权request

[SCQ_RF_Sref_C_training_execution_request_v1.json](pending_transport_v1/payload/SCQ_RF_Sref_C_training_execution_request_v1.json)

完整SHA256：

```text
6d63c000de45f02cee7e7318abedaef0bb96b39e32a5e0ae6f40bdfbf2c67b21
```

状态为`AWAITING_EXPLICIT_USER_AUTHORIZATION`，执行尚未授权。新安装根为`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1`，15个新文件不覆盖安装；原模型／runtime／数据及metadata目录精确复用。

固定tmux：`bcsp_scq_rf_Sref_C_train_20261114_v1`。

固定输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v1`。

身份绑定最近审计的`shu-common-25721452-notebook-zbpgzu-0`及GPU `GPU-dabcc897-ac69-efac-4438-a6186dea9aaa`。执行前需新鲜核验当前身份、依赖与复用文件哈希、315个训练payload哈希、资源及目标不存在。任何漂移立即停止，不自动重绑定。Windows路径仅作本机来源记录，服务器命令不使用这些路径。

## 4. 上传四文件

本机目录：`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\scq_rf_Sref_C_training_implementation_20261114_v1\pending_transport_v1`。

将以下四个文件上传至`/home/jovyan/`：

1. `bcsp_scq_rf_Sref_foldC_training_pending_20261114_v1.tar.gz`
2. `bcsp_scq_rf_Sref_foldC_training_pending_20261114_v1.tar.gz.sha256`
3. `bcsp_scq_rf_Sref_foldC_training_pending_20261114_v1.tar.gz.bytes`
4. `bcsp_scq_rf_Sref_foldC_training_pending_20261114_v1.tar.gz.contents.sha256`

压缩包106,555字节，SHA256为`eb68d200627443e924ff6e14840fa340c5d1a576e9bb89f599d42f4456a3cc5c`；共16成员，含15个payload和1个安装映射，不含真实点数组或checkpoint。

上传后，仍需单独授权request完整哈希，才能核验、不覆盖安装并启动唯一一次3900步训练。本轮没有材料化真实授权回执、runtime配置或launcher，也没有启动训练。
