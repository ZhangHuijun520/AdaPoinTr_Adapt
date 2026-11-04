# V1与Morton两臂：Fold C开发集配对评价方案 v1

日期：2026-11-03。状态：待单独执行授权；本轮仅本机准备，未连接服务器。

## 研究问题与固定范围

比较面积均匀V1与冻结Morton等面积分层8k采样能否改变缺失骨块完整边界的预测质量，重点为未知原始表面E和缺损接触切壁J。本阶段模型为B0 AdaPoinTr，不是Mamba创新实验。使用已正式审计的两个final checkpoint，均epoch99、3900 updates；不选最佳epoch，不改权重或BN统计。

固定SkullBreak Fold C、seed0、21开发来源、每来源五缺损，共105例。每臂105次native forward，共210次，输入与输出均8192点。无warmup、重复投票、TTA、loss、backward、训练、BNCal。顺序固定为V1全部105例后Morton全部105例，逐病例顺序与冻结fold一致；模型逐个加载到GPU。

两臂使用各自同一采样规则的开发输入，延续训练阶段相同的逐病例PCG64固定点序政策。仅重排已存在的seed0点集，不重采样；GT8192、D-only归一化及病例身份相同。本机逐例回读及反置换验证已完成。训练来源与开发来源互斥；不接触确认集、SkullFix、MUG或Fold D。

该两臂设计比较训练与部署均采用各自采样方法的整体效果，不分离训练采样效应与测试输入采样效应；没有新增交叉采样四格推理。

## 评分定义与结论边界

继承已冻结、由真实G/D生成的A1面心及面积权重参考，复用105例原始参考，禁止依据当前预测重新构造参考或挑病例。G完整边界分成未知原始表面E和与D共享的切壁J。主终点是A1 E_G→预测的面积加权P95，单位mm；先对同source五缺损取算术均值，再21来源等权。关键次指标为J_G P95、J_G Cover@2mm、E_G Cover@2mm及同GT8192的CD-L1（双向最近邻平均距离之均值，不平方）。D-only逆归一化回物理mm，模型不读取GT。

统一报告Morton−V1差值：距离负向更好，覆盖率正向更好；报告来源级差值、五类缺损及退化病例，不因结果差而剔除病例。主指标改善但J退化时，明确报告权衡，不宣布整体胜出。辅助列出反向离群距离、A2/B离散敏感性，以及GT8192／输入原样预测的CPU控制。单折单训练seed，仅描述性探索比较；不新增bootstrap、p值或正式gate，不外推临床精度或Mamba收益。J覆盖和距离并非完整植入物接触吻合、骨厚度、实体/网格拓扑或临床验证。

## 执行与资源合同

固定FP32、严格deterministic、TF32/AMP关闭，复用原生PointNet2和全key query-chunk256 KNN，不安装、编译、下载或升级依赖。eval/inference_mode；参数/BN及Python、NumPy、CPU/CUDA RNG前后必须一致。资源阈值沿用既有评价：wall7200秒、RSS8GiB、torch allocated/reserved20GiB、SMI22528MiB、输出1GiB、最低空闲磁盘4GiB；PID仅作诊断，不声称独占cgroup。

执行授权后先实时核对固定hostname/GPU/Python、复用资产和两个checkpoint哈希、上传包哈希、全部新目标不存在、GPU空闲与磁盘。213文件包只含210开发点集和入口/index/receipt三个文件，不含checkpoint或原始NRRD。按冻结映射独占写入；五个全新数据目录、控制目录、输出目录均不得覆盖。授权回执单向绑定内层request，runtime再绑定回执哈希，随后单次launcher和claim；只启动一次tmux。异常立即停止，不自动修复、重试或resume。

## 验证与分阶段授权

新入口从既有四模型评价工具限定派生，仅改变两臂合同、路径、checkpoint阶段及补充RNG断言，模型、provider和数值内核不变。20项人工CPU合同通过；实际运输包213成员完整回读哈希及两项异常拒绝通过。CPU测试包含人工Tiny BN张量与人工checkpoint，不加载真实模型或权重，不能证明当前CUDA推理成功。当前容器信息继承刚完成的正式审计，不替代执行前实时核验。

```mermaid
flowchart LR
    A[本机准备与待授权request] --> B[手动上传并单独授权完整哈希]
    B --> C[实时核验及不覆盖安装]
    C --> D[唯一一次210预测]
    D --> E[另行授权正式只读冻结审计]
    E --> F[核验手动下载后单独授权统一CPU评分]
```

本次request只覆盖未来一次部署与GPU预测，不授权本机评分。预测成功后须先正式只读冻结审计，再下载归档并核验；使用当前冻结参考/指标适配两臂评分入口并单独授权。旧四模型评分入口硬编码420条，不能直接冒用为当前两臂评分实现。当前不材料化生产authorization、runtime、launcher或attempt文件。
