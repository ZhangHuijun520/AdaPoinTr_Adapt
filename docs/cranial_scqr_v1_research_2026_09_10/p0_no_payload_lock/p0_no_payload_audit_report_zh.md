# Cranial-SCQR v1.1：P0 无数据载荷锁定审计

生成时间：2026-09-10T11:39:45Z  
协议 ID：`cranial-scqr-v1.1-p0-no-payload-lock-v1`

## 结论

P0 的“无 payload 锁定”已经完成并通过。病例 ID 划分、模型输入输出契约、主指标既有实现、epoch/step 语义、环境身份和内容哈希均已记录。

这不等于完整 P0 已通过。数据 manifest 内容、来源 lineage、development84 的点云表示与接触标签可行性仍未审计，因为它们需要单独、精确的数据读取授权。因此当前状态是：

- `NO_PAYLOAD_LOCK_COMPLETE`
- `DATA_METADATA_AUDIT_PENDING_EXPLICIT_AUTHORIZATION`
- `DEVELOPMENT84_REPRESENTATION_AUDIT_PENDING_EXPLICIT_AUTHORIZATION`
- `L1/L2/L3/L4_NOT_AUTHORIZED`

本次没有打开 `manifest.jsonl` 或任何 `.npz`，没有读取点云/GT/影像 payload，没有执行模型 forward、preflight、计时或训练，没有 optimizer step/BNCal，没有覆盖旧结果或删除归档，也没有访问排除目录。

## 1. 环境与版本身份

服务器项目根为 `/home/jovyan/adapointr_work/PoinTr`；主机为 `shu-common-25721452-notebook-w5fqxk-0`，用户为 `jovyan`。当前目录不是 Git worktree，因此本阶段以及后续服务器实验以文件 SHA256 标识代码和配置，不伪造 Git commit 身份。

运行环境为 Python 3.10.20、NumPy 2.2.6、PyTorch 2.4.1+cu118、PyTorch CUDA 11.8、SciPy 1.15.3。GPU 是 NVIDIA GeForce RTX 4090 D，显存 24564 MiB，驱动 570.190；审计开始时 GPU 空闲（利用率 0%，显存约 1 MiB）。这些只表示环境检查，不是性能凭据。

配置的数据入口是 `data/SkullBreakPC_out8192`，其链接元数据指向 `/home/jovyan/datasets/SkullBreakPC_out8192`；预期 manifest 为该目录下的 `manifest.jsonl`。这里只检查了链接自身，未遍历目标目录、未打开 manifest 或数据文件。

## 2. 病例划分审计

development84 包含 84 个 skull、420 个 case；confirmation20 包含 20 个 skull、100 个 case。两者 case 交集为 0，合并后为 520 个唯一 case。每个 skull 恰有五种缺损：`bilateral`、`frontoorbital`、`parietotemporal`、`random_1`、`random_2`。

每个 A–D fold 均满足：

- train：63 skull / 315 case；
- dev：21 skull / 105 case；
- train 与 dev 零交集；
- train ∪ dev 恰好等于 development84；
- A–D 的 dev 集两两互斥，四者并集恰好等于 development84；
- 所有 ID 文件内部无重复。

这证明现有 allowlist 在字符串身份层面自洽，但不证明跨来源 skull lineage 独立，也不证明 manifest 指向的 payload 与 ID 一致。后两项仍需下一阶段授权。

## 3. 模型与数据契约

冻结的共同基础为 `partial -> implant`，8192 点输入、8192 点输出；`center_num=[512,256]`，最终 encoder proxies 为 256，queries 为 256，embedding 维度 384，dense head 为 256×32，`query_selection=learned_only`，`denoise_weight=0`。

核心最小对照保持为 B0/A1/Q0/QC：B0 是同期从头训练的匹配 AdaPoinTr；A1 加入 raw-local 几何残差与共同 SCF 辅助监督；Q0 在 A1 上增加普通 query attention 且 β=0；QC 与 Q0 唯一设计差异为接触 log-bias β=1。这里仅锁定设计，没有创建或修改模型实现。

现有历史 C0 配置含 Mamba adapter，不能直接充当新 B0；它只用于确认现有输入、骨干尺度、loader 和 epoch 语义。新 B0 必须在 L1 中显式关闭新增模块并从头训练。

## 4. 指标与汇总契约

主指标 `RimCover-P95` 复用 `utils/skullfix_metrics.py::point_rim_metrics` 的既有字段 `rim_gt_rim_to_pred_p95_mm`，定义为每个病例的 GT rim 点到预测 implant 点集的单向最近邻距离的第 95 百分位数（mm）。当前实现调用 `numpy.percentile(..., 95)`；锁定 NumPy 2.2.6。L1/L2 仍须加入与历史字段逐病例一致的回归测试。

正式汇总顺序固定为：先计算 case 指标，再对同一 skull 的五种缺损等权平均，最后对 skull 等权平均。效应记为 candidate − control，负值更好。首版资源决策目标为 QC 相对 B0 改善至少 0.10 mm；这不是临床容差。

## 5. epoch、step 与总预算

`tools/runner.py` 使用 `range(start_epoch, max_epoch + 1)`，因此 `max_epoch=100` 在无 resume 情况下执行 epoch 0–100，共 101 次数据遍历。`tools/builder.py` 对 train loader 使用 `drop_last=True`，总 batch size 为 8、`step_per_update=1`：

- fold train：`floor(315/8)=39` step/轮，`39×101=3939` optimizer steps/run；
- full84：`floor(420/8)=52` step/轮，`52×101=5252` optimizer steps/run。

按门控逐段执行时，核心路线最多 33 个 run、141804 optimizer steps。这只是条件预算上限，不构成任何训练许可；每一阶段需重新授权，失败后不得自动重跑或进入下一阶段。

## 6. 未决风险与下一门

下一步不是直接写模型或启动 GPU，而是完成 P0 的数据元数据与 development84 表示审计。需要核对：

1. manifest 的 source/alias/lineage、split、monitor 与 normalization 字段；
2. development84 allowlist 与 manifest 的精确覆盖关系；
3. 只在 development84 上验证 `partial`/`implant` 形状、有限性和归一化；
4. 冻结 rim 构造后，统计每病例 raw positive、positive proxy、正负 proxy 共存、union coverage 与 KNN 半径；
5. 用 GT implant 自身作为预测参考，记录 RimCover 非零采样基准；
6. 建立正式 `source_use_ledger.csv` 和数据审计 receipt。

若任何病例无 GT rim、无正 proxy、不能同时产生正/负 proxy，或标签/覆盖明显饱和，立即停止并分类为 raw sampling、proxy coverage 或 label saturation；不自动扩大 K、修改半径或重试。任何修改都进入 v1.2 并重新授权。

建议的下一次授权只允许读取 `/home/jovyan/datasets/SkullBreakPC_out8192/manifest.jsonl`、development84 allowlist 选中的点云文件，以及其中审计所需的 `partial`、`implant` 和必要 normalization/rim 元数据；明确排除 confirmation20、official test、old monitor 与 MUG payload，不写数据、不训练、不做 optimizer step/BNCal/正式计时。

## 7. 当前门状态

| 门 | 状态 | 说明 |
|---|---|---|
| P0-A 环境/代码/配置哈希 | PASS | 以 SHA256 标识，服务器目录非 Git worktree |
| P0-B case ID 与四折集合关系 | PASS | 420/100 分离，A–D 完整互斥覆盖 |
| P0-C manifest/lineage 元数据 | PENDING | 未获精确数据读取授权 |
| P0-D development84 表示审计 | PENDING | 未打开任何点云或 GT payload |
| L1 实现 | LOCKED | 等待完整 P0 与单独实施授权 |
| L2 零更新 preflight | LOCKED | 未授权 |
| L3 人工输入 benchmark | LOCKED | 未授权 |
| L4 训练 | LOCKED | 未授权 |

