# Mamba v1.3 D3：MUG500+ Phase M0 元数据准入方案

## 1. 阶段目标

M0 只回答三个问题：

1. Figshare 官方版本 20 的文件清单能否完整覆盖健康颅骨 `A0001-A0500`；
2. 官方文件大小、MD5 和下载 URL 能否被固定为可审计清单；
3. Figshare 下载端点是否支持 HTTP Range，从而允许后续按 ZIP 成员流式抽取，而不在 50 GB 服务器上保存约 195.6 GB 原始数据。

M0 **不下载任何 ZIP 数据载荷，不生成训练病例，也不启动 D3 训练**。

## 2. 数据使用边界

| 数据 | 数量 | D3 用途 | 当前状态 |
|---|---:|---|---|
| 健康颅骨 `A0001-A0500` | 500 | QC、去重后构建新的 skull-level development/confirmation split | 尚未准入 |
| craniotomy skulls and implants | 29 | 模型与规则全部冻结后的外部临床验证 | 锁定，禁止开发阶段访问 |

健康集也不能直接全量用于开发。后续必须先完成固定 QC、跨库重复检查和 skull-level 抽样；建议目标为至少 125 个合格健康颅骨，其中 100 个用于 development、25 个作为 locked external holdout。

## 3. 固定数据源

- Figshare article：`9616319`
- 固定版本：`20`
- DOI：`10.6084/m9.figshare.9616319`
- 许可：`CC BY 4.0`
- 官方页面：<https://figshare.com/articles/dataset/MUG500_Repository/9616319>
- 维护记录：<https://github.com/Jianningli/mug500plus>

禁止使用未记录版本号的 “Download all” 结果替代固定版本清单。

## 4. 运行方式

在服务器代码目录执行：

```bash
cd ~/adapointr_work/PoinTr
conda activate adapointr-mamba
bash scripts/inventory_mug500plus_phase_m0.sh
```

该任务很短，不需要 tmux。若网络不稳定，可以放入 tmux，但不得修改 article id 或 version。

若计算节点访问 Figshare API 返回 HTML `403 Forbidden`，可从能正常访问 Figshare 的浏览器分别保存以下两个官方 JSON 响应：

```text
https://api.figshare.com/v2/articles/9616319/versions/20
https://api.figshare.com/v2/articles/9616319/versions/20/files
```

将其上传为 `/home/jovyan/mug500plus_article_v20.json` 和
`/home/jovyan/mug500plus_files_v20.json`，再执行：

```bash
MUG500_ARTICLE_JSON=/home/jovyan/mug500plus_article_v20.json \
MUG500_FILES_JSON=/home/jovyan/mug500plus_files_v20.json \
bash scripts/inventory_mug500plus_phase_m0.sh
```

离线入口不会信任文件名本身；两个 JSON 仍须通过相同的 article id、version、许可、MD5、大小与 A0001-A0500 覆盖硬校验。

默认输出：

```text
logs/mamba_v13_d3_mug500plus/inventory_figshare_v20/
```

关键文件：

- `article_response.json`：Figshare v20 原始 article 响应；
- `files_response.json`：规范化后的官方文件响应；
- `figshare_files.csv`：全部文件的大小、MD5 和 URL；
- `healthy_archive_index.csv`：健康颅骨分卷及覆盖范围；
- `range_probe.csv`：首、中、末健康分卷及 craniotomy 分卷的字节范围探测；
- `inventory_summary.json`：M0 结论；
- `files.sha256`：以上文件的完整性清单。

## 5. M0 通过标准

以下条件必须同时满足：

1. article id 为 `9616319`，version 为 `20`；
2. 标题包含 `MUG500+`，许可为 `CC BY 4.0`；
3. 文件 ID 与文件名无重复，大小为正，下载地址为 HTTPS；
4. supplied/computed MD5 同时存在时必须一致；
5. 健康分卷精确覆盖 `A0001-A0500`，无缺失、无重叠；
6. 恰有一个 `craniotomy_skull.zip`，且继续保持锁定；
7. `files.sha256` 校验通过。

Range 探测失败不会篡改元数据准入结论，但会改变下一阶段的数据获取方式。

## 6. M0 后的分支决策

### 6.1 Range 探测全部通过

实现 M1 流式 ZIP 成员索引器，只读取中央目录，并按固定 skull ID 下载所需的 `Axxxx_clear.stl`。禁止下载 NRRD、PNG 和非 clear STL。

### 6.2 Range 探测不通过

先在本地 D 盘按固定 skull 抽样清单下载最少数量的健康分卷；本地完成 QC、去重与点云派生，再只上传派生后的 8192 点数据和完整 provenance。服务器仍不保存 195.6 GB 全量原始数据。

## 7. 尚未允许的操作

- 不得把 29 个 craniotomy 病例用于候选选择、超参数调整或阈值设计；
- 不得在 QC 规则冻结前依据模型表现选择健康颅骨；
- 不得把 MUG500+ 与 SkullBreak/SkullFix 的病例级数据混在同一随机划分中；
- 不得启动 S1/S2 比较，直到独立数据锁定器生成新的开发协议并通过全部数据准入检查。
