# H2-COUPLE Fold D 正式只读训练后冻结审计与AUX_D配对核验

2026-11-07。结论PASS，34项检查全部通过。

## 完成与清单

退出码0，worker/tmux均已退出，无failure或startup_failure。精确完成3900次forward/backward/clip/optimizer更新，100遍历、31200曝光、300丢弃。3900条指标及3902条资源记录完整，BNCal、评价、resume均false。

COUPLE_D checkpoint为407239343字节，实测SHA256：

```text
216bf45e144c205f7b52329d8542f04a75986012d53765ed43f8b622eeff34ca
```

AUX_D checkpoint也重新读取文件字节核验，与冻结值一致：

```text
0e8afe3ba44e8b35105d7e4f45677517442fbcc54b48b7ada899075ee6e1162f
```

15个精确COUPLE输出、payload manifest成员/大小/哈希及100个冻结资产/配对文件均通过核验。产物目录审计前后inode、权限、大小、mtime不变；atime不作为内容差异。本次未下载/反序列化任一权重，未解码NPZ或写服务器、运行模型。

## AUX_D／COUPLE_D公平配对

全量初始参数指纹、持久state指纹、seed及canonical order相同；COUPLE真实dispatch记录AUX_initialization_exact_match=true并绑定相同初始化JSON哈希。共有factory构建证据除mode外相同。原362项参数组加新增head两项、optimizer defaults、完整order_plan和exposure记录均一致。

3900个实际case/source批次、LR、BN momentum、clip和step提交标记逐条一致。两臂科学配置仅H2.mode不同，均8192输入/8192目标、315病例/63来源、3900更新；未根据C折或本折loss调参。配对不要求后续权重、动态残差标签、loss或梯度相同。

## 耦合日志与资源

所有3900步模式COUPLE且generation=step。首批delta0、scale1；后续确有非中性耦合。逐记录重算exp(log(1.25)*tanh(delta/log(1.25)))、尺度边界、coarse中心保持及r_used=s*r_raw。使用既定rel_tol=2e-6/abs_tol=1e-6，未放宽；最大舍入误差：

```json
{
  "scale": 1.5064937586295457e-07,
  "radius": 4.859195357198587e-08,
  "center": 1.1920928955078125e-07
}
```

同时核验raw Q参考的log半径目标、SmoothL1 beta0.1及0.1单次加权和总loss加和。loss_reconstruction沿用父字段并含辅助项，纯原始重建损失应读loss_original_reconstruction。

3902条资源记录满足原上限，设备显存峰值14208 MiB，Torch allocated峰值13388433920字节，reserved峰值14386462720字节，RSS峰值1700102144字节。PID警告按既定DIAGNOSTIC_ONLY政策保留，不证明跨命名空间所有权；采样监测不等同cgroup硬隔离。

## 证据限制与下一步

初始化比较使用已记录指纹和冻结factory证据，未重建初始张量；checkpoint仅字节哈希，不校验反序列化后的张量。耦合核对基于已保存矩日志，完整点张量与梯度未重算，实际消费者与detach路径沿用已绑定adapter及既有CPU/CUDA证据。有限原生Mamba梯度非确定性继续披露。

至此H2两臂×C/D四个训练运行均完成正式冻结；尚没有H2开发集预测或评分，不能判断形状精度、覆盖或接口吻合收益。

下一步建议仅核对四模型的预测入口兼容性及既定评价合同，再准备每模型105例、共420次Native预测的待授权request。COUPLE固定病例的额外20次条件干预仍需按原协议单独授权，不混入Native性能表。本次未创建评价request、启动预测/评分或改阈值。
