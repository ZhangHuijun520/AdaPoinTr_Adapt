# SCQ-RF v2单次CUDA执行状态

2026-11-14。授权request SHA256：`09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf`。

## 状态

**本次执行失败并已停止。v2 request已有执行尝试，已消耗，不得复用。**

安装前确认当前仍为冻结容器`shu-common-25721452-notebook-zbpgzu-0`，GPU、资源、上传压缩包及三个校验文件通过核验；56项复用资产大小与SHA256通过核验。7个新文件不覆盖安装并回读哈希一致，随后按单向合同材料化控制文件，提交唯一一次tmux启动。

S-ref参考forward完成，日志记录该阶段的状态／RNG／模块模式／BN动量恢复及梯度清理均为true。随后构造RF-Static模型时，原RF模块的初始化加载检查触发：

```text
ValueError('RF fixed private-seed values')
```

该失败点对应`load_initialization`在读取并校验冻结二进制后，调用当前运行环境的`initialization_values()`重新生成私有seed随机值，并要求与文件内tensor逐位相同的额外检查。不能仅凭这次失败认定冻结二进制损坏、RF公式无效或训练数值异常；本轮不修改初始化文件或科研实现。

实际计数为**1 full_forward／0 full_loss／0 full_backward／0 optimizer step**。RF-Static／RF-Requery均尚未执行forward。退出码1，worker PID8474与固定tmux均已结束。原始异常保存在`failure.json`；log还出现退出时读取守卫的次级KeyError，不能覆盖原始首错解释。

本次是启动与结果状态观察，尚未进行正式只读失败冻结审计，也没有完成CUDA准入。原生两臂loss／backward／显存及科研效果仍未知。未重试、训练、运行BNCal、访问真实数据或checkpoint。

## 证据位置

- [启动回执](authorized_execution_v2/launch_receipt_v1.json)
- [最终状态观察](authorized_execution_v2/observation_1.json)
- 原始stdout／stderr、上传／资产／安装核验记录均保存在本机`authorized_execution_v2`。
- 服务器输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v2`。

下一步建议仅做**正式只读失败冻结审计＋初始化字节合同核查**：重新核验冻结二进制和加载路径，区分字节损坏、绑定错误与跨环境重新生成随机数的逐位比较问题，并保留次级错误证据。不重生成／替换初始化、不运行模型或重试。
