# H1下载核验与M0统一CPU评分准备

日期：2026-11-07（Asia/Shanghai）。结论：**本机归档及配对核验通过；评分范围已冻结；现有评分入口需限定适配。**

本轮只读本机备份、既有元数据、参考文件和源码，所有新报告写在项目目录。没有修改备份、解压到备份目录、访问服务器、加载checkpoint、运行模型或计算评分。

## 1. H1本机备份核验

已核验目录：

`E:\ResearchBackups\AdaPoinTr\BCSP_MAMBA_P2_H1\2026-11-07_C_D_development_eval`

压缩包19059283 bytes，SHA256：

```text
48d93ab773d62fe5a59f89f98a7ce97743e6a261e997e23861bbcb35a0f8e1ed
```

压缩包、SHA256/bytes/contents三个校验文件的大小与哈希，均与服务器正式冻结审计一致。215成员的类型、路径、大小、顺序和内容哈希逐项核验；210份预测的float32、8192×3和有限值通过；固定coarse共12份（C7/D5）、256×3。归档含完整manifest、forward journal、geometry、state/RNG完成记录和资源证据；并非只有预测数组。

**因此，本目录已经具备本次H1预测归档的经核验本机副本。** 这不授权删除服务器产物。

## 2. 冻结M0基线与共同参考核验

重新核验两个原始P1预测归档及其各自三个sidecar：

- C：`E:\ResearchBackups\AdaPoinTr\BCSP_MAMBA_P1\2026-11-06_FoldC_paired_development_eval`；归档SHA256 `068dd9812c410c2b84451740a3ed2eb2f12326d8a66fe3bc3ee4623ab3f9b733`。
- D：同根下`2026-11-06_FoldD_paired_development_eval`；归档SHA256 `8e9c7d5bc49ee91819a7c555ba6b34c5a936f60fcc6f468eadbfcbe4467b9af3`。

两个归档各215成员、210份T0/M0预测及固定coarse均完整通过，本次不是只相信旧回执。未来统一比较只取其中M0的每折105份，T0不进入本次两臂评分，也不重新推理基线。

逐病例核对H1与原M0的case/source/fold、输入文件hash/bytes、D-only center/scale、normalization_source、target_array_sha256及开发顺序。C/D各21来源、每来源5缺损，合计210唯一病例、42唯一来源，全部匹配。

已有评分参考与本机点集**420个文件**（210 reference＋210 point file）逐个重新测量bytes/SHA256，保持原参考与GT指纹。此处只读其字节做哈希，没有解码GT/输入数组或计算任何距离。归档/参考/源码读取前后大小、mtime/ctime保持，备份写入0。

## 3. 冻结的统一评分范围

| 项目 | 数量/合同 |
|---|---|
| 模型臂 | M0与M_H1 |
| Fold C | 105例，每例两模型＋共享Nop_D/GT_8192 |
| Fold D | 105例，同协议 |
| 模型评分行 | 420 |
| 共享控制行 | 420，每病例每控制只算一次 |
| 总病例评分行 | 840 |
| 来源评分行 | 168（42来源×4臂/控制） |
| 差值 | M_H1−M0，距离负/覆盖正为改善 |
| 主指标 | A1面积加权E P95，先每来源5缺损均值、再每折21来源等权 |

E/J、双向CD、反向A2离群、coarse/dense几何、风险代理及阈值保持冻结定义。继续报告严重事件新/救回/共有/均无转移，不能只看净数量。Native world mm，无ICP或GT对齐；完整报告退化病例和缺损分层，不筛病例。

核心指标引擎不变：`bcsp_eval_metrics_v1.py`，SHA256 `af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766`。

本轮未执行评分、bootstrap、p值或正式gate。既定H1资源晋级规则仍保留；未来评分冻结后再解释是否满足，不在预测/准备阶段改阈值。

候选资源：RSS8GiB、输出2GiB、2线程；两折840行的wall预算拟为14400秒，是原单折420行7200秒的两倍，不是实验效果阈值变化。该预算尚待最终实现/request锁定。

## 4. 为什么还不能直接创建可执行评分request

现有评分入口写死`T0/M0`、单折105例/21来源、单个210预测归档和7个代表病例，差值字段也命名为M0_minus_T0；另一D入口仅把fold和代表数量改为D/5。新任务需要从**一个H1两折归档＋两个P1基线归档**正确取出M_H1/M0并分别路由C/D参考，无法通过只替换标签文件就安全运行。

需要的限定实施是：新增一个隔离的H1/M0两折评分入口，复用原metric及评分函数，适配多归档lookup、每折105索引与42来源汇总、H1完成状态和每fold coarse代表、840行计数及delta命名。原P1入口保持不变。人工CPU测试应覆盖实际reader与两折分派、错误绑定拒绝、模型/控制计数和不完整即停；P3通过后再创建绑定最终哈希的待授权评分request。

这不需要新训练、重新预测、GPU preflight或通用审计框架。代码适配/人工测试未在本轮执行，因此没有用占位哈希生成“最终request”。

## 5. 本轮产物

- `local_archive_and_pair_verification_v1.json`：H1与两M0基线归档、全部成员和数组的核验结果及来源配对证据。
- `H1_M0_twofold_score_case_index_candidate_v1.json`：210例的原参考/点集绑定。
- `unified_CPU_scoring_protocol_candidate_v1.json`：840病例行、168来源行及固定评价合同。
- `scoring_request_preparation_draft_v1.json`：入口兼容性和最小实施范围；明确`is_execution_request=false`。

本次未操作服务器，未修改评分器、数据、权重或任何备份文件，尚无H1效果结论。
