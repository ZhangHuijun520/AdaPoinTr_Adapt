# Mamba-Implant-8192 第一版设计与运行说明

本文档记录 AdaPoinTr-Implant-8192 进入 Mamba 改进阶段的第一版实现方案。

## 1. 总体判断

第一版不建议直接替换 AdaPoinTr 的 encoder / decoder / query generator / rebuild head。原因是当前 AdaPoinTr-Implant-8192 baseline 已经形成稳定协议，直接大规模替换会同时改变全局上下文建模、query 生成、decoder cross-attention 和重建头，很难判断性能变化来自 Mamba 还是来自结构扰动。

因此第一版采用低侵入的 Mamba Adapter：

```text
defective skull points
  -> DGCNN grouper / point proxy extraction
  -> AdaPoinTr encoder
  -> Mamba Adapter
  -> AdaPoinTr decoder / query / rebuild head
  -> implant point cloud, 8192 points
```

代码层面插入在 `PCTransformer.forward()` 中：

```python
x = self.encoder(x + pe, coor)
x = self.encoder_adapter(x, coor)
```

baseline 配置没有 `mamba_adapter.enabled: true` 时，模型行为保持不变。

## 2. Adapter 形式

第一版采用残差式 Adapter：

```text
x = x + alpha * DropPath(MambaBlock(LayerNorm(x)))
```

默认配置：

```yaml
mamba_adapter: {
  enabled: true,
  adapter_type: mamba_ssm,
  depth: 2,
  d_state: 16,
  d_conv: 4,
  expand: 2,
  use_fast_path: false,
  drop_path: 0.05,
  alpha_init: 0.1,
  order: xyz,
}
```

其中 `alpha_init=0.1` 是为了让第一版从接近原 AdaPoinTr 的状态开始训练，降低训练初期扰动。当前服务器的 `causal_conv1d_cuda` fast path 未能加载，但 `mamba_ssm` 的 `use_fast_path=False` slow path 已通过 forward 验证，因此第一版默认关闭 fast path。正式实验应使用 `adapter_type: mamba_ssm`。代码也提供 `adapter_type: gated_conv`，仅用于没有安装 `mamba-ssm` 时的配置/脚本 smoke test，不应作为正式 Mamba 结果。

## 3. 点云序列化

Mamba 是序列模型，点云本身无序，因此第一版不能使用随机顺序。当前实现使用 encoder proxy center `coor` 的确定性排序：

```yaml
order: xyz
```

流程为：

1. 根据 proxy center 坐标排序 token；
2. 将排序后的 token 输入 Mamba Adapter；
3. Adapter 输出后反排序回原 token 顺序；
4. 再交给原 AdaPoinTr decoder。

这样 decoder 看到的 token 与坐标 `coor` 仍然一一对应，不破坏原本的 cross-attention / local graph 关系。

第一版排序只使用输入缺损颅骨产生的 proxy 坐标，不使用 GT implant、GT rim 或完整颅骨，因此没有标签泄漏。

## 4. 对称感知序列化的后续版本

颅骨具有近似双侧对称性，用户提出的 Symmetry-Aware Serialization 是合理的后续方向。但它不建议放进第一版，原因是它会同时引入：

- 对称轴估计误差；
- 镜像侧特征构造方式；
- 缺损跨中线时的软对称约束；
- Mamba 条件注入方式；
- 可能的边界/rim 识别误差。

第一版建议先验证“低侵入 Mamba Adapter 是否带来增益”。若有稳定收益，再做 V2：

```text
input defective skull
  -> non-leaking symmetry axis estimation
  -> mirrored healthy-side context / symmetry code
  -> Mamba Adapter condition injection
```

可选方案：

- 使用 PCA / canonical coordinate 估计粗对称轴；
- 使用仅由 defective skull 推断的 mid-sagittal plane；
- 以镜像后的完好侧局部特征作为 Mamba 的条件 token 或 hidden-state conditioning；
- 对跨中线缺损使用软对称权重，而不是硬镜像替代。

## 5. 新增文件

模型改动：

- `models/AdaPoinTr.py`

新增配置：

- `cfgs/SkullFix_models/MambaAdapter_implant_full100_out8192_bncal.yaml`
- `cfgs/SkullBreak_models/MambaAdapter_implant_full100_out8192_bncal.yaml`

新增脚本：

- `scripts/run_skullfix_mamba_adapter_full100_out8192_bncal.sh`
- `scripts/run_skullbreak_mamba_adapter_full100_out8192_bncal.sh`

新增依赖说明：

- `requirements_mamba.txt`

## 6. 运行建议

正式跑 full baseline 前，建议仍然按 gate 进行：

1. 安装并验证 `mamba-ssm`；
2. SkullFix 单样本 overfit 或小样本 sanity；
3. SkullFix full100 Mamba Adapter out8192；
4. SkullBreak full100 Mamba Adapter out8192；
5. 与 AdaPoinTr-Implant-8192 baseline 在相同 test split、相同 voxel/point/rim 指标下比较。

安装依赖：

```bash
python -m pip install -r requirements_mamba.txt
```

SkullFix full：

```bash
bash scripts/run_skullfix_mamba_adapter_full100_out8192_bncal.sh
```

SkullBreak full：

```bash
bash scripts/run_skullbreak_mamba_adapter_full100_out8192_bncal.sh
```

## 7. 风险与注意事项

- `mamba-ssm` 与 CUDA / PyTorch 版本强相关，安装前应确认服务器环境。
- Adapter 参数量增加不大，但会增加训练显存和时间，应记录 GPU memory、inference time、params/FLOPs。
- 如果第一版收益不稳定，应先做 `order: x / xyz / zyx` 排序消融，再考虑对称序列化。
- 不要使用 GT implant 或 GT rim 定义输入序列，否则会产生信息泄漏。
