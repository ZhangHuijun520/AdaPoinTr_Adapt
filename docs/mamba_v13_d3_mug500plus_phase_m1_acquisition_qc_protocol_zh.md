# Mamba v1.3 D3：MUG500+ Phase M1 获取、QC 与去重协议

## 1. 阶段定位

M0 已固定 Figshare article `9616319`、版本 `20`、98 个官方文件、96 个健康颅骨分卷以及 `A0001-A0500` 的完整覆盖。M1 只负责冻结健康 A 系列的获取顺序、STL 准入规则、重复检查和停止条件，不训练模型，也不访问 29 个 craniotomy/B 系列病例。

M1 的目标不是下载约 195.6 GiB 全量数据，而是以分卷为不可拆分获取单元，依照与模型和几何质量无关的预注册顺序逐批获取。每完成一批即运行固定 QC；当至少 125 个唯一健康颅骨通过所有硬门控时，在当前分卷边界停止。

## 2. 固定数据边界

- 允许：官方健康分卷中的 `Axxxx_clear.stl` 及其 Figshare provenance。
- 禁止：`craniotomy skull.zip`、B 系列 skull/implant、NRRD、PNG 和非 clear STL。
- 原始 ZIP 保存在本地 D 盘，不在 50 GB 服务器长期存放。
- D3 训练保持锁定，直到 M1 QC、跨库去重、点云派生以及独立数据锁定器全部通过。

## 3. 确定性获取顺序

1. 只接受 SHA256 为 `f475490611f5d17536bbf76a0f7db0693a668fd3e87e8502ec395db6b461a078` 的 Figshare v20 files JSON。
2. 将 A 系列按编号分为 10 个连续的 50-skull strata。
3. 每个 stratum 内使用固定 salt、分卷名、官方 MD5 和文件大小生成 SHA256 排序键。
4. 各 strata 按固定哈希顺序轮转交错，避免只从病例编号前段或特定文件大小区间取样。
5. 以完整 ZIP 为边界组成目标约 40 个 skull 的批次；不得拆分 ZIP，也不得根据 QC 或模型结果重排后续分卷。

首次只下载 `batch_001_downloads.csv` 中的分卷。后续是否进入下一批只由“累计 QC 合格且去重后的健康 skull 数是否达到 125”决定。

## 4. 冻结 QC

每个预期病例必须且只能对应一个 `Axxxx_clear.stl`。以下任一条件成立即硬失败：

- 文件小于 100 KiB；
- STL 无法按 binary 或 ASCII 格式完整解析；
- 三角面少于 1000；
- 存在非有限顶点；
- 非退化三角面比例低于 0.99；
- 最短包围盒边小于 50 mm，或最长边大于 600 mm；
- 包围盒最短边/最长边小于 0.15；
- 表面积非有限或非正；
- 规范化表面指纹与另一个 skull 重复。

尺度范围刻意设置得较宽，只用于识别单位错误、截断文件和显著非颅骨几何。不得在查看模型性能后收紧或放宽这些阈值。

## 5. 表面指纹

算法标识为 `mug500plus-canonical-triangles-v1-normalized-q1e-5`：

1. 以包围盒中心平移，以最长包围盒边统一缩放；
2. 以 `1e-5` 归一化单位量化顶点；
3. 每个三角面内按顶点字典序排序，再对全部三角面排序；
4. 对算法标识、三角面数和规范化三角面字节流计算 SHA256。

因此指纹不受 STL 三角面顺序、绕序、全局平移和统一缩放影响。它用于识别同一表面的重复导出；不同重建或重网格化仍需在后续跨库近重复审计中补充旋转不变的几何筛查。

## 6. 服务器预检

将 M1 overlay 和 `mug500plus_files_v20.json` 放在 `/home/jovyan` 后执行：

```bash
cd ~/adapointr_work/PoinTr
conda activate adapointr-mamba

bash scripts/prepare_mug500plus_m1_protocol.sh
```

输出目录：

```text
logs/mamba_v13_d3_mug500plus/protocol_m1_v1/
```

关键文件：

- `archive_acquisition_order.csv`：全部健康分卷的固定顺序与批次；
- `skull_acquisition_order.csv`：500 个健康 skull 的 provenance；
- `batch_001_downloads.csv`：当前唯一允许下载的首批分卷；
- `batch_001_expected_case_ids.txt`：首批 QC 的精确病例集合；
- `protocol.json`：顺序、停止规则、QC 与保护边界；
- `files.sha256`：冻结输出哈希链。

## 7. 本地获取与 QC

在本地 D 盘创建：

```text
D:\ResearchBackups\AdaPoinTr\MUG500plus\raw_v20\archives\batch_001\
D:\ResearchBackups\AdaPoinTr\MUG500plus\raw_v20\clear_stl\batch_001\
D:\ResearchBackups\AdaPoinTr\MUG500plus\qc_m1_v1\batch_001\
```

只下载首批 CSV 列出的 ZIP，先核对官方 MD5，再只提取对应 `Axxxx_clear.stl`。QC 可以在 Windows 或服务器运行；若在服务器运行，只上传 clear STL，并在完成派生和哈希归档后删除原始 STL。

服务器示例：

```bash
export MUG500_STL_ROOT=/absolute/path/to/clear_stl/batch_001
export MUG500_EXPECTED_CASES=logs/mamba_v13_d3_mug500plus/protocol_m1_v1/batch_001_expected_case_ids.txt
export MUG500_QC_OUTPUT=logs/mamba_v13_d3_mug500plus/qc_m1_v1/batch_001
bash scripts/qc_mug500plus_m1_batch.sh
```

## 8. 停止与后续

- 累计唯一 QC-pass skull 少于 125：按冻结顺序进入下一完整批次。
- 达到至少 125：完成当前 ZIP 的全部 QC 后停止获取；不得删去“难病例”来改善后续模型指标。
- 达标后：执行 M2 跨 MUG500+、SkullBreak、SkullFix 的 fingerprint/近重复审计，冻结 100 development + 25 locked holdout，再派生点云与合成缺损。
- 若 500 个 A 系列全部处理后仍不足 125：冻结数据准入负结果，不得启用 B 系列补足。
