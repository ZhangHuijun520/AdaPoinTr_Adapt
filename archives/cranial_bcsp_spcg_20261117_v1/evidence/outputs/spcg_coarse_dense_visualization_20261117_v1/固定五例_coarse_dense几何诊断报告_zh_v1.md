# SPCG：5例固定退化与改善病例的 coarse／dense 几何诊断

日期：2026-11-17。本次只复用已有数组：5例×3模型，共15份预测、30个coarse/dense点集。没有新forward、训练、checkpoint加载、配准或调参。

## 1. 病例范围与展示合同

依据既定规则：G2相对G1新增严重病例，按病例ΔE从大到小、并列case_id取前3；改善对照每折取G2不严重且ΔE最小的1例。选例在读取选中预测数组之前写入 frozen_case_scope_v1.json。本次选例是事后解释，不是新的独立确认样本。

|折|病例|用途|dense ΔE：G2−G1/mm|
|---|---|---|---:|
|C|train__051__random_1|新增严重|+78.9967|
|C|train__072__random_1|新增严重|+66.5975|
|D|train__008__random_2|新增严重|+30.2439|
|C|train__012__parietotemporal|改善对照，非正常保证|-67.0515|
|D|train__046__parietotemporal|改善对照，非正常保证|-9.6832|

每例生成4张图：XY、XZ、YZ全局投影，以及XY局部放大，共20张。每张图按G0/G1/G2分行，coarse256/dense8192分列。相同病例全部模型/阶段共用等比例world-mm全局坐标范围，包含输入、GT及全部预测离群点。没有模型间配准或删除离群点。

局部框为GT8192包围盒外扩10mm，仅用于显示，不能当作可部署的输入定位器。局部图会裁剪显示范围，同时报告落在3D框外的预测点数；全局图保留所有点。颜色是预测点到A2离散参考的最近距离，40mm以上颜色饱和，但统计不截断。灰色为输入，青色GT，紫色为J参考面中心；投影重合不能证明三维接触。

## 2. G2主要阶段数值

质心偏差与E P95单位mm；反向离群比例为预测→A2距离>20mm。E/J支持按既定A1面积权重计算。

|病例|coarse质心偏差|dense质心偏差|coarse E95|dense E95|coarse→dense质心移动|dense反向离群|
|---|---:|---:|---:|---:|---:|---:|
|train__051__random_1|97.552|97.699|96.870|88.555|2.030|99.37%|
|train__072__random_1|89.779|90.631|80.656|72.455|1.956|100.00%|
|train__008__random_2|23.879|22.314|46.650|35.557|2.001|0.00%|
|train__012__parietotemporal|13.333|12.501|10.134|4.590|0.856|0.06%|
|train__046__parietotemporal|29.368|26.672|7.890|4.575|2.774|32.42%|

## 3. 三个新增严重病例

### C / train__051__random_1

G2 coarse质心偏差97.552mm，dense为97.699mm；反向>20mm比例由98.83%变为99.37%，J Cover@2mm两阶段均为0。全局三视图显示预测落在错误空间区域，局部细节不能解释如此大的失配。coarse到dense质心只移动2.030mm，子点相对本模型coarse中心的RMS为7.709mm。对应G1 dense质心偏差6.433mm、E95=9.559mm。大偏移在可观察coarse节点已经存在，dense主要延续它。

### C / train__072__random_1

G2 coarse质心偏差89.779mm，dense为90.631mm；两个阶段的预测点全部距A2超过20mm，J Cover@2mm均为0。coarse半径比0.9994几乎等于1，位置仍然完全不对，直接说明尺度矩正确不能替代位置与表面覆盖。dense质心仅移动1.956mm，不能挽回近90mm级偏移。此例G0也严重（dense质心62.185mm、E95=41.778mm），所以“新增严重”是相对G1而言，不能称为只有G2失败。

### D / train__008__random_2

G2 coarse/dense质心偏差为23.879/22.314mm，半径比0.5924/0.5808，E95为46.650/35.557mm，J95为55.192/44.535mm。两个阶段反向>20mm离群比例均为0，但图中预测集中在目标的一部分区域，远端目标没有得到覆盖。这是范围收缩、分布偏置与目标漏覆盖，不能把“没有远端离群”解释成形状正确。相对G1的E95回退30.244mm也不是由dense从一个正确coarse突然偏离而出现。

**这3例的共同观察：主要失配已在保存的coarse节点出现，dense没有纠正。** dense的E/J支持距离有所下降，不能直接称为生成机制修复：点数从256增至8192，本来就会影响离散覆盖。这里没有证据表明这3例主要属于“正确coarse经dense变成大偏移”的模式。也不能由这3个事后极端病例推断整个210例队列都相同。

## 4. 两个改善对照

### C / train__012__parietotemporal

G1在coarse阶段已偏位83.851mm，dense为84.418mm，所有点距目标A2超过20mm。G2 coarse偏差13.333mm、dense12.501mm，dense E95由G1的71.642降为4.590mm，J95由75.721降为7.643mm。收益也已经出现在coarse层，dense进一步提供密集覆盖。它说明当前局部方案能够在个别病例恢复位置和形状支持，但与退化病例一起看，表现具有明显病例依赖，不能宣布稳定定位问题已解决。

### D / train__046__parietotemporal

G2相对G1的dense E95由14.258降到4.575mm，J95由16.690降到4.522mm，J Cover@2mm由5.92%提高到54.82%。然而G2 dense质心仍偏26.672mm，半径比1.383，反向>20mm离群达32.42%；coarse已有40.23%离群。它是“目标支持改善但预测仍明显多余/偏位”的对照，不是正常病例。G0的反向离群仅2.55%、质心13.806mm，因此按E指标选出的改善样本也不能被包装成整体几何最优。

## 5. 归因边界

1. 本次支持将关注点前移到coarse空间生成的可靠性，而非首先归咎于dense残差放大。但保存的coarse是现有可观察节点，不证明错误在计算图中首次产生的位置。
2. 本次所有模型使用同一冻结病例和D-only归一化/反归一化合同，读取的文件/成员哈希均一致。三臂同病例结果明显不同，不支持把统一坐标变换错误作为唯一解释；这并不代替所有上游轴向/空间合同的独立证明。
3. coarse与dense点数不同。质心位移、范围与离群比例可描述阶段变化；E/J覆盖变化含点预算影响，不是同预算因果消融。
4. dense按现有每coarse32子点布局检查相对位移；同一槽位在不同模型之间没有保证一致的解剖含义，不能跨模型逐槽硬配对。
5. 未保存实际Memory、probe/索引与局部摘要，本次不能把失败唯一归因于探针位置、近邻选择或特征质量，也未执行同权重反事实。
6. D折G1/G2同设备，G0_D跨设备仅供参考；5例是按结果选出的解释样本，不代表总体失败率。

## 6. 交付与下一步

已保存20张PNG、总览、可离线打开的index.html、逐病例/模型/阶段指标、选例范围、源文件及15份预测成员的SHA绑定和产物清单。所选dense的E/J、质心和反向离群指标已与正式冻结评分核对一致；原评分、预测和备份未修改。

建议下一步先对本次图表、选例和数值做正式只读诊断后冻结审计，再与已冻结全队列评分综合决定收束当前SPCG候选。不要直接据此添加dense补偿、扫描邻域大小或追加训练；本次没有授权或执行这些操作。运行时一致性核验不代替另行正式冻结审计。

## 7. 三臂两阶段完整简表

每病例每模型均列出，避免只报告G2或最显著一张投影。

|病例|模型|coarse质心/mm|dense质心/mm|coarse E95/mm|dense E95/mm|dense J95/mm|dense J2/%|dense离群20/%|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|train__051__random_1|G0|8.708|8.225|10.701|5.060|9.601|51.19|0.00|
|train__051__random_1|G1|6.550|6.433|24.876|9.559|18.491|29.78|0.00|
|train__051__random_1|G2|97.552|97.699|96.870|88.555|91.225|0.00|99.37|
|train__072__random_1|G0|69.077|62.185|54.775|41.778|44.405|0.00|94.68|
|train__072__random_1|G1|22.607|18.359|13.102|5.857|5.517|59.32|2.84|
|train__072__random_1|G2|89.779|90.631|80.656|72.455|75.308|0.00|100.00|
|train__008__random_2|G0|13.458|13.315|15.256|8.148|12.568|2.00|0.00|
|train__008__random_2|G1|11.544|11.215|25.983|5.313|8.601|8.10|0.00|
|train__008__random_2|G2|23.879|22.314|46.650|35.557|44.535|5.01|0.00|
|train__012__parietotemporal|G0|27.360|22.478|20.542|12.955|18.504|33.61|3.05|
|train__012__parietotemporal|G1|83.851|84.418|81.079|71.642|75.721|0.00|100.00|
|train__012__parietotemporal|G2|13.333|12.501|10.134|4.590|7.643|50.40|0.06|
|train__046__parietotemporal|G0|19.613|13.806|10.968|6.148|5.773|58.06|2.55|
|train__046__parietotemporal|G1|43.223|40.335|23.593|14.258|16.690|5.92|57.36|
|train__046__parietotemporal|G2|29.368|26.672|7.890|4.575|4.522|54.82|32.42|

## 8. 图表入口

### train__051__random_1

[train__051__random_1_XY_global.png](train__051__random_1_XY_global.png)
[train__051__random_1_XZ_global.png](train__051__random_1_XZ_global.png)
[train__051__random_1_YZ_global.png](train__051__random_1_YZ_global.png)
[train__051__random_1_XY_ROI.png](train__051__random_1_XY_ROI.png)

### train__072__random_1

[train__072__random_1_XY_global.png](train__072__random_1_XY_global.png)
[train__072__random_1_XZ_global.png](train__072__random_1_XZ_global.png)
[train__072__random_1_YZ_global.png](train__072__random_1_YZ_global.png)
[train__072__random_1_XY_ROI.png](train__072__random_1_XY_ROI.png)

### train__008__random_2

[train__008__random_2_XY_global.png](train__008__random_2_XY_global.png)
[train__008__random_2_XZ_global.png](train__008__random_2_XZ_global.png)
[train__008__random_2_YZ_global.png](train__008__random_2_YZ_global.png)
[train__008__random_2_XY_ROI.png](train__008__random_2_XY_ROI.png)

### train__012__parietotemporal

[train__012__parietotemporal_XY_global.png](train__012__parietotemporal_XY_global.png)
[train__012__parietotemporal_XZ_global.png](train__012__parietotemporal_XZ_global.png)
[train__012__parietotemporal_YZ_global.png](train__012__parietotemporal_YZ_global.png)
[train__012__parietotemporal_XY_ROI.png](train__012__parietotemporal_XY_ROI.png)

### train__046__parietotemporal

[train__046__parietotemporal_XY_global.png](train__046__parietotemporal_XY_global.png)
[train__046__parietotemporal_XZ_global.png](train__046__parietotemporal_XZ_global.png)
[train__046__parietotemporal_YZ_global.png](train__046__parietotemporal_YZ_global.png)
[train__046__parietotemporal_XY_ROI.png](train__046__parietotemporal_XY_ROI.png)
