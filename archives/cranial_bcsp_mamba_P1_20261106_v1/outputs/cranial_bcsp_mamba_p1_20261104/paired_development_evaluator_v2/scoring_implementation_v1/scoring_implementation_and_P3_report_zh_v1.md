# P1 Fold C T0/M0 统一CPU评分：实施、人工回归与P3

日期：2026-11-06。状态：实现完成、42/42人工CPU测试通过、本机P3通过；仅生成待授权request，未计算任何真实病例分数。

## 实现范围

新增隔离文件bcsp_p1_pair_score_v1.py和test_p1_score_contract_v1.py。旧评分器及metric引擎保持不变。指标引擎SHA256仍为af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766。现有105例参考、V1点集、预测及坐标合同未修改。

新增入口支持P1 T0/M0身份、215成员归档、210条调用前claim、210条几何摘要、四类RNG不变证据，以及7固定病例/臂共14份可选coarse数组。逐预测核验大小/哈希和8192×3有限float32；coarse为256×3。不接受多余GT数组、缺失/重复病例或未声明coarse。

每例评分T0、M0、Nop_D、GT8192共4行：模型210行＋共享控制210行，总420行；每来源5缺损平均，21来源×4臂=84来源行。两臂共用同一V1输入，不重复Nop_D控制。

## 数值与科学合同

所有点集按原D-only归一化恢复世界mm；不对齐、不平移、不ICP。面积加权E_G→prediction P95仍为唯一效能主终点。沿用J P95、J Cover@2mm、E覆盖、共同GT8192双向欧氏均值半和CD-L1、pred→固定A2 P95和>2/20mm离群比例。20mm使用严格大于号，不修改冻结的距离引擎。A2依然是离散参考，不能宣称精确连续表面距离。

质心与回转半径使用同一冻结GT8192表面样本；placement_tail为质心偏移>20mm，compact_distribution为回转半径比<0.9，severe_geometry为native E P95>20mm或J覆盖@2mm=0。边界与零覆盖均有回归。多个标签可重叠，输出全部105例新增/救回及每缺损计数；非临床灾难标签。

pose协方差用population N。dense和GT均8192点，故回转半径比与P0用N−1的比值完全一致；人工回归已核对。coarse256与dense8192保留不同点预算，不把其比例当作等点数比较。回转半径比只作描述，不能简单把越大判为越好。

利用已保存coarse/dense质心、回转半径、bbox、协方差谱及offset均值/能量，恢复世界mm的诊断摘要；记录方差分解交叉项。14份保存coarse核对其质心/回转半径，全部dense核对摘要；不新增forward。这是代数分解，不等同于偏移的因果归因。

完整病例、来源配对差、缺损分层与全量回退排序均保留。M0−T0为差值，距离下降/覆盖上升为改善。空区域或非有限配对显式标记、不丢病例；畸形预测使整批失败。单折单seed不运行bootstrap/p值或两折合并gate。C止损规则保持原计划，在评分正式冻结后再解读；不自动启动D。

## 42项人工CPU验证与P3

测试覆盖：两臂105例元数据与来源隔离、215成员读取、四类RNG拒绝、缺失/重复/错权重身份拒绝、NPZ形状/dtype/finite及可选coarse集合、共享GT哈希、面积加权P95、E/J语义、mm恢复、未平方CD-L1、来源等权和差值方向、非有限配对保留、不消费bootstrap/RNG、所有病例与类型分层、单向授权及反向绑定拒绝、精确风险阈值、coarse/dense分解和摘要错配拒绝。

另用人工phantom及真实冻结metric引擎走完整105例run_scoring路径，生成420病例行、84来源行、105模型配对和风险表。测试总耗时51.264秒，数据均为人工fixture；未读取真实预测/参考数组，没有科研结果。原始日志与完整fixture保留在cpu_contract_v1。

P3核对源码/测试/结果/stdout哈希、实际病例索引的元数据兼容性，流式重验105参考文件和105 V1点集身份而不解码数组；核验人工完整汇总及固定指标引擎。详见local_P3_v1.json。没有Torch、GPU、服务器调用或真实评分。

## 最终待授权request

文件：local_scoring_execution_request_v1.json

完整SHA256：`749de9cffe7aaba667108347f93ad86bf7cea447c4e97f58e60897122048f897`

状态：AWAITING_EXPLICIT_USER_AUTHORIZATION。输入为已下载并全量核验的210份预测归档及三个侧车、固定105参考/输入；输出为本项目全新paired_scores_v1。CPU环境固定E:\RelocatedData\zhj\.conda\envs\adapointr\python.exe，numpy1.26.4/scipy1.13.1/psutil5.9.0，-I -B，CUDA_VISIBLE_DEVICES空，2线程。

预算沿用准备协议：7200秒、RSS8GiB、输出2GiB；执行器外层超时7205秒。唯一一次执行，先写独占claim；失败停止并保留部分结果，不自动修复/重试/resume。源文件、request及备份归档不覆盖、不删除。

尚未材料化授权回执、启动真实评分或创建真实结果目录。本机评分不需要上传或操作服务器。下一步单独明确授权本request完整SHA256后，才可创建授权回执并启动唯一一次CPU评分；完成后另做正式只读评分冻结审计，再解读科研结果。
