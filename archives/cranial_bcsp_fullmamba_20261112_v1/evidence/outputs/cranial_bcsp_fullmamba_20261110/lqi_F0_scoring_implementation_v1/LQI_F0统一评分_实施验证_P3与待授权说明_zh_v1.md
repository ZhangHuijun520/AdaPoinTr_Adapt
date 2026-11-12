# LQI／F0 统一 CPU 评分：实施、验证、P3 与待授权说明 v1

日期：2026-11-11。结论：**专用评分入口完成；50 项人工 CPU 检查通过，本机 P3 通过；最终 request 保持 AWAITING_EXPLICIT_USER_AUTHORIZATION。尚未运行真实评分。**

## 1. 实现范围

新增 `bcsp_lqi_F0_two_arm_score_v1.py`，仅适配两臂评分身份、归档读取与汇总计数，不修改原 F0／T0／M0 评分入口、指标模块、数据、模型或预测。

- 固定 F0、LQI 两臂，比较方向为 `LQI minus F0`；两折各 105 例、21 来源，各来源五种缺损，共 210 例、42 来源。
- 严格绑定 F0 246 成员归档与 LQI 216 成员归档的顺序、成员名称、模型标签、请求哈希、checkpoint／输入／坐标元数据、实际 Native construction 与状态／RNG证据。
- 精确接受 LQI 的 **0 字节 `cache_manifest.jsonl`**，不将零字节例外扩展到预测、F0 缓存日志或其他成员。预测、代码、授权文件等非空守卫继续保留。
- 两臂 420 个模型／病例组合均有实际 coarse[256,3] 和 dense[8192,3]，不虚构缺失中间点集，也不运行额外 forward。
- 重算后将 F0 210 行和共享控制 420 行与已冻结历史评分的对应完整记录逐一比较，共 630 行；任何差异即停止，不输出成功 completion，不静默更新历史结果。

## 2. 保持不变的科研定义

以下函数与原 F0 评分入口的 AST 完全一致：`load_prediction_arrays`、`load_prediction`、`select_metrics`、`position_shape`、`risk_labels`、`stage_geometry`、`score_case`、`aggregate_source`、`describe_pairs`、`paired_summary`、`case_differences`、`defect_summary`、`csv_rows`、`risk_transitions`。

冻结指标源码 SHA256 仍为：

`af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766`

主指标为 A1 面积加权 E_P95（毫米）。保留原 J_P95、覆盖率、CD-L1、远端离群、位置／尺度、coarse／dense几何和风险指标；原阈值不变。误差差值负值表示改善、覆盖率差值正值表示改善；半径比不强行按单向优劣排序。

保持五种缺损先按来源等权汇总，再在折内按 21 来源等权汇总。两折分别报告，保留全部异常／退化病例；描述性单种子比较不扩展成训练随机性或临床适用性结论。不做筛选、调参、ICP、Oracle对齐、后处理、bootstrap、p 值或正式 gate。

## 3. 人工 CPU 验证

环境为已授权的本机隔离 Python 3.9.21、NumPy 1.26.4、SciPy 1.13.1、psutil 5.9.0、scikit-image 0.24.0；CUDA_VISIBLE_DEVICES 为空、线程数固定为 2。不导入模型、Torch 或 GPU 后端。

第一批人工测试在进入评分运算前，因沿用旧三臂fixture的字典索引而触发 `KeyError('LQI')`；失败产物保留于 `artificial_cpu_batch_v1`。仅将该测试参数改为本轮实际所需参数，生产入口保持原字节不变，新测试文件 v2 在全新 `artificial_cpu_batch_v2` 下执行。

**新版 50/50 项检查通过**，覆盖：

1. 实际冻结的 210 例元数据／420 预测绑定，缺例、重复预测、目标摘要或坐标漂移的拒绝。
2. 完整 request／authorization 校验及未授权、计数错误、配对方向错误的拒绝。
3. 两种 Native 归档读取路径、LQI 精确空日志、禁止空预测／非空LQI缓存日志／泛化允许空F0日志。
4. 错误模型版本、旧条件序列 construction、RNG 漂移、请求／checkpoint／预测哈希错误的拒绝。
5. 实际冻结指标在 12 行人工模型／控制数据上的计算，以及 D-only 反归一化、阈值边界、coarse／dense摘要一致性。
6. 两折 840 行人工流程及 168 个来源行的聚合，LQI minus F0方向、来源等权、未定义配对保留、退化新发与恢复分别统计。
7. 冻结 F0／共享控制不一致时停止并不产生成功 completion；首病例失败不继续后续病例；指标及核心函数 AST 保持一致。

840 行流程验证采用人工病例模板，并不等价于执行 840 次真实指标计算；实际指标只用于 12 行人工数据。本轮未读入真实预测／GT数组计算分数，没有科研结果解读。

本机 P3 状态：`LOCAL_LQI_F0_SCORING_P3_PASS`。其后完成最终 request 的 8 项元数据绑定复核，包含最终源码／测试／CPU结果／P3、两份归档、证据、630行历史记录绑定和内存中的完整授权合同校验；未材料化真实授权回执。

## 4. 最终待授权 request

文件：`local_scoring_execution_request_v1.json`

完整 SHA256：

`b394b3b8814ac729d07a79fe607cbf0636b1ee596546304f8f416bc66e88304a`

状态：**AWAITING_EXPLICIT_USER_AUTHORIZATION**，`execution_authorized=false`。

| 范围 | 数量 |
|---|---:|
| F0 模型行 | 210 |
| LQI 模型行 | 210 |
| 共享 Nop_D／GT_8192 控制行 | 420 |
| 病例评分总行 | **840** |
| 来源评分行 | **168** |
| 历史 F0／控制一致性核验行 | 630（属于上述840行的子集） |

预算保持 18000 秒、RSS 8 GiB、输出 2 GiB、2 线程，外部超时 18030 秒。唯一一次本机 CPU 评分，失败保留部分产物并停止，不自动重试／resume，不剔除病例继续。

未来结果目录：本实现目录下 `unified_scores_v1`；未来授权目录：本实现目录下 `authorized_execution_v1`。当前两目录均未创建，未产生真实授权回执、启动claim或评分进程。

授权后必须先重验入口、指标、CPU Python和版本、全部证据、两份归档与sidecar、历史评分、210参考bank及210点集容器，并确认执行／输出目标不存在。全部通过后才启动唯一一次评分。本轮无须上传服务器。

## 5. 当前边界及后续

本轮未操作服务器、未使用GPU、未重跑预测／preflight／训练／BNCal，也未启动真实 CPU 评分。尚不能判断 LQI 相对 F0 是否改善颅骨补全或接口吻合。

下一步单独明确授权上述 **request完整SHA256**，才可启动唯一一次本机 CPU 评分。完成后再单独进行正式只读评分后冻结审计，通过后才解读科研结果。
