# 冻结特征读出对照：本机实施、验证与缺口记录 v1

日期：2026-11-07。状态：**核心CPU验证通过，完整执行接入／最终P3尚未通过，无execution request。**

## 已完成

- 新增独立提取核心：从实际coarse头捕获1024维特征和256点Q，专用退出跳过decoder；不改生产源码。
- 新增固定18维几何、4维经验矩、训练来源等权ridge与四种对照；lambda=1按平均损失定义，无调参。
- 唯一一批20项人工CPU检查通过，0失败／0错误；实际CPU Torch hook输出与同一head直接计算精确一致，异常透传、hook清理、状态／RNG保持、primal／dual系数、315／105完整读者及训练／开发隔离均验证。
- 四个本机checkpoint、420个唯一8k点集文件实际SHA256核对通过。仅字节读取，未解码真实点集或加载checkpoint。
- 新容器身份、磁盘／SMI资源及固定路径存在性只读核对完成；四个冻结旧权重路径缺失。

## 不能省略的剩余接入

必须把已验证核心接入既有加载／数值／资源／授权短入口，增加限定的实际orchestration人工检查与最终P3；绑定新容器实际provider和数据哈希，固定运行超时与显存阈值后，才能创建待授权request。本轮没有通过不完整入口虚报P3。不会为此扩展库存框架或重复GPU preflight。

## 权重上传清单

四文件均位于 `E:/ResearchBackups/AdaPoinTr/BCSP_MAMBA_P1/2026-11-06_P1_checkpoints_v1/weights`。建议手动上传至`/home/jovyan/`；上传不代表授权安装／加载。最终应恢复到新目录，不能假定旧logs路径仍在。

| 文件名 | bytes | SHA256 |
|---|---:|---|
| T0_C_epoch99_step3900.pth | 380368111 | `8671656b5a2b0843ed426868d9d06976a2ead816808f9f7c54ddadb83515ab07` |
| M0_C_epoch99_step3900.pth | 407224375 | `bc6a489bcd4df5123a3bb6616105d7ec4628fc365e71313398ee516bcf72ef9a` |
| T0_D_epoch99_step3900.pth | 380368111 | `ed901f18be2efb84f9b7b159cec2b71a3602e2e960087ac53d510881be9eba7c` |
| M0_D_epoch99_step3900.pth | 407224375 | `9e6f5c3034b051474e0ca78de725ba1579c2ddd25b2acf9848a1f8bf21c79263` |

## 科研范围仍固定

T0/M0×C/D，各315训练＋105开发，共1680次encoder/coarse前缀，0次完整dense forward、backward或optimizer step。训练标签只用于CPU读出拟合；开发只评价。无新seed、病例选择、正则扫描、模型训练或H2选择。

人工核心检查不代表真实Mamba/CUDA或新容器执行链已验证。当前未产生任何真实探针对照结果。
