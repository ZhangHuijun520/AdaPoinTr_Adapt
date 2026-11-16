# SCQ-RIVE Static_C正式只读训练后冻结审计

状态：**通过，39项核验全部通过。** 本轮延续已授权审计，没有运行新实验。

## 核心结果

- 退出码0，固定tmux与worker均已结束。
- 完整3900更新、100 traversals、31200曝光、300drop；完整实际批次逐步对应冻结C折order，LR/BN、clip和loss合同一致。
- 3900条几何日志与metrics逐条匹配；Static全部复用N0，Q0→Q1→Q2质心关系及Q2/coarse摘要一致，完整coarse+dense重建loss对应。未独立重新计算KNN或模型张量。
- 初始参数/持久状态指纹、共同母版、冻结头初值和419参数分组符合绑定；与历史C折初态、顺序、曝光及优化器分组一致。历史跨设备模型不作为本轮准确率对照。
- 3902条资源记录的条件逐条重算通过；有效墙钟3600秒。训练完成记录elapsed1489.370秒，资源末条elapsed1495.913秒，二者起止口径不同。
- 16个输出文件、15个安装/控制文件、精确目录集合、12成员payload manifest均核验；审计前后31个文件内容SHA与内容相关属性完全一致，忽略atime。
- BNCal、evaluation、resume均false。没有自动重试或后续臂。

## 最终checkpoint

大小489927058字节。独立流式读取两次SHA256：

```text
80c59d40fe3d0a415e41c67f1b036f619e2e862fde829f42a66ecb73e950eb97
```

与completion及manifest相同。未反序列化checkpoint，未从权重重建模型。

## 资源与解释边界

Torch allocated峰值约13.0GiB，reserved约13.82GiB，SMI14638MiB，workerRSS约1.56GiB；均低于原阈值。采样监测不保证捕获所有瞬时峰值，不是专属cgroup或进程树硬限制。SMI/容器PID差异按既定诊断口径保留。

AdamW defaults里的weight_decay=0.01是库默认记录；实际419参数分组明确覆盖为5e−4或0，未把库默认误当实际训练衰减。completion/权重内旧stage名BCSP_INPUT_DENSITY_V1为复用runtime的历史标签；run_identity明确RIVE、Static、C及实际资源合同，不是本轮身份错配。

本次只读审计没有服务器写入、forward、backward、optimizer、评价、BNCal、NPZ数组加载或checkpoint反序列化；也没有据训练loss判断补全精度。

## 下一步

可单独授权**仅准备RF-Requery Fold C待授权训练request**，绑定本次正式冻结凭据、相同当前设备、初态、C折批次顺序和3900步合同。复用已验证入口/bridge，不重复GPU preflight；不自动启动训练，不据本次loss调参。后续request前仍需核对剩余空间；完整四运行矩阵容量未获认证。
