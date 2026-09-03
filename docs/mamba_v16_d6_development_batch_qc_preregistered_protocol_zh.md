# Mamba v1.6 D6 development100 分批提取与模型无关 QC 预注册

> 本协议在读取任何 D6 STL 几何之前冻结。D6-A artificial CUDA zero-step 已通过，但没有访问 D6 病例；因此现在仅开放 development100 的逐批 clear-STL 提取与模型无关 QC。

## 范围

- development100 固定分三批：40 / 40 / 20 个来源，对应 8 / 8 / 4 个完整官方 ZIP。
- 每次只允许处理一个冻结 batch，不合并或拆分官方 ZIP 边界。
- 只提取每个冻结来源唯一且规范命名的 `A????_clear.stl`。
- NRRD、PNG、非 clear STL、B-series 以及任何未列入该批次的来源均不得提取。

## 完整性与 QC

- ZIP 目录必须与冻结下载清单完全一致，并逐一通过官方字节数和 MD5。
- ZIP 中每个预期来源必须恰好出现一个规范 clear STL；缺失、额外、重复、加密或过小成员均 hard fail。
- STL 使用冻结的 `tools/qc_mug500plus_clear_stl.py` 执行模型无关几何门控和 batch-local surface fingerprint 重复门控。
- 跨批重复门控推迟到三个 batch 的 100 个来源全部冻结后执行。
- QC 失败来源原样冻结，不允许自动替换；任何替换必须先签发正式 amendment。

## 权限边界

- `proposal_confirmation25` 在运行前后都必须是空目录，文件数固定为 0。
- 本阶段不生成合成病例，不做 gradient calibration，不训练 R0/R1，不运行 seed-1，不访问 confirmation25，不启动 D6-B 或候选选择。
- 只有当前批次全部来源通过，才允许继续下载和 QC 下一 development batch。
