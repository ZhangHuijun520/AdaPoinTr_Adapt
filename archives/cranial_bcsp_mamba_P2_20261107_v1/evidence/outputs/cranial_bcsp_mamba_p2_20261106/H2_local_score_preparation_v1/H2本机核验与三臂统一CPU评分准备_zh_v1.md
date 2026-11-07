# H2本机下载核验与统一CPU评分准备

2026-11-07。四文件本机核验PASS；统一评分元数据已准备，评分入口适配待单独授权。

## 本机归档可核验

用户指定目录：E:\ResearchBackups\AdaPoinTr\BCSP_MAMBA_P2_H2\2026-11-07_native_development_eval。

压缩包38096299字节、SHA256为e2b28e7243531428ec7192c522bf87fe6855e01c4196be6d38d614bcc1511180。三个sidecar自身大小/哈希及其内容均与正式审计一致。流式核验全部425个正规成员，集合/大小/哈希匹配服务器冻结记录；420个prediction数组有限FP32、8192x3，精确20个事前代表病例含coarse有限FP32、256x3。归档内420条manifest和各105条模型记录一致，四模型状态/RNG不变证据一致。本机备份文件大小/mtime核验前后不变，排除atime；未解压、改写或删除备份。

这是可继续评分的本机预测归档核验，不包括任何模型权重，不代表完整推理环境恢复验证。不会自动删除服务器文件。

## 统一评分身份与计数

已重新核验固定210份几何参考文件、210份原V1点集的字节哈希，以及既有P1 Fold C/D两份预测归档与sidecar。参考、点集、case/source/fold、D-only normalization及target_array_sha256与新H2预测身份一致，保持原metric源码SHA256 af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766。

三模型臂M0、H2_AUX、H2_COUPLE，每臂210例，两共享控制Nop_D、GT_8192每个210例：630行模型评分+420行共享控制=1050行病例评分；42来源、每来源5类缺损，模型/控制共210行来源汇总。旧M0归档内T0不进入本次模型对比，不新增推理。

主比较COUPLE-AUX；次比较COUPLE-M0、AUX-M0分别解释，不合并成一个结论。沿用来源等权E P95主指标及原E/J/CD、Cover2mm、reverse>20mm离群、严重几何等定义，报告分折/来源/病例/五缺损类型和风险新增/挽救，frontoorbital全部保留。不算bootstrap、p值或正式gate，不做筛病例、扫描参数、ICP或GT对齐后分数。

## 实际入口缺口

现有H1评分器锁定M0/M_H1两臂、H1索引以及215成员/210预测归档，不能处理H2的425成员/420预测和重复210个实际病例；其汇总固定840病例行/168来源行，不适用于新的1050/210。同时新H2 Native粗点代表病例为每折5个，H2同forward条件摘要需要兼容。不能只改标签和行数就视为实现通过。

下一步建议限定implementation-only：一个H2/M0三臂评分入口、一个人工CPU测试文件与P3，原metric计算函数和阈值保持不变。人工验证应覆盖三臂/共享控制计数、真实档案元数据合同、方向/风险转移、缺损与来源汇总、H2 summary/coarse处理和错误hash/mode/frame拒绝；不执行真实评分。通过后创建绑定最终实现哈希的待授权评分request，再等待完整哈希执行授权。

原H1评分预算14400秒/840行，本次准备草案按1050/840比例提出18000秒墙钟预算，RSS8GiB/输出2GiB/线程2不变；这只是新增CPU工作量依据，不改任何精度阈值或执行授权。最终入口P3和request须明确冻结它。

本轮没有修改评分源码、调用指标计算、模型/GPU/服务器或启动评分。没有材料化执行授权文件，也尚未创建正式评分execution request。

配套文件：local_download_verification_v1.json、H2_M0_twofold_score_case_index_candidate_v1.json、H2_M0_frozen_scoring_protocol_candidate_v1.json、scoring_compatibility_and_minimal_implementation_scope_v1.json。
