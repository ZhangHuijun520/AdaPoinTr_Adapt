# SCQ-RF人工CUDA单次执行状态

2026-11-14。授权request完整SHA256：`85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32`。

## 结果

**本次CUDA准入失败，已停止，不自动修复或重试。该request已有执行尝试，不得复用。**

新鲜核验确认容器`shu-common-25721452-notebook-zbpgzu-0`、GPU身份及资源符合冻结request。上传压缩包与三个校验文件通过核验，52个复用资产的大小／SHA256通过，12个目标文件完成不覆盖安装及安装后哈希核对。按单向顺序创建授权回执、runtime和launcher后，提交唯一一次tmux启动。

首阶段`S_ref_eval1`的模型forward已经返回，在入口检查实际坐标消费路径时触发：

```text
RuntimeError('actual Q2 consumer mismatch')
```

该断言合并检查query-MLP、decoder q_pos、位置编码和FC重建条件中的坐标，当前保存结果没有分别标出哪一个消费者不匹配，不能仅凭该错误确定根因。此时尚未进入RF-Static或RF-Requery阶段，不能将它视为RF结构、梯度或效果失败，也不能认定CUDA准入通过。

## 实际计数与状态

| 项目 | 本次实际记录 |
|---|---:|
| full_forward尝试 | 1 |
| full_loss | 0 |
| full_backward | 0 |
| optimizer_steps | 0 |
| 退出码 | 1 |
| tmux会话仍存活 | false |
| worker PID 7717仍存活 | false |

阶段异常处理日志记录state、RNG、模块模式、BN动量恢复以及梯度清理均为true。已读取资源样本的阈值检查均为true；这些是当前观察结果，**不代替正式只读失败冻结审计**。没有运行后续阶段、重试、训练、BNCal或真实开发集评价。

## 保存位置

- [启动回执](authorized_execution_v1/launch_receipt_v1.json)
- [独立状态观察](authorized_execution_v1/observation_0.json)
- 本机原始传输stdout／stderr、安装及控制文件核验记录均保留在`authorized_execution_v1`。
- 服务器输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v1`。

下一步建议单独授权**正式只读失败冻结审计＋该坐标消费者hook合同的限定核查**。先确认是采集口径／调用顺序问题还是实际坐标传递问题，不放宽数值容差、不改模型、不运行forward；之后再决定必要修订范围。
