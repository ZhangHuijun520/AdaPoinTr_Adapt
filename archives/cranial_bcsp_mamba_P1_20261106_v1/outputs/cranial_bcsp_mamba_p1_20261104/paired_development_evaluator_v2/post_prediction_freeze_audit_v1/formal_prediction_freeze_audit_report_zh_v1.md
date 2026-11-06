# P1 Fold C T0/M0 配对预测：正式只读冻结审计

日期：2026-11-06。结论：FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS。退出码0；T0/M0各105例，合计210次forward和210份预测。此结论为产物完整性及执行合同核验，不是模型优劣或临床精度结论。

## 审计范围与边界

当前容器v2iwsa-0，UID1000，项目/home/jovyan/adapointr_work/PoinTr。绑定已消耗的v2 request SHA256：187a19712d92cb5cdf92eebc2a46ffe5caf6e99614224bc8fbac0a2498e76b82。仅运行内存中的stdlib只读审计；服务器写入0、模型导入0、checkpoint反序列化0、CUDA调用0、forward0、评分0。预算60秒/2GiB，实际耗时2.199秒、读取945373325 bytes。读取权重只用于流式SHA256，没有加载模型。

## 核验结果

全部12组检查通过：

1. 会话与worker已结束、退出码0；9个安装文件及4个控制文件逐一核验大小/SHA256，精确集合一致。
2. 授权回执、runtime单向绑定、单次启动claim与本机原材料化记录一致，未复用旧request。
3. 两份最终checkpoint、105份唯一输入文件及factory/encoder/helper等相关绑定重新哈希一致。
4. 同一21个开发来源、每来源5种缺损、105例顺序与C开发清单一致，并与63个C训练来源隔离；两臂输入/目标指纹与D-only坐标一致。
5. 210条调用前claim、210条成功manifest、210条几何摘要按同一顺序精确匹配；每臂105例。训练更新/BNCal/loss/backward均为0。
6. 两臂parameters/BN状态哈希、CPU/CUDA/Python/NumPy RNG前后记录相等；均为eval/inference_mode。
7. 构造证据确认T0保留原分支、M0替换六个分支并记录原生Mamba类；共享初始化指纹相同。
8. 210份NPZ逐文件SHA256核验，prediction均为有限float32、8192×3；冻结7例/臂共14份coarse为有限float32、256×3；没有GT数组或未声明成员。
9. 全部dense摘要及已保存14份coarse摘要的质心、包围盒、回转半径/协方差迹与实际数组核对；其余coarse仅验证记录有限性，未伪称可独立重建。
10. 423条资源记录的阶段/计数顺序正确；逐条按原阈值独立重算均通过。
11. 归档215个普通文件成员的名称/顺序/大小/哈希全部与现场一致，无重复或链接成员；四个下载文件及三个校验侧车内容全部核验。
12. 完整输出集合为223个文件；输出及所有已读证据的内容相关指纹在审计期间稳定，排除atime干扰；无失败文件、无额外预测或checkpoint。

## 资源证据

记录的RSS最大值1677221888 bytes（约1.56GiB），设备显存最大692MiB，torch allocated峰值214610944 bytes（约204.7MiB），reserved峰值253755392 bytes（242MiB）。记录的预测预算耗时46.098秒。资源记录的output最大值发生在归档前；审计另核对归档后实际总输出38791367 bytes，仍低于1GiB阈值。各模型开始时会重置torch峰值计数，此处为所有采样记录的最大值；采样监测不等于硬cgroup隔离。

## 归档与下载

服务器目录：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1/FoldC_T0_M0_development_20261106_v2`

下载以下四文件，建议放置于 `E:\ResearchBackups\AdaPoinTr\BCSP_MAMBA_P1\2026-11-06_FoldC_paired_development_eval`。本轮只将文本审计证据冻结到项目内，未把预测压缩包下载到Windows，不能据此删除服务器原件。

| 文件 | bytes | SHA256 |
|---|---:|---|
| development_predictions_v1.tar.gz | 19045938 | 068dd9812c410c2b84451740a3ed2eb2f12326d8a66fe3bc3ee4623ab3f9b733 |
| development_predictions_v1.tar.gz.sha256 | 100 | a7d512d1687a7c74a118b736c223d3b6ef218b4d531c698e67799ba9ead28420 |
| development_predictions_v1.tar.gz.bytes | 9 | 3015c5c61ab48dd2a4eedde5664ea033342ed6c00d938f0a35ed00fda373e88d |
| development_predictions_v1.tar.gz.contents.sha256 | 23877 | 871570eb4fca63fc9367d979d061e39cc63e77368eeaf22ce43a8c1d90ee95d2 |

逐文件清单、资源最大值、状态/RNG原始指纹见audit_report_v1.json。原样保存的12份元数据见frozen_metadata，均已在本机重新校验字节与哈希。

## 限制及下一步

状态/RNG审计核验的是运行时记录及其来源，不会独立重建模型状态；不证明CUDA全程位级确定性或临床接口质量。几何摘要核验仅用于完整性，不计算GT误差或选择候选。未新增评分request、训练或GPU准入。

下一步手动下载四文件，完成本机哈希与成员核验后，再单独准备/授权统一CPU评分，以回答M0相对T0的补全与接口效果。服务器文件应继续保留，未经备份确认及删除授权不清理。
