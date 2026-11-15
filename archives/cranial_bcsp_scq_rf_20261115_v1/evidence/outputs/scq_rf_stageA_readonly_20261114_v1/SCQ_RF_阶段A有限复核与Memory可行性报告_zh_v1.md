# SCQ-RF阶段A：有限计算图复核与既有Memory可行性核查

_2026-11-14｜确认正式计划v2后的限定本机核查｜未连接服务器、未加载checkpoint、未运行模型或训练_

## 1. 本轮结论

**计算图及唯一插入位置已核清；现有冻结材料不足以完成真实重查询可行性判断。** 十个拟用病例已按正式计划规则固定。已有SCQ Native归档没有保存实际Memory坐标／特征、全局z及原邻居索引；不能由Qraw／Q1／dense逆推出这些信息。旧N0-B的实际Memory来自不同LQI权重，不能替代SCQ S模型。

因此本轮不宣称重查询“有用”“无用”或“机制无差异”。下一步如继续，需要对固定十例采集同次forward的实际Memory；本次没有运行这十次forward，也没有生成执行请求或实现新采集入口。

## 2. 计划确认与边界

已记录用户确认修订计划v2并开展有限核查。计划SHA256：

`fe041d33cb16d6517ab31820599a8b750c7aee1db10580b3fe913f45618499d2`

确认记录：[plan_confirmation_v1.json](plan_confirmation_v1.json)。本轮按计划第5.1节区分“复用既有材料核查”与“单独授权新增GPU forward”；没有将计划确认解释为六run训练、真实诊断执行或RF实施授权。

本次只读取精确相关源码、冻结JSON及所选预测NPZ的数组头，保存本机报告与范围。没有读取真实D／GT点数组值，没有重新评分、bootstrap、GPU调用或服务器操作。

## 3. 有限计算图复核结果

核查五份实际相关Python源码及其哈希，作静态阅读／语法解析，不导入模型，不运行CPU契约测试。

| 位置 | 实际行为 | 对RF的要求 |
|---|---|---|
| SCQ factory编码后 | `coor`是Memory坐标，`mem`是256×384特征，`global_feature`是query生成前全局z | 必须采集这一位置的z，不能使用重建头重新汇总出的同名global_feature |
| 原SCQ输入 | `scq(coor, mem, global_feature, coarse)`；coarse来自learned query | 可在原SCQ调用的输入／输出处观察实际M、F、z、Qraw、Q1 |
| 原SCQ邻域 | `knn(8,S,Q0)`得到N0；逐token LN后在邻域mean／max | 重查询必须使用同一个native KNN及同一Memory token身份 |
| 原SCQ输出 | `Qused=Q0+delta`；模型用Qused，诊断副本被detach | RF计算必须使用带计算图的Q1，不能将已detach的诊断副本接回训练 |
| query-MLP／decoder | Q1传入MLP和`q_pos` | 新第二头插在原SCQ返回后、query-MLP之前，Q2替换同一coarse变量 |
| LQI decoder | 入口以q_pos计算self／cross KNN；同一套索引供八层使用 | 不需要每层额外重算KNN；保证索引基于最终Q2即可 |
| FC重建 | coarse坐标既参与重建条件，也与relative_xyz相加 | 不能只改最终加法或只改导出坐标 |
| 返回与损失 | 返回实际coarse；`loss_recon=loss_coarse+loss_fine` | Q2必须进入coarse输出和原损失，不能遗漏监督 |

原S已经在Q1处读取decoder Memory。RF新增的是**解码前第二次坐标校正**，不能把S描述成全网一直只使用Qraw处旧邻域。

零初始化时，delta0=0使Q1=Qraw，从头模型首个初态N1=N0。真实可行性需基于训练后S或非退化人工机制案例，而不是据零初态输出相同否定机制。

源码身份及逐项行号：[finite_compute_graph_review_v1.json](finite_compute_graph_review_v1.json)。关键源码SHA256均与冻结父证据一致：

| 源码 | SHA256 |
|---|---|
| SCQ residual | `2f3a86c5daf7ad00c01dc405b4a3b7011faae06f5766da3dcfe72d645b730404` |
| SCQ factory | `fe5f7229aa40ba2b7e599c2bea32982f6bb33cf5f1db115b222a581c1d4af1c5` |
| LQI decoder | `92a52949ec037edd13bac7bfae7395bfafad84c5ffc204e1d178ea1f68507ea8` |
| AdaPoinTr母版 | `1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4` |

## 4. 既有Memory能否复用

### 4.1 SCQ预测归档检查

重新核验本机冻结Native归档：40,571,136字节，SHA256为

`57e7c761510bd8fb0f4758a49eb38354231ba8b0893eab16513f1b478350838d`。

核对426个归档成员名，并对本次固定十例S预测的NPZ成员核验大小、哈希和数组头；没有解码点坐标值。每份均只有：

| 数组 | 形状 | dtype |
|---|---|---|
| prediction | 8192×3 | FP32 |
| coarse，即Q1 | 256×3 | FP32 |
| Qraw | 256×3 | FP32 |
| delta | 256×3 | FP32 |

原正式预测审计也明确记录`context=0`、`traces=0`。原预测入口虽保留完整instrumentation接口，但“代码支持采集”不等于“此次已采集”。不能将缺少的Memory假装成可从现有轨迹恢复。

### 4.2 旧N0-B为什么不能替代

旧N0-B七例实际Memory对应的LQI checkpoint哈希为C：`d8d819ff…5a0ddf`、D：`2afd1b45…3e5ed`；本次需用SCQ S_C：`00f1ce94…0d2f0b`、S_D：`bd8fe23f…1f636fa`。两组不同；即使输入病例相同，训练后encoder／query参数不同，也不能将旧Memory与SCQ Qraw／Q1拼接。

这些旧记录仍保留历史研究价值，但不能回答SCQ-RF的当前邻域变化。本次结论仅针对精确审阅的冻结归档及已定位N0-B材料，不声称全盘所有目录都不存在任何Memory。

机器可读检查：[saved_memory_feasibility_v1.json](saved_memory_feasibility_v1.json)。

## 5. 已固定的十例范围

五个既知反例保持不变；五个分数盲对照按正式计划中的哈希最小规则选择，不读取任何分数作选择。共C折7例、D折3例，十个不同来源；这只是可行性样本，不是重新平衡后的疗效队列。

| 角色 | Fold | 病例 |
|---|---|---|
| 既知反例 | C | `train__013__frontoorbital` |
| 既知反例 | C | `train__051__frontoorbital` |
| 既知反例 | C | `train__053__frontoorbital` |
| 既知反例 | D | `train__046__parietotemporal` |
| 既知反例 | D | `train__069__random_2` |
| 分数盲对照 | C | `train__036__bilateral` |
| 分数盲对照 | C | `train__105__frontoorbital` |
| 分数盲对照 | C | `train__076__parietotemporal` |
| 分数盲对照 | C | `train__042__random_1` |
| 分数盲对照 | D | `train__054__random_2` |

冻结清单：[fixed_ten_case_memory_scope_v1.json](fixed_ten_case_memory_scope_v1.json)。其中逐例保存既有实际服务器输入路径、大小／SHA256、D-only归一化、对应S模型、历史预测成员及哈希；当前未读取输入payload或确认服务器现状。

该JSON状态为`PROPOSED_BOUNDED_MEMORY_SCOPE_NOT_EXECUTION_REQUEST`，不是可执行请求、授权回执或GPU准入结论。

## 6. 后续真正需要的最小步骤

如继续，应只准备一个观察型采集短入口，复用原模型、provider、数据读入及运行逻辑，不实现RF第二头、不修改科研源码。建议在原SCQ模块输入／输出处采集M、F、z、Qraw、delta0、Q1及N0，用同一native KNN计算N1；这比启用所有decoder层完整轨迹更小。

必要人工CPU验证应集中检查输入／输出绑定、采集不改变返回值、十例／fold／checkpoint限制、无GT进入条件和退出后的hook清理。通过及P3后，核对当前容器与冻结资产，再生成绑定最终实现哈希的待授权request。不能复用旧420预测或N0-B请求执行十例采集。

拟定执行范围仍是十例各一次eval forward，0 loss、0 backward、0 step、0 warmup、0 BNCal，无自动重试；额外N1查询最多十次。墙钟30分钟，RSS 8 GiB、torch峰值20 GiB、SMI22,528 MiB、输出2 GiB。当前容器／GPU未在本轮核验，不能从历史身份直接材料化执行内容。

取得实际张量后才能报告N0／N1重合率、条件差异和证据不足情况。距离下降本身是KNN构造结果，不证明重查询更解剖正确；局部条件不同也不代表RF效果改善。

## 7. 本轮完成状态

- 已完成：计划确认记录、五源码有限计算图复核、既有SCQ预测数组头检查、旧Memory身份排除、十例精确范围。
- 尚未完成：SCQ S模型实际Memory采集及真实条件可区分性判断。
- 未执行：模型导入、checkpoint加载、真实输入／GT数组读取、新forward、GPU、训练、CPU契约测试、RF实施、服务器操作。
- 未创建：execution request、runtime config、launcher、授权回执。

本轮应收束为“计算图明确，既有证据不足，下一步采集范围已固定”，不能写成RF可行性通过或科研假设失败。
