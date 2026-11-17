# TRACE D0：本机下载核验与CPU分析准备

日期：2026-11-17。状态：**四文件下载及84成员核验通过；CPU分析request待授权；未执行分析。**

## 本机长期保存位置

`E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_TRACE/2026-11-17_D0_memory_evidence/`

已保存：

- `development_predictions_v1.tar.gz`
- `development_predictions_v1.tar.gz.sha256`
- `development_predictions_v1.tar.gz.bytes`
- `development_predictions_v1.tar.gz.contents.sha256`

归档84179082 bytes，SHA256：

`509dde04102c49ab0de13f9e1d8821491a6371109cf5f1934d8cc585ad03feb9`

四文件内容关系与正式服务器冻结证据一致；84个普通成员逐一回读大小和SHA256通过，包含80份trace。没有解压落盘、解码NPZ数组或进行数值分析。下载日志、退出码、范围及本机核验回执保存在备份目录中。

## CPU分析准备

复用已完成人工CPU验证／P3的分析实现，没有修改观察器、GPU入口或分析公式。

已按冻结40病例核验80个本机参考文件绑定：每病例一份参考曲面容器和一份既定点集容器。本次仅核验容器字节／SHA256，未读取GT数组。历史SPCG预测归档、病例评分文本及评分器哈希均核对通过。

唯一拟执行内容：

1. 80条TRACE记录与历史同病例Native Q/P重放对照，检查逐元素／世界坐标、E/J距离、Cover及风险标签是否满足事前界限。
2. 核验实际原生FP32近邻索引与距离矩阵，计算既定FP64空间描述量；不以FP64排序替代实际消费者索引。
3. C折17个、D折18个非压力来源的固定主要相关及类型调整相关；5个已曝光案例单列，不纳入主要关联。
4. 结果只可作为投入动机或不支持／不确定，不推导唯一因果结论，也不自动实施G3或训练。

运行范围不包含新forward、GPU、训练、病例筛除、参数扫描或新增bootstrap。固定CPU墙钟预算1800秒，RSS上限8GiB、输出上限1GiB；实际执行需保留前台托管会话并由外部监测器约束，失败即停，不自动重试。现有入口未曾执行完整真实数据重放，因此本机准备通过不保证实际分析完成。

## 最终待授权request

文件：`TRACE_D0_CPU_analysis_execution_request_v1.json`

状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`

完整SHA256：

`78952610006e441f49c0f84caf95134652dea133c0526974325cae86c038d5e9`

拟输出目录：

`E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/outputs/trace_D0_implementation_20261117_v1/CPU_history_replay_analysis_v1`

本轮未创建该输出目录、CPU生产授权回执、执行claim或启动脚本。下一步需单独授权上述完整SHA256，才能执行一次CPU历史重放与空间证据分析；完成后仍须正式只读分析后冻结审计，再解读结果。
