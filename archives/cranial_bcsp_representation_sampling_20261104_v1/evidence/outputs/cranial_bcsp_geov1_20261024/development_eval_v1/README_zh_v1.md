# 四模型开发集配对评价：本轮交付与执行衔接

2026-10-26。状态：**READY_AWAITING_EXPLICIT_USER_EXECUTION_AUTHORIZATION**。尚未产生模型预测或模型性能比较。

## 已完成

| 项目 | 实测结果 |
|---|---|
| 最终模型身份 | Fold C／D × 输入8192／16384，共四个B0 AdaPoinTr；各3900步最终checkpoint，均已有正式训练后冻结审计 |
| 评价病例 | 各模型105例，合计420个模型－病例组合；210个不同病例、42个不同颅骨来源，每来源五种缺损 |
| 真实几何参考 | 210/210完成；A1体素边界面中心、A2固定四子面、B固定MC三角中心；模型无关，D/G原始哈希和既有接口面数／面积重新核验 |
| 参考构建预算 | 895.875秒，参考NPZ总440,030,810字节；详细环境、RSS和病例清单见reference_bank_v2/reference_manifest_v1.json |
| 最终人工CPU检查 | 几何20、推理／评分18、控制器8，共46项通过；与最终代码哈希绑定 |
| 本机P3 | local_P3_v1.json通过，明确保留CUDA、Linux符号链接动态证明和采样监测局限 |
| 服务器只读核验 | 01dt08-0身份及固定GPU一致；读取1,622,123,754字节，四个checkpoint／420个输入及相关固定资产哈希通过；GPU初始1 MiB，磁盘12,099,518,464字节可用 |
| 当前执行边界 | 服务器写入0，安装0，模型forward0，训练0，BNCal0，真实模型评分0 |

准备过程中曾修正QC共享接口面积字段映射、本机换行字节绑定及Windows人工fixture常量兼容；原失败证据保留，详见正式实现补充。未通过失败重跑模型、修改科研参数或筛选病例。

## 固定评价内容

主终点为未知原始表面`E_G→预测点`的面积加权P95，单位mm。同步报告切壁J、全G、0.5／1／2mm覆盖、逆向离群及固定GT参考CD-L1；A2／B交叉参考不替换主终点。每来源五缺损等权平均，再以source为配对单位，差值16k−8k，10000次bootstrap、seed20261024。固定Nop-D8k／16k和GT8192控制在本机评分阶段统一计算。

该比较使用固定seed0、两折开发数据，不能解释为独立测试结果、训练随机性估计、Mamba收益或临床贴合认证。

## 下一次单独授权的具体范围

1. 手动上传`bcsp_four_model_development_eval_v1.tar.gz`到服务器`/home/jovyan/`。运输包仅含推理入口和420输入身份清单两个文件；不含权重、真实点集或参考mask，不需重复上传点云。
2. 对`development_execution_request_v1.json`的完整SHA256单独授权。授权后才重新核验上传包、身份／资源、复用资产及新目标不存在，并按冻结映射不覆盖安装两个文件。
3. 按单向顺序材料化授权回执、runtime和单次launcher，启动一次固定tmux `bcsp_dev_four_models_seed0_v1`。固定420次native forward、batch1、8192点输出；不热身、不投票、不训练、不BNCal。异常停止，不自动重试或resume。
4. 结束后核验预测归档四文件，用户下载并本机核验，再绑定实际预测归档SHA开展既定本机统一评分与科研解读。未产生的归档哈希不预填；此运输包及当前request均不授权真实本机评分。

待授权request完整SHA256：

```text
85de7ec1c3f33e88009a177b2dd9532233f3da183df635fc15167079e0de12ea
```

运输包SHA256（31,808字节）：

```text
87160bb7ec986d6b813098a5ffaf12a54da0d27d27a155fc1d1221ef101cd047
```

正式协议位于项目`docs/cranial_bcsp_geov1_20261024/four_model_development_evaluation_protocol_zh_v1.md`；实现补充为同目录`four_model_development_evaluation_implementation_note_zh_v1.md`。两份均在模型预测前冻结，不追认为训练前预注册。
