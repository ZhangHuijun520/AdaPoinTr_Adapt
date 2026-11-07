# H1/M0两折统一CPU评分：实施、验证、P3与待授权request

日期：2026-11-07。状态：**implementation-only完成；32项人工CPU检查通过；P3通过；request保持AWAITING_EXPLICIT_USER_AUTHORIZATION。**

## 1. 实施范围

新增隔离评分入口`bcsp_p2_h1_M0_twofold_score_v1.py`。原P1 C/D评分入口及核心metric文件未改，参考、采样点集、物理单位和阈值保持原合同。

必要适配：

- 从H1两折归档、P1 C基线归档、P1 D基线归档三个精确文件中读取预测；P1中的T0不进入评分，只取M0，未重新推理。
- 每fold105例，M0/M_H1两臂，各自对应同病例/参考/归一化/目标指纹；差值明确为`M_H1_minus_M0`。
- 每病例共享Nop_D和GT_8192控制各一次：420模型行＋420控制行＝840病例行；42来源×4臂/控制＝168来源行。
- 源均值仍为每来源五缺损平均，每折21来源等权，C/D分别汇总。不用C收益掩盖D退化。
- 风险标签、新/救回病例、原始双方布尔值与缺损分层保留；共有与均无可由全病例布尔表直接核算。
- 全量保留case/source/defect/regression/coarse-dense记录，不筛失败病例。评分不执行bootstrap、p值或正式gate。

以下七个函数与母版AST完全一致：`load_prediction_arrays`、`load_prediction`、`select_metrics`、`position_shape`、`risk_labels`、`stage_geometry`、`csv_rows`。计算核心`bcsp_eval_metrics_v1.py`哈希仍为：

`af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766`。

## 2. 人工CPU验证与P3

唯一一批人工验证**32/32通过**，产物保留于`artificial_cpu_batch_v1`。内容包括两fold索引/参考路由、三归档实际reader、H1/P1完成状态、checkpoint/input来源、错误hash/目标/坐标拒绝、完整authorize、840/168输出、H1−M0方向、每折来源等权、风险阈值与转移、未定义值保留、首错停止不跳病例。

重要覆盖边界：

- 使用解析小实体生成的人工参考、人工点集和三个完整结构的人工归档，真实预测/参考数组读取为0。
- **8行人工模型/控制记录实际调用未修改的metric引擎**，验证两fold真实评分路径、GT控制零CD及扰动方向。
- 完整840行流程使用上述人工case结果模板，检查真实archive reader、210case调度、计数、来源/缺损汇总、delta/risk/CSV和完成记录；不是840行独立KD距离回归。
- 人工首case失败场景确认不进入第二case，没有真实任务失败或自动重试。
- 全部新代码经过静态审查；P3核对核心哈希、继承函数AST、完整reader路由及CPU结果。测试通过不构成真实研究评分或结果结论。

P3回执：`implementation_P3_v1.json`；CPU结果：`artificial_cpu_batch_v1/result_v1.json`。

## 3. 最终待授权评分request

文件：`local_scoring_execution_request_v1.json`。

完整SHA256：

```text
a962c57510371c880fa3510a56c2ffe4081537201797210a5769558dd07f94ab
```

只有对该完整哈希单独执行授权后，才可创建本机真实授权回执和启动唯一一次CPU评分。当前不存在真实`authorized_execution_v1`控制目录，也没有`unified_scores_v1`输出目录。人工fixture中的授权只是测试数据。

固定输出目录：

`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\cranial_bcsp_mamba_p2_20261106\H1_scoring_implementation_20261107_v1\unified_scores_v1`

输入是已核验本机H1归档＋两个P1 M0基线归档、210份冻结reference和210份V1点集。执行前仍需重验request、scorer/metric/P3、环境、证据与输入hash，确认输出/控制路径不存在。不能因为之前核验过就覆盖任何现有产物。

## 4. 固定CPU环境与预算

绑定既有`adapointr` CPU Python的解析后真实路径、大小、SHA256和成功测试中的依赖版本，`-I -B`、CUDA_VISIBLE_DEVICES为空，OMP/BLAS/MKL均2线程。不安装或升级依赖。

RSS上限8GiB、输出2GiB、2线程。wall预算14400秒（两fold840行，为原单fold420行7200秒的两倍），外部超时14430秒。仅扩大到明确的两fold工作量，未改变任何精度/风险阈值。

失败保留日志与部分产物，停止整批，不自动retry/resume、不丢弃病例。只读备份，不提取/覆盖/删除备份文件，不访问服务器、网络、WSL、Torch/GPU或checkpoint，不运行新forward、训练或BNCal，不对预测做GT配准。

## 5. 结果边界

完成评分后还需单独正式只读评分后冻结审计，核验840/168计数、完整清单、汇总与原始行一致性，然后才解读两fold Native E/J/CD、完整覆盖和新增风险，并讨论既定H1资源门。

本次没有产生真实分数，没有自动执行gate或安排新训练。全部材料都在本机，无需上传服务器。
