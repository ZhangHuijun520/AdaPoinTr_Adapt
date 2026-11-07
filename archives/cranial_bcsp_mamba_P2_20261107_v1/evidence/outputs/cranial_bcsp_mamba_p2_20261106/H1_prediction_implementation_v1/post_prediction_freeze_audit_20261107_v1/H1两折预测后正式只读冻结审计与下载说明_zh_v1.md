# H1 C/D两折开发集预测：正式只读冻结审计

日期：2026-11-07（Asia/Shanghai）。结论：**PASS，22项汇总核验通过。**

request SHA256：`90df035abba6cb6651f323ce65f5477f2a9bd0b3a7a505a5ebcc376b7436c147`。

## 完成性与完整清单

退出码0；固定tmux已退出，worker不存活。输出严格为13个顶层文件、predictions目录中的210个NPZ、空tmp目录，总223个文件。权限/归属、无链接替代、全部内容哈希通过；审计前后223个文件的SHA256、大小、mtime/ctime、权限和uid/gid完全一致。atime不作为内容稳定性指纹。

manifest与forward claim journal各210行，索引连续1至210；C_M_H1105例、D_M_H1105例，各21来源×5缺损，共42个来源。每折病例顺序、训练/开发隔离、原始输入hash、目标/坐标来源和相应checkpoint绑定均与冻结index一致。没有基线重新推理、warmup/TTA或额外forward。

210份prediction数组均为8192×3、little-endian float32、非Fortran顺序、全部有限。固定代表病例coarse为C7份、D5份，每份256×3，其余文件不额外保存coarse或GT数组；总核验5170176个有限float32值。210条同次forward几何摘要完整。这里读取的是授权预测输出，不是原始输入/GT payload。

## 状态、RNG与实现

两模型均为eval/inference_mode，各105次前后persistent-state（参数/BN等）指纹一致；Python、NumPy、CPU及CUDA RNG指纹逐项一致。factory构造证据与冻结训练记录一致，仍是真实M0、seed0、六个替换分支。H1唯一配置与最终入口/P3/源码哈希、授权→runtime单向绑定和唯一claim均通过。

该结论基于保存的前后指纹及冻结代码，不是独立重新加载模型重放，也不证明执行期间每一时刻的状态不曾瞬态变化。审计未加载权重或创建模型。

## 资源与权限

423条资源记录逐条通过，阶段次序为每模型开始、每次forward前后及最终完成。RSS峰值1906114560bytes，torch allocated峰值214610944bytes，reserved峰值253755392bytes，SMI使用峰值692MiB；监测时段约47.654秒。PID保持诊断口径，采样监测不等于硬隔离。

训练更新、loss、backward、optimizer、BNCal均为0。新增审计forward/backward/optimizer均为0，服务器写入0。没有评分、bootstrap、正式gate或H1效果解释。

## 归档与下载清单

归档严格包含**215个唯一普通文件成员**：210份预测＋inference manifest、forward journal、geometry summary、inference_complete和resources五份证据。归档内外bytes/hash逐成员一致，无越界、绝对路径或链接。三个sidecar内容、大小、hash均独立核验。

服务器目录：

```text
/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2_h1/C_D_M_H1_development_20261106_v1
```

请下载以下四个文件：

| 文件名 | bytes | SHA256 |
|---|---:|---|
| development_predictions_v1.tar.gz | 19059283 | `48d93ab773d62fe5a59f89f98a7ce97743e6a261e997e23861bbcb35a0f8e1ed` |
| development_predictions_v1.tar.gz.sha256 | 100 | `8d434a8d183f20ca5da31bd3f2c6a84494ae023b2b00a80d29cecabab4165059` |
| development_predictions_v1.tar.gz.bytes | 9 | `9f89dcaae7f1737af7c3412a7ebf4931cc96b914df3e325a7ee10309dc9967fa` |
| development_predictions_v1.tar.gz.contents.sha256 | 24297 | `5629eae8c80d9a86aee7feab635d4f79bf3bb319016b72d34dbd0d286a317edd` |

建议本机位置（本轮未创建/下载）：

```text
E:\ResearchBackups\AdaPoinTr\BCSP_MAMBA_P2_H1\2026-11-07_C_D_development_eval
```

机器可读精确清单见`download_manifest_v1.json`。服务器归档已验证不等于已有本机备份；下载后需本机核验，不能因此删除服务器文件。

## 下一步

下载四文件并核验本机归档：压缩包SHA256/bytes、sidecar、215成员哈希和210预测计数。随后核验既有P1 M0 C/D预测归档与共同reference的case/input/target/frame配对，限定准备统一CPU评分，不重新推理基线。

评分入口尚需核对是否接受H1 run labels、两折索引和新归档；必要时限定适配并验证/P3后创建待授权评分request。评分定义、来源等权及事前H1晋级规则保持，不根据训练loss调参。当前尚无Native E/J/CD或严重风险结果，不能判断H1有效。
