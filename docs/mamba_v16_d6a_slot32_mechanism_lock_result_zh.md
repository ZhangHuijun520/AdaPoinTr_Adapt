# Mamba v1.6 D6-A slot32 mechanism 协议冻结结果

> 本次结果只冻结 D6-A 的科学问题、R0/R1 机制、assignment、loss、测试与权限边界。未提取 D6 geometry，未生成病例，未校准，未训练，也未访问 confirmation 或其他 sealed 数据。

## 冻结结论

- R0 固定为 D5 V1 的精确 reference，在 D6 development100 上重训后只提供来源迁移基线，不具备推进资格。
- R1 是唯一实验候选：保留 R0 的 27D descriptor、64D point feature 与 shared point calibration branch，引入 32 个 64D slots。
- R1 最终输出由 `32 x 8192` pointer logits 上的 deterministic maximum-weight rectangular linear assignment 得到，必须恰好包含 32 个不同 candidate indices。
- 训练 hard-forward 使用同一个全局唯一 assignment；soft-backward 仅使用固定温度 `1.0` 的 row softmax STE。因此训练 forward selected set 与 inference selected set 必须完全一致。
- 正式 loss 由 `L_point`、`L_support` 和 `L_shape` 组成。两个附加 loss 的权重当前未设定，必须在 D6 generation audit 后通过独立 training-only gradient calibration 冻结。
- R1 trainable parameter 上限固定为 `100,000`。超限必须在任何 D6 geometry access 前停止。

## 锁链

- mechanism protocol SHA256：`2fff4782d429a3ea70607560bee9f464fb7b4eb7cea261376a91eb648a72f284`
- mechanism receipt SHA256：`acd62da63f0788ed2cbca2d48a49114c4cf8cd89b49a878d7fcba94e7ecd2a89`
- mechanism `files.sha256` SHA256：`4cbad1016851057152ad536bb69462df9a2c0b3d2440780336e3f24ac69d1a12`
- R0/R1 contract SHA256：`cfab7bbdbba9edfb447d72f8d11ce2dd708f257b8021e87fe46e0d2ad7fec968`
- synthetic zero-step contract SHA256：`1267c23f7a6c0a1c782546a5a77c5eaf083c75d65456c4fcbc0b34204262931a`

该 lock 继续绑定：

- D6 source125 acquisition receipt：`865b9fb30ef52c532ae5dd4c5ff18405833dee0570144ee94957cf5c460dab71`
- D6 source125 acquisition manifest：`d8509c44dd36575d46784972f70ec8f808754d3ffa84f390655ef3e5467c0fc1`
- D5 V0/V1 negative result：`6b4eceafa24e29077fa48dae086df36bec3e6faea597793c388e05cf658f5932`
- D5 complete report：`f69bc137bc0d57ee43cd2ee1f4e8edad667ceabacc14875ca04180582152bfd6`
- D5 candidate protocol：`135cd7a99da57b36d94220fc8b6ed0ec73b87bb35443ddbd898e1216edba03ed`
- D5 V1 implementation：`6cca9c11f302da3ca202f3e33547c62e4584eeb0fd81f9e96c20f2787e04f070`

## 已通过的协议测试

- R0/R1 candidate set、8192 candidates、32-slot budget 和参数上限固定。
- slot-order greedy、随机/Gumbel assignment、temperature scan 均被拒绝。
- GT mask 进入 inference signature 被拒绝。
- generation、calibration、training 或 confirmation 权限提前打开被拒绝。
- 不可运行 lock 输出可重复且逐字节确定。

## 当前授权

只允许：

1. 实现 R0/R1；
2. 使用人工 points 和 masks 运行 deterministic、uniqueness、assignment、loss、leakage 与 tiny-learning tests；
3. 测试通过后运行不含 D6 身份或 geometry 的 synthetic zero-step。

继续禁止：D6 development extraction、generation、gradient calibration、seed-0/seed-1 training、proposal confirmation、D6-B、candidate selection 与任何 protected/sealed access。

## 下一步

实现 `utils/mamba_d6a_slot_allocator.py` 及独立 toy tests。只有全部实现测试通过，才能执行固定的 artificial zero-step；zero-step 仍要求 optimizer steps=`0`、model updates=`0`、D6 cases=`0`。
