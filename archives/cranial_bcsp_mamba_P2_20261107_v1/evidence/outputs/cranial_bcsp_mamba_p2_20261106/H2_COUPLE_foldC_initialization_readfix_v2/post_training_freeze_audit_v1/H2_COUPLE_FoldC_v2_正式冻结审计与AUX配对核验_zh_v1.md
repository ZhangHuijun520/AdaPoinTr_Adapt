# H2-COUPLE Fold C v2：正式只读训练后冻结审计与AUX配对核验

日期：2026-11-07。结论：PASS，34项检查全部通过。最终机器可读报告为audit_report_v2.json。

## 完成与产物

训练退出码0，worker与固定tmux均已退出，无failure/startup_failure。精确完成3900次forward、backward、clip及optimizer更新，100次遍历，31200次病例曝光，300次丢弃。3900条指标与3902条资源记录完整。

COUPLE最终checkpoint为ckpt-last.pth，407239343字节，服务器重新读取字节计算SHA256：

```text
08bd09eecb0df821e7e34d81a45612a769cf4858e827787f2cfc0412c1720083
```

AUX最终checkpoint也重新哈希，与已冻结值一致：

```text
15c8c3f717c340a2661b78d9e17d33f56ceb79dfdadd10908015b02f7dfc9538
```

COUPLE15个输出文件的精确集合、大小、payload manifest及哈希一致；审计前后inode、权限、大小、mtime保持不变，排除atime影响。共102个冻结资产/配对文件重新哈希，包括AUX原产物及相关实现。未下载或加载任一checkpoint。

## 公平配对

两臂的完整initialization.json一致：参数指纹、持久state指纹、seed0和canonical order全部相同。COUPLE实际dispatch记录AUX_initialization_exact_match=true，绑定的AUX初始化SHA也一致。

两臂factory构建证据仅H2_mode不同；两个模型均拥有同一1025参数范围头、原362项参数分类及新增两项head分类。optimizer defaults、完整参数组、order_plan和exposure.json完全一致。所有3900条实际case/source批次、LR、BN momentum、clip及commit标记逐条相同。原静态科学配置仅H2.mode从AUX改为COUPLE；数据、归一化、8k输入/8k输出、3900步及数值合同未改变。

配对要求是初始状态和训练协议相同，不要求训练后的权重、动态残差标签、loss或梯度相同。

## 耦合与损失日志

逐条核对COUPLE模式及generation=step。首批8个delta为0、scale为1；后续存在非中性耦合。所有记录的scale满足固定exp(log(1.25)*tanh(delta/log(1.25)))及浮点边界，raw/used coarse质心保持、半径满足r_used=s*r_raw。

所有3900步复算log半径目标（参考raw Q）、SmoothL1 beta0.1、辅助项0.1权重和总loss加和关系。用于核对的继承容差为rel_tol=2e-6、abs_tol=1e-6，未放宽。对应最大舍入误差：

```json
{
  "scale": 1.5525090679702203e-07,
  "radius": 5.327994045956075e-08,
  "center": 1.1920928955078125e-07
}
```

H1关闭，BNCal、evaluation和resume均为false。loss_reconstruction沿用父字段并包含辅助项；原始重建损失应读loss_original_reconstruction。

## 资源与边界

全部3902条资源记录满足原上限。峰值Torch allocated为13388433920字节，reserved为14386462720字节，设备显存14208 MiB，RSS为1701154816字节。PID口径警告按既定DIAGNOSTIC_ONLY策略保留，不推定跨命名空间所有权；资源监测不是cgroup硬隔离。

本次不写服务器，不运行forward/backward，不解码真实点集或反序列化checkpoint。耦合公式核对来自已保存的矩日志；没有重新计算完整raw/used点张量或梯度。实际坐标消费者与detach路径的证据仍来自已绑定adapter及既有CPU/CUDA验证。原生Mamba有限梯度非确定性继续披露。

## 检查器修正与结论边界

初版离线检查器一处factory合同比较仍将mode填为AUX，导致检查失败；已保留analysis_failure_v1.json。仅改为与冻结COUPLE模式比较，使用同一批已下载证据生成audit_report_v2.json；没有修改生产源码、重新取证或重跑实验。

本审计证明运行与配对证据完整、自洽；不能据此判断COUPLE改善了形状、覆盖或接口吻合。按事前协议，后续应继续Fold D同合同配对训练准备，再进行既定Native评价与单独授权的机制干预。不根据本折训练loss调参。本次没有创建或执行下一运行request。
