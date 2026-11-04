# BCSP四模型开发集配对评价协议 v1

_2026-10-26 · BCSP_INPUT_DENSITY_V1 · 四组训练后、预测结果产生前冻结的评价实施补充_

---

## 📋 目的和证据状态

比较同折8k与16k输入，是否改善未知原始骨表面和切壁接口；两者均输出8192点。模型为同一AdaPoinTr Transformer基线，不是Mamba架构比较。四组训练均已分别完成正式冻结审计。[原计划](cranial_bcsp_geov1_formal_experiment_plan_zh_v1_1.md)第7节的主终点、世界mm、source配对原则继续有效。

本协议在训练后补齐参考离散化、执行和输出细节，不追认这些新细节为训练前预注册。未提前冻结的临床／disaster阈值不补造；不计算正式通过门或宣称临床可植入。以四模型结果发表之前，保留该时间顺序。

## 🔒 病例、模型和输入

| 项目 | 冻结范围 |
|---|---|
| 四模型 | Fold C/D，各8k/16k输入，seed0，最终3900-step checkpoint |
| 每模型开发集 | 本折21个开发source、每source五种固定缺损，共105例 |
| 总预测 | 420个模型—病例组合；210个唯一病例、42个互斥out-of-fold开发source |
| 排除 | 本模型训练source、20个confirmation source、monitor／official-test |
| 预测 | 每组合一次batch1完整forward，共420次；无warmup、augmentation、投票、重采样、参数扫描或补跑 |
| 模型模式 | `eval()`及`inference_mode()`；加载final checkpoint的全部model state，严格匹配keys；不加载optimizer执行，不重置或校准BN |
| 数值 | FP32、严格deterministic、TF32关闭、既定PointNet2原生provider、query分块256且全key |
| 输入 | 仅既有归一化NPZ的`partial`；不读取`implant`数组、几何参考或J来构造预测 |
| 输出 | eval tuple中的dense项，形状`(1,8192,3)`，有限float32，保存归一化坐标 |

可复用服务器另一折的既有数据目录：C模型开发病例位于D训练目录，D模型开发病例位于C训练目录。合法性按**当前模型自身的source名单、病例ID和原manifest哈希**核验，不按目录名字判断。C/D训练来源按交叉验证设计重叠，不是独立训练总体。

四个checkpoint的原始SHA256和全部实际模型／provider／输入哈希进入执行request。只用`torch.load(..., map_location='cpu', weights_only=True)`读取，严格装载`base_model`；校验stage、epoch99及updates3900。不允许失败后改用不受限pickle加载。

## 📐 固定几何参考和单位

全部预测先用每病例已冻结的D-only `center,scale`逆变换到世界mm：`p_mm = p_normalized * scale + center`。不依据GT重新拟合平移、缩放或ICP。

对唯一210病例，本机只读已绑定的D/G NRRD，复核其SHA256、物理网格及D/G不相交。完整C的守恒证据继承既有全量QC；本次不重新解码C。该限制在参考回执中保留。

- **A1主参考**：G全部暴露体素面中心及其世界面积权重。面邻接D的部分为`J_G`，其补集为`E_G`；`all G=E_G∪J_G`。这是体素并集边界的面心数值积分，不是连续解剖真值。
- **A2敏感性参考**：每个同一体素面固定2×2四分点，面积权重各为原面的1/4。对两模型和控制组全部报告，不根据预测结果选择A1或A2。
- **B交叉参考**：同一G mask、level0.5、占据包围盒裁剪后补一层零、marching cubes、`allow_degenerate=False`，不平滑／填洞／删组件。三角形中心按真实世界三角面积加权，仅报告`all G`。MC没有可靠共享切壁对应，`B/E_G`与`B/J_G`记不可分区，不伪造标签。

参考在任何模型预测前构建并冻结，所有输入方案共用。A2和B都不是可事后替换主终点的候选。局部法向、内外板、孔洞可视化没有可靠解剖标签时，不输出内板／外板各自“已认证精度”。

## 📊 指标、控制和统计

唯一效能主终点为A1的`E_G→P_pred`面积加权P95。加权分位数取累计权重首次达到95%的距离，无插值。区域覆盖为面积权重内距离不大于0.5／1／2mm的比例，三个阈值仅作描述。

必须同时输出：

1. A1及A2各自的`all G/E_G/J_G`加权P95、均值、最大距离及三阈值覆盖。
2. B的`all G`同类指标，作为几何参考交叉检查。
3. `P_pred→固定A2/B表面参考点`的等权均值、P95、最大值及三阈值离群比例。这是离散参考点近似，不称精确点到连续mesh距离、面积NSD或surface HD95。
4. 固定8192点GT参考的CD-L1：`0.5*(mean NN(P,GT)+mean NN(GT,P))`，欧氏mm，不平方、不乘人为倍率。
5. 输出点数、完全重复点数、非有限值、空接口事件和最差source。

每个唯一病例同时计算固定控制：Nop-D原生8k、Nop-D原生16k、固定GT8192采样参考。Nop-D固定8192控制对两模型完全相同；16k原生Nop-D明确标记点预算不同。GT采样参考只反映表示底噪，不是严格最优上界。不增加J-transfer oracle。

每source五种缺损先等权平均，再在各fold及合并的42个唯一out-of-fold source上比较。差值统一定义`16k−8k`；距离负值表示改善，覆盖正值表示改善。按原计划使用10000次配对source bootstrap、seed=20261024、相同抽样索引；区间仅描述固定seed0模型的病例不确定性，不代表训练随机性。不得将两输入臂或五缺损当作独立患者数扩大N。

非有限／空／错误点数的预测记无效：主距离定义为`+inf`、覆盖为0，JSON用明确字符串`POS_INF`保存。GPU阶段遇到无效输出或系统异常即停，不重试；未执行病例另标`NOT_EXECUTED`，不伪装为模型失败或完整420例。未完成全部420例时不发布整体配对结论。若合法完整评分出现非有限source均值，保留总分母，bootstrap/delta不可定义时记NA，不通过删病例制造有限结果。

## ⚙️ 两阶段执行与资源

```mermaid
flowchart LR
    accTitle: Paired Development Evaluation Workflow
    accDescr: References and tools are frozen before one server prediction batch; the user transfers its verified archive for a fixed local metric and source comparison batch.
    refs["本机固定几何参考与工具"] --> scope["冻结待授权GPU预测request"]
    scope --> gpu["单独授权后420次预测"]
    gpu --> transfer["冻结归档并由用户下载核验"]
    transfer --> score["本机统一CPU评分与source配对"]
```

本机参考构建：逐病例串行，线程2，总时限3600秒、每例120秒、监测RSS8GiB、参考输出2GiB；失败即停且保留产物。使用已有NumPy／SciPy／scikit-image，不安装依赖。先完成针对性人工CPU检查，再启动唯一一次参考构建。

服务器预测：外层总时限7200秒、kill grace5秒，RSS8GiB、torch allocated/reserved各20GiB、设备22528MiB、输出1GiB、磁盘保留4GiB；启动前设备不超过256MiB且无计算进程。运行PID仅作诊断，不要求跨namespace归属证明。每模型前后完整model-state哈希一致，记录实际调用数和资源；不调用loss、backward、optimizer、BNCal或development拟合。

预测完成后仅归档420个预测NPZ及推理清单／回执／资源日志；不包含checkpoint。提供tar.gz、SHA256、bytes和内容清单四文件。Windows与服务器不自动同步，由用户下载并在本机核验；未下载前不启动本机评分。

本机评分：固定脚本、参考、病例及指标合同，线程2、RSS8GiB、总时限7200秒、输出2GiB。预测归档完整且哈希核验后才运行；输出逐病例、逐source、配对差值和区间，保存全部失败与NA。评分工具和计划先完成CPU验证；真实评分执行与预测结果绑定后再单独授权。

## ✅ 本阶段完成标准

协议、210病例参考、最小推理入口／CPU评分工具、针对性人工测试、本机P3和待授权GPU预测request均可核验。CPU通过不代表CUDA预测已通过；预测完成不代表评分完成。本阶段不启动训练、不改变现有checkpoint，不计算正式gate或进行新的病例／阈值／超参数选择。
