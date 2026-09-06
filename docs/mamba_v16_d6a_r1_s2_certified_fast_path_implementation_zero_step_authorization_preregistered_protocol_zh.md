# Mamba v1.6 D6-A R1 S2 certified fast-path implementation/zero-step 执行授权预注册

## 1. 授权对象

本授权仅允许实现一个隔离的 S2 shadow selector，并执行一次固定 168 例 artificial CUDA zero-step。生产 `utils/mamba_d6a_slot_allocator.py` 和冻结 S1 shadow 必须保持原 SHA256，不允许把 S2 接入生产 R1。

## 2. S2 实现边界

S2 保持完整 `32 x 8192` D2H、CPU float64 转换、candidate-index epsilon 与 SciPy `maximize=True` 不变。每行 top-32 截止并列全部进入升序列并集。

只有同时满足以下条件，才能返回 reduced solution：

1. 每行第 32/33 大 adjusted score 的 gap 严格大于冻结 cutoff guard；
2. 对 reduced optimum 的 32 条已选边逐一禁用并重求最优后，best 与 second-best objective 的 gap 严格大于冻结 uniqueness guard；
3. assignment 覆盖、候选唯一性、finite 等不变量全部成立。

否则必须再次独立执行完整 S0，并直接返回 S0 的 slot mapping、hard assignment、selected indices 与 objective。不得用未获证 S2 输出填充 fallback。

## 3. 一次性 artificial zero-step

完全复用父协议冻结的 7 个 family、168 个 seed 和 `32 x 8192` float32 矩阵。每例单独执行完整 S0 reference 与 S2，并要求：

- slot mapping：`168/168`；
- sorted selected indices：`168/168`；
- hard assignment：`168/168`；
- adjusted objective：`168/168`；
- 每例 selected indices 为 32 个唯一值，输入状态不变；
- false-positive certificate：0；
- certified fast path 至少 `96/168`；
- independent normal 为 `64/64` fast path；
- collision-heavy 为 `32/32` fast path；
- 其他所有未认证病例均执行 S0 fallback。

必须完成全部 168 例后才允许分类。语义失败冻结 equivalence negative；语义通过但覆盖率不足则冻结 routing negative。任何负结果都禁止性能测试。

## 4. 明确禁止

本授权中的 timing、warmup、timed run、torch profiler、optimizer step、model update 和 D6 case access 全部为 0。不访问 checkpoint、STL、NPZ、confirmation、holdout、official test 或 sealed 数据。

即便 zero-step 全部通过，也只允许以后另行预注册和签发 S2 artificial performance benchmark，不自动授权 benchmark、生产修改、formal rerun、seed-0/seed-1 training、D6-B 或 selection。
