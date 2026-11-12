# F0 两折 Native 预测入口核对与待授权范围

日期：2026-11-11。状态：范围草案已整理；入口尚需最小适配，未创建 execution request，未授权或启动预测。

## 📋 核对结论

Fold C／D 的 F0 最终训练及配对冻结证据已具备。下一步保持每折105例、合计210次 Native forward；不能根据训练 loss 判断补全性能。现有 P1／H2 预测入口不能原样运行 F0，需一个 F0 专用预测入口及一个针对性 CPU 测试文件，通过 P3 后再创建绑定最终实现哈希的待授权 request。不重复已经通过的 GPU preflight。

本次仅读取本机源码、配置及冻结元数据并编制范围文件；未连接服务器、读取真实点集数组、反序列化 checkpoint、运行测试、调用 GPU 或修改生产实现。当前容器及服务器资产的实时状态尚未重新核验。

## 🔍 入口兼容性

| 项目 | 结论与最小适配 |
| --- | --- |
| 模型工厂 | F0 为 `build_model(legacy_builder, seed=0)`，返回的证据结构也不同；旧入口的 variant 参数及顶层 variant 假设不能沿用 |
| 模型调度 | P1 两臂同折、H2 四模型的限定标签和模式不适用于 C_F0／D_F0 两折调度 |
| 权重加载 | 复用严格 checkpoint 元数据及 state_dict 校验；绑定 epoch99／3900 updates 和两折冻结 SHA256 |
| 输入 | 沿用已冻结开发顺序、精确文件路径及 D-only 归一化；只解码 partial，不读取 GT 张量 |
| 输出 | 全部210例保存 dense 8192×3 和 coarse Q 256×3；旧入口仅部分病例保存 coarse，必须适配 |
| 诊断缓存 | 复用现有 eval instrumentation，在同一次 forward 内采集，不额外执行 encoder、coarse 或完整模型 |
| 精确读取绑定 | 覆盖实际 F0 factory、encoder、decoder 及必要母版源码，不套用旧 T0／M0／H2 白名单假设 |

源码路径、实测大小与 SHA256 见 `prediction_entry_compatibility_review_v1.json`。

## 📐 固定预测合同

| 范围 | 固定值 |
| --- | --- |
| 模型／开发病例 | C_F0 105例、D_F0 105例；各21来源×5缺损类型 |
| 输入／输出 | 8192／8192；Q 为256点；FP32，TF32关闭 |
| 执行 | batch1、eval、inference_mode，恰好210次完整 forward |
| 禁止的额外调用 | warmup、loss、backward、optimizer step、BNCal、TTA 均为0 |
| Native 定义 | 保留原始预测；无 GT 配准、ICP、离群过滤或点数修改 |
| 坐标 | 沿用已冻结的 normalized 坐标；world = normalized × scale + center |
| 状态证据 | 每模型前后参数／BN 指纹、CPU／CUDA／Python／NumPy RNG 不变；每例清理 instrumentation 缓存与开关 |
| 资源 | 7200秒；RSS 8 GiB；Torch峰值20 GiB；设备22528 MiB；输出1 GiB；启动及执行保留4 GiB磁盘预算 |

每例记录 Q／P 的质心、回转半径、包围盒、有限点计数。10个代表病例保存8层 decoder 轨迹；代表例及10个 donor 共20个 fold/case 缓存 F／S／z／Q／X，均属于上述210例。

z 特指 query 构造前的 `backbone.global_feature`，不能混用 decoder 后的 `rebuild_global_feature`。未来 suffix 干预时，后者仍须按原生成头重新计算。本轮不执行原计划中另行授权的30次 decoder-only 机制调用，也不将未来 OOD 干预分数混入 Native 性能。

## ⚖️ 代表病例登记的时间偏差

正式计划已预先写明：每折每类取开发顺序首例，donor 取同类首个不同来源病例。本次在已审阅材料中未找到训练前冻结的精确 ID 表，因此按该原规则、在 F0 Native 预测前枚举，不能追溯宣称精确表已在训练前冻结。

| Fold | 五类代表病例来源 | 五类 donor 来源 |
| --- | --- | --- |
| C | train:001 | train:003 |
| D | train:004 | train:005 |

类别均为 bilateral、frontoorbital、parietotemporal、random_1、random_2。完整 ID 见 CSV 及登记附件。该选择未使用 GT 或 F0 预测结果，但其登记时间偏差须在后续协议中明确确认。每折五类来自同一个代表来源，不等于五个独立患者；其机制结论不能直接外推全部开发人群。此偏差不改变全部210例的 Native 评价范围。

## 📦 权重与后续边界

| Fold | checkpoint SHA256（各478810419字节） |
| --- | --- |
| C | `4fd73dd8c265781225ba63a712a5589b175c94f0ea0878a69ebf466265ebebe9` |
| D | `c4f29a8df3e36af2c87a20dc4888eb4b6a344bb448baa6403fb6c9c86023edaa` |

下一步的限定 implementation-only 范围：一个 F0 专用预测入口、一个人工 CPU 回归文件及 P3 证据。验证实际工厂／加载／authorize 路径、210计数与清单、全部 coarse 保存、缓存选择、代理模块下 trace 开关数值一致性及状态／RNG处理。CPU通过不代表 CUDA 或补全效果通过。

通过后才创建最终待授权 execution request，保持 `AWAITING_EXPLICIT_USER_AUTHORIZATION`。本轮范围草案的哈希不等于执行 request 哈希。部署与预测仍需单独执行授权，异常立即停止，不自动重试或恢复。

预测完成后的既定顺序为：正式只读冻结审计，下载归档及本机核验，再准备统一 CPU 评分。复用 T0／M0 已冻结预测进行后续比较，不增加训练或按当前 loss 调参。

## 📚 本次交付

- `F0_CD_210_Native_prediction_scope_draft_v1.json`：待审范围，尚不可执行。
- `F0_CD_Native_input_index_candidate_v1.json`：210例精确路径、哈希、归一化及两折权重／训练证据绑定。
- `recipient_donor_registration_addendum_v1.json`、`recipient_donor_pairs_v1.csv`：原规则枚举及登记偏差披露。
- `prediction_entry_compatibility_review_v1.json`：源码实测绑定、复用边界与最小适配。
- `preparation_consistency_verification_v1.json`、`preparation_manifest_v1.json`：本机元数据一致性核对及交付清单；不替代实施测试或 P3。

依据为项目正式计划 `docs/cranial_bcsp_fullmamba_20261110/Cranial_BCSP_FullMamba_正式实验计划书_zh_2026-11-10_v2.md`、两折正式训练冻结审计和兼容性 JSON 所列源码。本次未进行文献检索或新增科研效果判断。
