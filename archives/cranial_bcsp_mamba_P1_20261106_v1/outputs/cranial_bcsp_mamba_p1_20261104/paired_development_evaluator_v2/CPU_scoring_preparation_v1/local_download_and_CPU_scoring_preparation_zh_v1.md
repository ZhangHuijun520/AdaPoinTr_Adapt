# P1 Fold C 配对预测：本机下载核验与统一CPU评分准备

四个下载文件已落地到 `E:\ResearchBackups\AdaPoinTr\BCSP_MAMBA_P1\2026-11-06_FoldC_paired_development_eval`，包括预测压缩包及三个校验侧车。所有文件大小/哈希、215个归档成员、210份预测及14份coarse数组均核验通过；归档元数据与正式服务器审计字节一致。备份目录含local_verification_receipt_v1.json。未删除服务器文件。

本轮额外核齐固定105例参考bank和105份原始V1点集，重新计算全部大小/哈希，与本轮预测输入、D-only归一化、目标数组指纹一致。未解码真实参考或输入数组、未计算科研分数、未重建参考。病例索引见P1_score_case_index_v1.json。

## 统一评分合同

T0/M0各105份native预测，以原D-only中心/尺度恢复mm，不配准。唯一主终点为A1面积加权E_G→prediction P95：先每来源5缺损均值，再21来源等权。保留病例/来源配对差和5种缺损分层，M0−T0为差值方向。完整报告J P95、J覆盖@2mm、E覆盖、共同GT8192 CD-L1、pred→固定A2 P95和>2/20mm离群比例。

风险标签沿用确认计划：质心偏移>20mm、回转半径比<0.9、native E P95>20mm或J覆盖@2mm为0。质心及尺度参照沿用P0的GT8192表面样本，不能替换成面积加权中心后仍叫同一标签。利用已保存coarse/dense摘要，不额外forward，不用GT平移或ICP修正。所有异常、空区域及回退病例显式保留，不能结果筛例。

两模型共用完全相同V1输入，CPU控制只需Nop_D和GT8192各105例：模型210行＋控制210行，共420病例评分行、84来源行。不重复计算两个相同Nop_D并称为不同采样控制。单折单seed仅描述性统计，不计算bootstrap/p值或两折合并gate。C止损规则保持原计划，评分后正式冻结审计再解读，不自动启动D。

## 当前适配缺口

旧评分器硬编码采样臂名称、213成员归档、旧RNG字段及prediction-only NPZ；缺少本轮已定义的20mm离群与位置/紧凑度/严重几何标签。不能改名后直接运行，也不能伪称已有可执行request。现有metric引擎及固定参考保持不变。

本轮仅冻结评分准备草案（DRAFT_NOT_EXECUTABLE_REQUIRES_P1_SCORE_ADAPTER），没有修改旧评分代码、运行CPU契约测试或创建最终execution request。下一步限定新增P1评分入口与针对性人工CPU测试，覆盖实际215成员/14coarse/4类RNG、身份与坐标、GT-only控制及原阈值；P3通过后生成绑定最终哈希的待授权request，再单独授权评分。
