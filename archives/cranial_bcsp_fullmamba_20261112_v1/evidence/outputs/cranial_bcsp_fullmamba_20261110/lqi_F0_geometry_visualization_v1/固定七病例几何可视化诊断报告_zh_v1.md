# LQI／F0：固定七病例几何可视化诊断报告 v1

日期：2026-11-11。状态：**限定可视化完成；复用已有预测，未训练、未调参、未运行forward或重新评分。**

## 1. 核心发现

在这七个固定病例中，新增退化至少包括两类：一类在最终coarse出口已经存在明显整体空间偏差，另一类点云位于目标包围区域内但范围收缩、接口缺覆盖。两个明显改善例也在coarse布局上出现恢复，随后dense输出继续改善。后续假设应关注coarse位置与范围的可靠性，不能只凭整体均值或质心偏移判断完整骨块是否补全。

本次解码、D-only反归一化和绘图坐标核验均通过：同一病例两臂使用同一中心／尺度，world-mm坐标与冻结评分的coarse／dense质心一致。**在本轮核验覆盖范围内，图中的偏移是已有预测本身的偏移，没有发现本次可视化反归一化或配对误用。** 这不等价于对所有上游医学影像坐标作新的独立认证。

## 2. 查看入口与图示约定

[打开七病例总览及每例同步旋转3D](E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/outputs/cranial_bcsp_fullmamba_20261110/lqi_F0_geometry_visualization_v1/index_v2.html)

- 灰色：观测输入D；绿色：缺失骨块GT；蓝色：F0输出；橙色：LQI输出；紫色：冻结GT接口J参考面中心。
- 每例一张全局图：三行XY／XZ／YZ正交投影、四列F0 coarse／dense、LQI coarse／dense；每行统一世界坐标范围，包含全部原始点。全局图统一配色图例中的J主要在接口图和3D中展示。
- 每例一张接口近景：同样三投影，两列F0／LQI；显示范围固定为GT点云bbox外扩5mm。该裁剪仅作用于显示，未删除、重采样或过滤任何点，完整云仍在全局图及3D页面。
- 每例一个自包含3D HTML，提供相同初始相机、相机同步及global／target ROI切换；图例可分别开关coarse、dense、D、GT和J。没有外部脚本依赖，不需要服务器。
- J使用已有world-mm体素参考面中心，不是新拟合网格。二维投影重叠不证明三维表面贴合；ROI内点数也不是覆盖率或临床接口合格指标。

本轮7个固定病例：五个新增严重病例＋两个此前已固定的D折frontoorbital明显改善例。它们属于事后诊断选择，不能替代完整210例的性能结论。

## 3. 逐病例结论

| 病例 | E_P95：F0→LQI（mm） | LQI coarse→dense质心偏移（mm） | LQI dense半径比 | 图示支持的解释 |

|---|---:|---:|---:|---|
| C/train__012__parietotemporal | 5.21→73.59 | 91.74→92.77 | 0.417 | coarse已发生大幅定位偏差并紧缩；dense保留该错误布局 |
| C/train__013__frontoorbital | 4.80→18.54 | 28.30→26.84 | 0.795 | coarse整体位置失准；dense仍错位并缺少接口支持 |
| C/train__038__random_1 | 18.49→25.06 | 24.01→23.41 | 0.671 | 位置与范围混合退化；dense聚集在GT的一部分 |
| C/train__041__frontoorbital | 16.15→30.96 | 58.41→49.65 | 0.857 | F0已有位置偏差，LQI在coarse和dense均进一步偏离 |
| D/train__060__bilateral | 17.93→21.64 | 16.05→15.70 | 0.536 | 整体范围／形状覆盖不足；质心更近但未覆盖外围及接口 |
| D/train__008__frontoorbital | 77.21→6.69 | 33.42→20.22 | 0.938 | F0 coarse完全偏离；LQI coarse回到缺损附近，dense进一步改善 |
| D/train__052__frontoorbital | 66.34→4.42 | 17.70→13.90 | 0.921 | LQI coarse与dense均较F0恢复了位置和范围，但仍非完美覆盖 |

### 3.1 C／012 parietotemporal：大偏移在coarse出口已存在

LQI coarse质心偏移91.74mm，dense92.77mm；两者在固定GT ROI内均为0点。全局三投影显示LQI输出形成偏离GT骨片的紧缩点团，dense未将其搬回正确区域。冻结结果还显示全部dense点距A2参考超过20mm。这里的失败不是仅凭近景“看不到点”推断，全局图保留了全部点并直接显示其位置。

F0 coarse同样存在32.15mm质心偏差，但dense减至16.10mm；这也表明coarse质心偏移并非dense性能的充分统计量，仍需结合云形状和参考覆盖。

[C012全局coarse／dense对照](E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/outputs/cranial_bcsp_fullmamba_20261110/lqi_F0_geometry_visualization_v1/figures/C__train__012__parietotemporal_global.png)

### 3.2 C／013与C／041 frontoorbital：coarse错位伴接口失配

C013的F0 dense接口J覆盖63.68%，LQI降至0；LQI coarse／dense质心偏移28.30／26.84mm，大量点落在GT区域之外。C041两臂本来均存在明显偏移，LQI coarse58.41mm、dense49.65mm，较F0进一步回退，J覆盖由2.69%降为0。两例都不能仅凭dense局部外观解释成单独的切壁细节缺失。

### 3.3 C／038 random_1：混合位置与范围退化

两模型大部分点仍在GT bbox+5mm内，但LQI点云更集中于GT的一部分；coarse／dense半径比分别0.693／0.671，质心偏移24.01／23.41mm。接口J覆盖由25.56%降至22.07%。ROI内点多不等于覆盖充分，这例不能简单归为“完全跑到了错误位置”，也不能只归为接口局部误差。

### 3.4 D／060 bilateral：更靠近质心，不代表形状覆盖更好

LQI 256个coarse和8192个dense点全部位于固定ROI内；dense质心偏移由F0的19.38降到15.70mm，但dense半径比由0.711降至0.536，J覆盖由25.60%降至1.55%。接口近景显示外围GT／J仍有明显空缺，点团偏聚于内部的一部分。这与范围收缩／形状覆盖不足一致；冻结远端>20mm比例为0，不支持把它解释为远端离群主导。

[D060接口近景](E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/outputs/cranial_bcsp_fullmamba_20261110/lqi_F0_geometry_visualization_v1/figures/D__train__060__bilateral_interface_v2.png)

### 3.5 D／008与D／052 frontoorbital：改善也体现在coarse布局

两个F0的coarse和dense均完全位于固定GT ROI之外；LQI coarse／dense进入缺损附近。D008 coarse质心偏移89.25→33.42mm，dense96.71→20.22mm；D052 coarse79.42→17.70mm，dense79.14→13.90mm。J覆盖分别由0提高到54.57%和61.80%。

它们说明LQI训练后的整体布局有可能恢复，dense也可在coarse基础上进一步改善；仍有接口缺口和分布偏差，不能把“明显改善”写成完整修复或临床吻合。

## 4. ROI内点数：仅解释近景裁剪

| 病例 | F0 Q／256 | LQI Q／256 | F0 P／8192 | LQI P／8192 |

|---|---:|---:|---:|---:|
| C/train__012__parietotemporal | 209 | 0 | 8163 | 0 |
| C/train__013__frontoorbital | 236 | 83 | 7841 | 2552 |
| C/train__038__random_1 | 239 | 237 | 7930 | 7815 |
| C/train__041__frontoorbital | 110 | 37 | 5169 | 2108 |
| D/train__060__bilateral | 256 | 256 | 8191 | 8192 |
| D/train__008__frontoorbital | 0 | 118 | 0 | 6472 |
| D/train__052__frontoorbital | 0 | 225 | 0 | 7707 |

这些计数不参与正式评分、不新增gate或阈值。D060所有LQI点在ROI内但覆盖更差、C012所有LQI点在ROI外，正好展示了此计数的能力边界。

## 5. 机制解释的边界

可直接确认的是：多个失败病例在**最终coarse出口**已经失去合适位置／范围，dense没有充分修复；部分改善病例的coarse布局也更好。

不能直接确认的是：错误最早产生于encoder、learned query头、输入proxy取点、实际局部memory邻域还是Mamba状态传播。本轮没有这些更早阶段的完整张量，不可用输入点的邻近关系冒充模型实际memory邻域。

LQI条件序列位于同一次前向的coarse生成之后。两套训练后模型的coarse不同，并不表示decoder在推理时回写了上游coarse；端到端训练会改变共有模块权重及梯度路径。当前是两模型训练结果的空间对照，不是对某个算子的反事实因果证明。

这些病例的观察不能推翻或替代已冻结的210例统计：D折平均收益仍存在，C折覆盖退化和新增严重失败也必须保留。对选定7例作诊断不构成新的总体性能估计。

## 6. 后续科研方向建议

本轮证据把优先级指向：**coarse空间位置的失稳与coarse分布范围不足需要分别建模、分别验收**。仅追求质心更近会漏掉D060类覆盖失败；仅追求平均误差下降会掩盖C012类灾难性错位。

下一步可先结合已冻结的计算图、既有decoder-only诊断与LQI公式，起草一个位置／范围可靠性的最小假设，明确它与此前H1／H2已失败方案的差别，以及新发严重病例和原正常病例如何共同验收。当前证据尚不足以指定具体新公式；本轮不自动追加训练、调参或GPU instrumentation。

## 7. 输出与质量核对

- 推荐入口：`index_v2.html`；14张最终PNG（7张全局＋7张接口v2）、7个自包含交互HTML、两张七例汇总预览。
- 全部点数保持D8192、GT8192、每臂Q256／P8192，全部点原样参与全局／交互显示，无配准或重采样。
- 预测成员和本机点集／参考bank均核验冻结大小／SHA256，GT数组摘要及world坐标质心与原评分匹配。
- 已目视检查全部7例全局和接口图的汇总预览，并检查C012全局、D060接口大图；最终图片及HTML文件哈希、PNG完整性和本地页面链接通过检查。
- 初版接口图图例／脚注重叠且紫色参考点过密，保留初版并仅作一次展示层修订：降低J标记透明度／大小、调整图例和脚注，不改变任何点、范围或统计。推荐使用接口v2及`index_v2.html`。
- 交互HTML的结构、内联脚本、数据量与链接已检查，未在实际浏览器逐页点击验证相机同步。用户可用本机浏览器打开。
- `visualization_result_v2.json`记录每例源绑定、所有冻结统计、显示ROI与内点数；`delivery_QA_v1.json`记录交付检查。
- 本轮服务器操作、新forward、训练、重新评分、参数扫描、配准、重采样和GPU调用均为0。
