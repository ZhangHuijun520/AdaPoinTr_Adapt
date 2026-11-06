# P1 T0／M0：冻结 Fold C／D 综合复盘与退化几何诊断

日期：2026-11-06。结论限定于既定seed0、两折、相同3900步训练合同及原生未配准预测。复盘保留全部病例；未修改采样、数据、模型、训练参数或正式评分。

## 1. 完成范围与证据来源

C、D两折正式评分后冻结审计均已通过，本轮再次核对其全部结果文件哈希。每折105病例（21来源×5缺损）、两模型及两共享控制，分别420行评分。420份模型预测已经冻结；本轮先汇总已有记录，再于读取预测数组前冻结14病例解释性清单：两折全部10个M0新增严重风险病例＋各折一个最大E改善病例＋各折一个双臂均不触发风险、E变化最小的对照病例。并列时按病例名排序。

仅对这14例的28份既有预测读取数组，核验其冻结哈希，并复查A1全量E/J面中心覆盖、面积加权P95以及预测至A2的>20mm离群点。复查结果与既有分数一致，未替换正式评分。图使用共同世界毫米坐标、共同范围，不裁掉远端点、不平移或刚体配准；参考点仅在绘图时按固定步长稀疏显示，计算仍使用全量。未使用原始NRRD/STL、checkpoint、服务器、GPU或新forward。

14例按结果有目的选取，适合解释机制，不构成无偏性能样本。总体结论始终来自未删病例的冻结统计。每折一个训练seed，训练来源有交叉，不能把两折当完全独立重复。本轮不计算合并gate、显著性、bootstrap或p值。

## 2. 两折性能方向不一致，M0尚不能替代T0

每来源五种缺损先平均，再21来源等权。差值为M0−T0，距离负值／覆盖正值为改善；百分比指标的差值为百分点。

| 指标 | 折 | T0 | M0 | 差值 |
| --- | --- | ---: | ---: | ---: |
| E P95（mm） | C | 8.4496 | 6.9352 | -1.5144 |
| E P95（mm） | D | 7.4497 | 7.8119 | +0.3622 |
| CD-L1（mm） | C | 4.3077 | 3.8854 | -0.4223 |
| CD-L1（mm） | D | 3.4843 | 4.1944 | +0.7101 |
| J Cover@2mm（%） | C | 47.0093 | 50.2928 | +3.2835 |
| J Cover@2mm（%） | D | 45.9144 | 48.1309 | +2.2164 |
| >20mm 离群比例（%） | C | 4.8219 | 2.4873 | -2.3346 |
| >20mm 离群比例（%） | D | 2.5438 | 3.9880 | +1.4441 |

C主指标改善1.514mm，D回退0.362mm；C的CD改善，D的CD回退0.710mm。两折J覆盖均提高，但与未知表面覆盖、反向离群和CD的变化并不一致。因此当前证据支持“有条件收益＋明显异质性”，不支持稳定整体优势。

M0严重几何标签：C从7降到4（新增3、挽回6），D从5增到10（新增7、挽回2）。这些标签允许重叠且不是临床诊断。不存在“平均好一点便可忽略少量严重退化”的依据。

| 缺损类型 | C ΔE P95 | D ΔE P95 | C ΔCD | D ΔCD |
| --- | ---: | ---: | ---: | ---: |
| bilateral | -1.678 | -0.647 | -0.393 | +0.084 |
| frontoorbital | +3.863 | +1.835 | +3.334 | +2.381 |
| parietotemporal | -5.285 | -0.628 | -3.768 | -0.085 |
| random_1 | -0.486 | -0.638 | +0.224 | +0.543 |
| random_2 | -3.986 | +1.889 | -1.508 | +0.627 |

frontoorbital在两折E/CD均退化，是最值得优先检查的共同形态；parietotemporal两折均改善，但D改善很小且仍有个别严重退化。random_2在C改善、D退化，不能把C的有利分层直接推广到D。类型分层不用于筛掉病例或改动既定数据范围。

## 3. 全病例误差模式：位置、覆盖和离群不能混为一谈

C共有37/105例E P95回退，其中13例质心偏差未变差、24例CD同时变差、9例>20mm离群比例增加。D共有51/105例E P95回退，其中15例质心偏差未变差、48例CD同时变差、26例>20mm离群比例增加。以上条件可重叠，不能相加。

这些计数显示：质心改善不保证形状覆盖改善；离群增加与部分回退同时存在，但不是所有回退的必要条件。D有10个E回退病例的J覆盖反而提高；C也有8个，说明只优化接口指标可能掩盖未知骨块表面退化。这里是方向共现，不是因果或统计显著性结论。

## 4. 新增严重风险病例逐例复查

离群点列为距固定A2表面参考>20mm的预测点数量，分母均8192。E覆盖为面积加权Cover@2mm，质心单位mm。

| 折／病例 | E P95：T0→M0 | E覆盖：T0→M0 | >20mm点数：T0→M0 | 质心偏差：T0→M0 |
| --- | ---: | ---: | ---: | ---: |
| C/053__frontoorbital | 6.55→37.35 | 75.9→2.4% | 1096→5684 | 23.6→50.1 |
| C/072__random_1 | 12.96→29.85 | 44.8→7.5% | 1554→2674 | 28.6→37.8 |
| C/105__parietotemporal | 8.53→32.34 | 75.5→33.9% | 165→1570 | 16.9→37.4 |
| D/008__random_2 | 10.08→33.70 | 48.1→42.9% | 0→0 | 18.1→19.6 |
| D/022__random_1 | 5.38→16.81 | 56.2→0.0% | 3→508 | 7.5→21.9 |
| D/046__frontoorbital | 8.99→21.74 | 69.9→3.0% | 7→3646 | 15.7→35.1 |
| D/060__bilateral | 18.45→20.54 | 28.8→35.1% | 0→0 | 12.5→15.9 |
| D/079__frontoorbital | 18.58→51.21 | 38.0→0.0% | 2→8192 | 21.9→64.0 |
| D/087__frontoorbital | 6.30→24.40 | 69.1→1.9% | 156→4971 | 17.9→37.1 |
| D/087__parietotemporal | 6.60→26.73 | 61.5→6.2% | 16→3766 | 17.0→53.7 |

### 4.1 整体错位并收缩：D/079/frontoorbital

M0 E P95=51.208mm，E/J覆盖均为0，8192/8192预测点距A2超过20mm。这是整片骨块落到错误区域的模式，不能解释为少量可删除的飞点。coarse质心偏差已达66.303mm、半径比0.428；dense分别为64.018mm、0.467。明显位置和尺度问题在coarse出口已可见，dense阶段没有纠正。

[查看同尺度三投影](figures/D__train__079__frontoorbital.png)。灰色GT与红色M0预测簇在三个投影均明显分离，并伴随收缩。这里能说“问题最迟在coarse已出现”，不能仅凭出口统计进一步归因到encoder、query选择或某一loss。

### 4.2 无极端离群仍会严重漏覆盖：D/008/random_2

M0的>20mm离群点为0，但E P95由10.076升至33.697mm、CD由3.251升至6.401mm。coarse半径比由T0的0.785降至M0的0.612，dense为0.789→0.631；coarse和dense均缩在目标骨片的一部分区域。M0不是大量点飞到远处，而是大片目标表面没有预测支持。

[查看覆盖诊断](figures/D__train__008__random_2.png)。漏覆盖区并非只沿接口的一条细带，三投影可见整个表面部分区域缺失。质心误差18.071→19.581mm的变化不足以独立描述这种范围收缩。预测→GT方向距离可以较好而GT→预测尾部距离很差，必须保留双向和区域指标。

### 4.3 共享切壁／接口失败与整体形状失败可同时发生：D/022/random_1

M0 E P95为16.809mm，未超过20mm，但E覆盖为0且J覆盖为0，因此触发既定严重风险规则。其质心偏差7.452→21.926mm、CD3.375→12.851mm，不能仅解释为一个接口细节缺失。需连同全骨片错位和覆盖范围一起检查。

### 4.4 风险标签跨阈值不等于所有指标恶化：D/060/bilateral

M0 E P95从18.453升至20.539mm而触发标签，但E覆盖28.76%→35.06%、CD5.946→5.661mm，且两臂均无>20mm离群点。这是尾部覆盖变差与部分平均指标变好并存。标签用于提示审阅，不能替代连续指标或被简单称为“全面失效”。

### 4.5 改善和稳定对照说明失败不是统一坐标常量偏移

C/013/parietotemporal：T0→M0 E P95=44.598→3.101mm，>20mm点数6709→2；coarse质心62.428→7.888mm、dense63.589→3.485mm，改善同样在coarse阶段已有体现。D/093/parietotemporal也从T0明显错位改善为M0较好覆盖，但仍有残余位置误差。

C/026/bilateral及D/008/random_1两臂均无既定严重风险，E P95变化很小。病例间既有改善也有相反退化，且输入／目标／归一化绑定一致，目前不支持把模型差异统一归为同一个固定坐标变换错误。但本轮没有重新审计所有原始影像affine，不能声称排除了任何可能的实现问题。

## 5. 下一阶段最值得改什么

**第一优先：coarse生成的空间锚定与全骨片范围覆盖。** 极端失败和显著改善都已在coarse出口位置／尺度中出现；仅增加dense层数或在后处理中删除远端点缺乏依据。应先基于现有计算图明确learned query/coarse是否具有足够的输入空间约束，以及既有重建目标是否允许集中覆盖一部分表面。尚不能断言Mamba本身或某一模块就是根因。

**第二优先：区分全局位置与形状分布的匹配。** 079代表整片错位＋收缩，008/random_2代表无远端离群但范围不够。任何新假设需同时解释这两类，保持E/J、CD、双向距离和风险监测，避免只改善质心或单个方向的Chamfer统计。

**第三优先：局部接口建模。** 仍有价值，但当前整块错位和大范围漏覆盖已足以导致接口不吻合；不宜把全部资源先用于接口定位器、rim加权或更多采样搜索。既定完整骨组织边界、实体缺损、8k/8k和V1采样暂时保持不变。

下一步建议仅制定一个针对“输入几何锚定的coarse位置与范围约束”的最小可检验假设，列出它对上述失败／改善／稳定病例应产生的不同预期，再决定是否需要新增无更新instrumentation或模型对照。新的GT配准Oracle、多seed训练或loss变更应单独讨论，均未在本轮执行。

## 6. 复现与产物

- `frozen_CD_descriptive_review_v1.json`：两折来源统计、全部病例差值、风险及来源绑定。
- `frozen_diagnostic_selection_v1.json`：读取预测数组前冻结的14病例清单与规则。
- `diagnose_existing_predictions_v1.py`：只读既有预测诊断及绘图代码。
- `selected_case_geometry_v1.json/.csv`：28份预测的选定几何复查及面积遗漏记录。
- `selected_coarse_dense_evidence_v1.json`：对应coarse/dense已保存出口统计；部分病例只有coarse汇总，没有完整coarse张量。
- `diagnostic_input_bindings_v1.json`：两份预测归档和所读参考／点集精确绑定。
- `artifact_manifest_v1.json`：本轮代码、记录和14张图的内容哈希。

正式模型性能仍以两折原评分目录为准，本轮诊断分数不替换它们。无GT对齐、无参数搜索、无重训、无checkpoint读取、无新增forward、无服务器操作。图中X/Y/Z是冻结世界坐标轴，不新增未经验证的解剖方向命名。

### 全部诊断图

- [C/train__053__frontoorbital](figures/C__train__053__frontoorbital.png)：all_new_severe
- [C/train__072__random_1](figures/C__train__072__random_1.png)：all_new_severe
- [C/train__105__parietotemporal](figures/C__train__105__parietotemporal.png)：all_new_severe
- [C/train__013__parietotemporal](figures/C__train__013__parietotemporal.png)：maximum_E_improvement
- [C/train__026__bilateral](figures/C__train__026__bilateral.png)：risk_free_minimum_absolute_E_change
- [D/train__008__random_2](figures/D__train__008__random_2.png)：all_new_severe
- [D/train__022__random_1](figures/D__train__022__random_1.png)：all_new_severe
- [D/train__046__frontoorbital](figures/D__train__046__frontoorbital.png)：all_new_severe
- [D/train__060__bilateral](figures/D__train__060__bilateral.png)：all_new_severe
- [D/train__079__frontoorbital](figures/D__train__079__frontoorbital.png)：all_new_severe
- [D/train__087__frontoorbital](figures/D__train__087__frontoorbital.png)：all_new_severe
- [D/train__087__parietotemporal](figures/D__train__087__parietotemporal.png)：all_new_severe
- [D/train__093__parietotemporal](figures/D__train__093__parietotemporal.png)：maximum_E_improvement
- [D/train__008__random_1](figures/D__train__008__random_1.png)：risk_free_minimum_absolute_E_change
