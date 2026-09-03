# Mamba v1.6 D6-A full-inference efficiency implementation zero-step

本阶段只验证效率测试实现，不产生正式效率门控结论。

- 输入：固定 seed 的人工 `1 x 8192 x 27` float32 descriptor，不含 D6 身份或几何。
- R0：head forward 加 stable top-32 selector。
- R1：slot allocator forward 加 SciPy 全局唯一 assignment。
- R0/R1 各执行一次完整推理，只验证 32 个唯一索引、有限输出和模型状态不变。
- 正式 warmup 设定仍为 10、timed runs 仍为 50，但本 zero-step 两者实际执行次数均为 0。
- 不计算 latency ratio、peak-memory ratio，也不作 pass/fail 判定。
- 下一步只能单独签发 formal efficiency execution authorization。
- Training、seed-1、confirmation、D6-B、selection 与 sealed access 继续锁定。
