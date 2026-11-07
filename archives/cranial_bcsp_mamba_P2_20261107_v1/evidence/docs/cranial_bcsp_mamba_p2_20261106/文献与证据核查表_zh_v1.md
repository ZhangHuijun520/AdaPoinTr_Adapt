# 文献与证据核查表

检索/核对截止2026-11-06。以出版社、会议官网、作者arXiv和PubMed原始元数据为依据；专用学术检索连接器未提供，使用网页检索与原始页面核对。不是PRISMA系统综述，不声称穷尽。摘要/预览核查不能替代全文复现；“有代码链接”不表示已经验证代码可运行或许可证合适。

检索主题包括 Mamba point cloud completion、geometry anchors/coarse queries、medical/skull completion、cranial implant trustworthiness。优先查2025–2026新增工作，并向前补充直接相关方法。

| 文献与原始来源 | 年份/状态及核查深度 | 本计划采用的用途与限制 |
|---|---|---|
| [AdaPoinTr: Diverse Point Cloud Completion with Adaptive Geometry-Aware Transformers](https://arxiv.org/abs/2301.04545) | 2023；作者摘要/元数据，结合本地实际母版代码 | query与decoder母版；不能据论文概括替代本项目实际loss |
| [High-resolution Cranial Defect Reconstruction by Iterative, Low-resolution, Point Cloud Completion Transformers](https://arxiv.org/abs/2308.03813) | MICCAI2023；作者摘要/元数据 | 颅骨点云补全先例；本次不声称已验证其全部采样实现细节 |
| [AnchorFormer: Point Cloud Completion From Discriminative Nodes](https://openaccess.thecvf.com/content/CVPR2023/html/Chen_AnchorFormer_Point_Cloud_Completion_From_Discriminative_Nodes_CVPR_2023_paper.html) | CVPR2023，13581–13590；官方索引摘要；直接打开受限 | 输入条件锚点先例；本项目只输出G，不能直接拼接D |
| [SeedFormer: Patch Seeds Based Point Cloud Completion with Upsample Transformer](https://arxiv.org/abs/2207.10315) | ECCV2022；作者摘要/元数据 | 区域种子与coarse-to-fine先例 |
| [CompletionMamba: Taming State Space Model for Point Cloud Completion](https://pubmed.ncbi.nlm.nih.gov/40853794/) | IEEE TIP2025，34:5473–5485；摘要/元数据；DOI 10.1109/TIP.2025.3597041 | 直接相关Mamba补全；本次未取得付费全文 |
| [A point cloud completion network integrating Mamba and transformer architectures](https://www.sciencedirect.com/science/article/pii/S0957417425044410) | Expert Systems with Applications313:130826，2026-06-01；出版社摘要/预览；DOI 10.1016/j.eswa.2025.130826 | 与Mamba encoder＋Transformer decoder直接相关；不横比PCN和颅骨数值 |
| [FusionMamba: Efficient 3D point cloud completion via spatially-aware state space models and multi-scale information fusion](https://www.sciencedirect.com/science/article/pii/S1566253526002575) | Information Fusion134:104378，2026-10刊期；官方摘要/预览；DOI 10.1016/j.inffus.2026.104378 | 空间SSM/几何融合相关先例；未核全套方程或代码 |
| [DAPointMamba: Domain Adaptive Point Mamba for Point Cloud Completion](https://ojs.aaai.org/index.php/AAAI/article/view/37596) | AAAI2026，40(8):6653–6661；官方索引摘要，页面有访问保护；DOI 10.1609/aaai.v40i8.37596 | 域适应补全，不能当成已验证的临床方法 |
| [CloudMamba: Grouped Selective State Spaces for Point Cloud Analysis](https://arxiv.org/abs/2511.07823) | AAAI2026，40(11):8659–8667；作者摘要及官方索引；DOI 10.1609/aaai.v40i11.37818 | 点云分析/序列化相关；不是补全性能证据；与同名云检测论文区分 |
| [Hyper-PCN: Hypergraph-Based Point Cloud Completion via High-Order Correlation Modeling](https://openaccess.thecvf.com/content/CVPR2026/html/Li_Hyper-PCN_Hypergraph-Based_Point_Cloud_Completion_via_High-Order_Correlation_Modeling_CVPR_2026_paper.html) | CVPR2026，39121–39130；官方索引摘要，直开受限 | 高阶几何关系；不因此要求本项目加hypergraph |
| [MedPCFM: Improving Medical Point Cloud Completion by Integrating Point Transformers and Flow Matching](https://arxiv.org/abs/2606.24433) | 2026-06-23预印本；摘要与HTML全文相关方法段 | SkullFix/Break、PTv3确定性/生成基线、点数；协议不同，不横比绝对分数 |
| [MedPCFM-TED: One-Step Point Cloud Flow Matching for Implant Generation via Teacher-Guided Endpoint Distillation](https://arxiv.org/abs/2609.16934) | 2026预印本；摘要；[SASHIMI官方](https://papers.miccai.org/miccai-2026-sat/SASHIMI_017.html) | MICCAI卫星研讨会，不写成主会论文；不把其速度迁移为本项目效率 |
| [Automatic Skull Reconstruction by Deep Learnable Symmetry Enforcement](https://arxiv.org/abs/2411.17342) | 作者预印本2024；2025正式出版记录；摘要/元数据 | 解剖对称性先例；不能默认所有缺损适合对称硬约束 |
| [Structure-Preserving Point Cloud Completion with Symmetry-Guided Progressive Refinement](https://www.mdpi.com/1424-8220/26/11/3536) | Sensors2026，26(11):3536；官方索引/正文片段；DOI 10.3390/s26113536 | 结构/对称融合相关；通用对象，不是颅骨临床证据 |
| [TriFlow: Triplane Latent Conditional Flow Matching for Efficient 3D Skull Shape Completion](https://papers.miccai.org/miccai-2026/1089-Paper1927.html) | MICCAI2026官方摘要 | triplane生成路线；官网代码N/A，不预先安排代码复现 |
| [LOT-Bridge: A Latent Optimal Transport Bridge Based on Signed Distance Fields for Automatic Skull Defect Reconstruction](https://papers.miccai.org/miccai-2026/0596-Paper1071.html) | MICCAI2026官方摘要 | SDF/latent bridge路线；官网列代码链接，本次未验证可运行性/许可 |
| [Plausible but Unimplantable: A Trustworthiness Audit of Shape Completion Foundation Models for Cranial Defect Reconstruction](https://arxiv.org/abs/2610.30035) | 2026-10-21预印本；作者注明ACCV2026 TrustFMI接收；摘要与HTML相关段 | no-op/放置性评价警示；零样本模型，不得外推本项目失败率；其缺损表面构造不等同本项目切壁表示 |
| [Thickness and Design Features of Clinical Cranial Implants—What Should Automated Methods Strive to Replicate](https://pubmed.ncbi.nlm.nih.gov/38430381/) | 2024；摘要/元数据；DOI 10.1007/s11548-024-03068-4 | 临床设计与合成骨块差异；不能据二值GT宣称临床制造级精度 |
| [BuildingComSSSM: Building point cloud completion with Geometry-Aware Mambas](https://www.sciencedirect.com/science/article/pii/S1569843226001858) | 2026，International Journal of Applied Earth Observation and Geoinformation149:105269；出版社摘要/元数据；DOI 10.1016/j.jag.2026.105269 | 建筑领域的几何Mamba补全，作为邻域先例；非医学基线强制项 |

## 本地证据的核查范围

已对照用户计划、P1正式报告/closeout、C/D冻结复盘、既有H1草案、AdaPoinTr真实loss函数及P1 runtime。历史D2.1负结果来自本地已归档报告，不能与BCSP新任务合并计数。

本次未重新读取大量NPZ、checkpoint或体素payload，没有跑推理、评分或训练。归档状态引用本机既有verification/cleanup记录，不把“曾记录有文件”写成“本次又验证了大归档全部payload”。

主计划和审阅说明中所有拟新增训练、probe、GPU调用均是建议，尚未发生。证据绑定清单单独保存本次实际读取的小文件的路径、大小和SHA256，以便区分直接核验与历史引用。
