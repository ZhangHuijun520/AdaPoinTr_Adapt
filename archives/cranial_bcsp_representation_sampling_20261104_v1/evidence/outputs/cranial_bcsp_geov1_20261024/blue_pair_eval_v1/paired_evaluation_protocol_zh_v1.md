# 欧氏／表面图距离采样：Fold C开发集配对评价协议 v1

日期：2026-11-04。状态：待单独执行授权。本轮仅本机准备，未连接服务器、安装或运行真实模型。

## 研究问题与固定设计

比较固定点数的欧氏消减采样Euclidean_elimination与表面图距离版本surface_graph，在相同B0 AdaPoinTr模型条件下是否改善缺失骨块完整边界补全，重点是未知原始表面E与共享切壁J。两臂训练与正式配对审计均已完成，不以训练loss判定胜负。本阶段不是Mamba结构创新对照。

固定SkullBreak Fold C、seed0，21个开发来源、每来源5类缺损，共105例。两臂各105次native forward，共210次；输入与输出8192点。两臂均用已审计epoch99、3900更新的final权重，不另选epoch或checkpoint。顺序为欧氏105例后图距离105例，病例顺序由冻结fold指定；模型逐个加载。

使用已保存的开发点集，逐例验证文件SHA256、float32形状与有限性、目标数组一致、D-only归一化和共同点序；不重新采样、不重复置换。GT8192仅用于数据核对及之后CPU评分，GPU预测读取partial键，不读取implant键。训练／开发来源互斥，不访问确认集、Fold D、SkullFix或MUG。图距离是基于原表面邻接的离散路径近似，不表述为精确连续测地距离或严格最小半径Poisson-disk。

该设计评价“训练和部署均采用各自采样方法”的整体效果，不分离训练采样效应与推理输入效应；不新增交叉采样四格实验。

## 固定指标及解释

继承原105例由G/D几何生成的冻结A1面心／面积参考，不依据本次预测重建参考或筛选病例。主指标为A1未知原始表面E_G→预测的面积加权P95（mm）；先对同来源5缺损取算术平均，再21来源等权。关键次指标是J_G P95、J_G Cover@2mm、E_G Cover@2mm和同GT8192的CD-L1（双向最近邻距离均值之均值，不平方）。D-only逆归一化回物理mm。

统一报告surface_graph−Euclidean_elimination差值，距离负值更好、覆盖率正值更好。保留全部固定病例，列出来源级差值、缺损类型及明显退化病例；不按结果剔除病例。E改善但J退化时报告权衡，不宣称整体胜出。反向离群距离及A2/B离散敏感性作为诊断，GT8192／输入原样预测为CPU控制。

单fold、单训练seed的探索对照，仅作描述性比较，不新增bootstrap、p值、正式gate或临床阈值。J为G/D共享切壁，相关距离／覆盖率不能认证骨厚度、内外板解剖标注、接触间隙、网格实体拓扑或临床适配。

## 执行合同与运输范围

native eval/inference_mode、FP32、严格deterministic、TF32/AMP关闭，复用原生PointNet2及全key query-chunk256 KNN。无训练、optimizer、loss、backward、BNCal、warmup、TTA、投票或重复预测。模型参数／BN与Python、NumPy、CPU及CUDA RNG前后必须一致。

预算保持wall7200秒、RSS8GiB、Torch allocated/reserved20GiB、SMI22528MiB、输出1GiB、最低可用磁盘4GiB。PID仅诊断，无专属cgroup或GPU独占承诺。执行前重新核验当前hostname/GPU/Python、固定模型／provider和两个checkpoint哈希、上传包、全部213目标及新目录不存在性。CPU合同通过不证明当前CUDA推理通过。

运输包只含210份开发点集及预测入口、index、receipt共213文件，不含checkpoint、原始NRRD、参考NPZ或训练数据。使用精确Linux安装映射，Windows溯源路径不用于服务器命令。独占写入、不覆盖；授权回执→其SHA256→runtime→单次launcher／claim→唯一tmux。任何异常立即停止，不自动修复、重试、resume、扫描参数或追加训练。

## 分阶段边界

本轮限定适配既有两臂评价入口，仅替换采样身份／阶段和精确路径，计算循环、原生输出、状态／RNG守卫及指标代码保持原逻辑。20项人工CPU合同通过；只使用Tiny BN、人工张量／checkpoint，没有加载真实模型或权重。最终运输包还应完成全部成员回读及重复／缺失目标拒绝检查，再冻结P3与待授权request。

单独授权完整request后才可核验上传、安装及执行唯一一次210预测。预测结束后另行授权正式只读冻结审计，再手动下载归档并在本机核验；之后单独适配／授权统一CPU评分。本request冻结评分定义但不授权评分执行；不直接套用旧V1／Morton的硬编码评分入口。
