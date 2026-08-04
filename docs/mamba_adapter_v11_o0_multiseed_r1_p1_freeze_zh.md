# Mamba Adapter v1.1 O0-xyz 多 seed R1/P1 冻结与归档记录

_SkullBreak out8192，seed-0/1/2；冻结日期 2026-08-04_

---

## 冻结结论

`Mamba Adapter v1.1 O0=xyz out8192` 的 R1 多 seed 稳定性复核和 P1 完整 monitor post-hoc 内部诊断现正式冻结。冻结后，不得根据这些结果重新选择 seed、重开 O0/O1/O2/O3 ordering、修改灾难阈值或继续使用已消费的 monitor 调参。

本次冻结不宣称模型已经解决 seed 敏感性。冻结的科学结论是：

- final reconstruction 跨 seed 较稳定；
- implant 与 rim contact 存在明显 seed 波动；
- 三 seed 的实际 512-token 坐标与排序完全一致；
- 两个 Mamba block 的残差分工随 seed 明显重排；
- 当前标量 instrumentation 与病例级 Rim HD95 仅呈弱相关；
- 现有证据只允许生成新假设，不允许作因果归因或模型选择。

机器可读冻结声明位于：

```text
docs/protocols/mamba_v11_o0_multiseed_r1_p1_freeze_v1.json
```

## 冻结对象

### R1 多 seed 稳定性复核

| 项目 | 冻结值 |
| --- | --- |
| 候选 | Mamba Adapter v1.1 O0=`xyz` |
| 输出点数 | 8192 |
| seeds | 0、1、2 |
| strict train | 520 cases / 104 skulls |
| monitor | 50 cases / 10 skulls |
| canonical checkpoint | 每个 seed 的 `ckpt-last-bncal.pth` |
| official test | R1 未运行 |
| 选择行为 | 无 |

灾难规则保持为：

```text
rim_contact_hd95_mm > 50.0 mm，或该值为 NaN/Inf
```

三 seed 的灾难数固定为 `0`、`2`、`3`，不得在后续阶段修改阈值后重写该结论。

### P1 完整 monitor post-hoc 诊断

| 项目 | 冻结值 |
| --- | --- |
| 记录数 | 150 seed-case records |
| 独立病例 | 50 |
| token 坐标和排序跨 seed 一致 | `True` |
| 最大坐标差 | `0.0` |
| 独立灾难病例 | 4 |
| official test | P1 未运行 |
| 允许用途 | 机制解释与新假设生成 |

完整分析见 [P1 中文诊断报告](./mamba_adapter_v11_o0_multiseed_full_monitor_posthoc_diagnosis_zh.md)。

## 归档范围

服务器归档文件固定命名为：

```text
skullbreak_mamba_v11_o0_multiseed_r1_p1_seed012_v1.tar
skullbreak_mamba_v11_o0_multiseed_r1_p1_seed012_v1.tar.sha256
skullbreak_mamba_v11_o0_multiseed_r1_p1_seed012_v1.part-000 ...
skullbreak_mamba_v11_o0_multiseed_r1_p1_seed012_v1.parts.sha256
```

服务器保留完整 tar 作为母本，同时默认生成 128 MB 分块。鉴于此前大文件通过网页下载时发生过截断，本次优先下载全部 `part-*`、`parts.sha256` 和完整 tar 的 `.sha256`，再在本地重组。

归档包括：

- seed-0/1/2 的 canonical BN-calibrated checkpoint 及 BNCal 元数据；
- canonical 冻结配置，以及存在时的各实验目录配置副本；
- seed-0/1/2 的 monitor CSV、summary、训练日志和 tmux 日志；
- strict-train 20-case instrumentation；
- P1 完整 monitor 150-record instrumentation 与全部分析输出；
- R1/P1 冻结协议及报告，以及服务器存在时的 ordering 历史报告；
- 运行脚本、instrumentation、分析工具和关键模型/数据代码；
- 数据 manifest 副本、运行环境、checkpoint 哈希和逐文件 SHA256 清单。

归档明确不包括：

- 原始或转换后的 SkullBreak 数据集；
- official-test 预测和评价结果；
- `ckpt-best.pth`、`ckpt-last.pth`、epoch checkpoint 等重复 checkpoint；
- 新 development folds 或尚未预注册的新候选结果。

## 归档执行

在服务器仓库根目录执行：

```bash
conda activate adapointr-mamba
cd ~/adapointr_work/PoinTr
chmod +x scripts/archive_skullbreak_mamba_v11_o0_multiseed_r1_p1.sh
chmod +x scripts/verify_skullbreak_mamba_v11_o0_multiseed_r1_p1_archive.sh
bash scripts/archive_skullbreak_mamba_v11_o0_multiseed_r1_p1.sh
```

脚本会在打包前验证：

- 三个 BNCal checkpoint 和 sidecar 均存在；
- 三个 monitor CSV 均为相同的 50-case 集合；
- P1 summary 为 150 records / 50 cases；
- token equality 为 `True` 且最大坐标差为 `0.0`；
- `selection_allowed=False`、`official_test_used=False`；
- P1 结果树 SHA256 清单自检通过。

任一门槛失败时，脚本必须停止，不生成正式归档。

### 正式归档结果

服务器母本与本地重组归档已经完成一致性验证：

| 项目 | 冻结值 |
| --- | --- |
| 完整 tar | `skullbreak_mamba_v11_o0_multiseed_r1_p1_seed012_v1.tar` |
| 字节数 | `1219491840` |
| SHA256 | `1d5b3c96d7a4b171fb0924c5a52e302b1cae884382468a63f2145f7cd76e9d09` |
| 下载分块 | 10 |
| 分块校验 | 10/10 通过 |
| 本地重组 tar | SHA256 与服务器母本一致 |
| 解压后逐文件校验 | 通过 |
| 解压后语义校验 | 通过 |
| verification exit | `0` |

正式本地归档目录为：

```text
D:\ResearchBackups\AdaPoinTr\SkullBreak_mamba_v11_o0_multiseed_R1_P1_seed012\server_archive
```

## 本地验收

下载全部分块、`parts.sha256` 和 `.tar.sha256` 到：

```text
D:\ResearchBackups\AdaPoinTr\SkullBreak_mamba_v11_o0_multiseed_R1_P1_seed012\server_archive
```

先在 Windows PowerShell 校验每个分块，再重组完整 tar：

```powershell
$Dir = "D:\ResearchBackups\AdaPoinTr\SkullBreak_mamba_v11_o0_multiseed_R1_P1_seed012\server_archive"
$Tar = "$Dir\skullbreak_mamba_v11_o0_multiseed_r1_p1_seed012_v1.tar"
$Sha = "$Tar.sha256"

$partManifest = "$Dir\skullbreak_mamba_v11_o0_multiseed_r1_p1_seed012_v1.parts.sha256"
$results = Get-Content $partManifest | ForEach-Object {
    if ($_ -match '^([0-9a-fA-F]{64})\s+\*?(.+)$') {
        $expectedPart = $Matches[1]
        $name = [IO.Path]::GetFileName($Matches[2].Trim())
        $path = Join-Path $Dir $name
        $actualPart = (Get-FileHash $path -Algorithm SHA256).Hash
        [pscustomobject]@{Part=$name; Match=($actualPart -eq $expectedPart)}
    }
}
$results
"all parts match: $(($results.Match -notcontains $false))"

$parts = Get-ChildItem "$Dir\skullbreak_mamba_v11_o0_multiseed_r1_p1_seed012_v1.part-*" |
    Sort-Object Name
$output = [IO.File]::Create($Tar)
try {
    foreach ($part in $parts) {
        $input = [IO.File]::OpenRead($part.FullName)
        try { $input.CopyTo($output) }
        finally { $input.Dispose() }
    }
}
finally { $output.Dispose() }

$actual = (Get-FileHash $Tar -Algorithm SHA256).Hash
$expected = (Get-Content $Sha).Split()[0]
"hash match: $($actual -eq $expected)"

tar -tf $Tar | Out-Null
"tar exit: $LASTEXITCODE"
```

验收标准为：

```text
all parts match: True
hash match: True
tar exit: 0
```

随后可解压到空目录，并在 Linux、WSL 或 Git Bash 中运行归档内的验证脚本：

```bash
bash scripts/verify_skullbreak_mamba_v11_o0_multiseed_r1_p1_archive.sh .
```

## 冻结完成判据

R1/P1 只有同时满足以下条件才算完成物理归档：

- [x] 协议、结果和解释边界已经冻结
- [x] 归档与校验脚本已经固定
- [x] 服务器 `.tar`、整体 `.sha256`、分块和分块清单已生成
- [x] 服务器侧整体 SHA256 自检通过
- [x] 全部分块及两个 checksum 文件已完整下载到本地正式目录
- [x] Windows 整体 SHA256 与 tar 结构检查通过
- [x] 解压后逐文件清单与语义门槛检查通过

以上门槛已经全部通过，R1/P1 物理归档正式完成。清理服务器原始文件前，仍应先完成本轮代码、协议和报告的 Git 提交与 tag 冻结。

## 后续约束

归档完成后的下一步仅允许：

1. 基于 strict train 构建新的 skull-level development folds；
2. 在读取新开发结果前预注册候选、指标、灾难规则和选择逻辑；
3. 对 query/coarse/decoder/rebuild head 扩展零扰动 instrumentation；
4. 在新开发集上验证少量机制候选。

不得再次把当前 monitor 或既有 official test 变成候选筛选集。
