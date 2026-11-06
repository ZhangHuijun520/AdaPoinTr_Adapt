# P1 Fold C 配对预测失败产物：正式只读冻结审计

日期：2026-11-06。结论：失败现场已通过正式只读冻结审计；原预测执行仍为失败，旧 request 已消耗，不得复用。

## 核验结果

服务器20项检查及本机5项历史交叉检查全部通过。精确核验9个安装文件、4个控制文件、4个失败输出文件（launch.log、worker.pid、exit_code.txt、failure.json），以及仅有的predictions/tmp两个空目录。所有证据内容、大小、权限、所属用户和mtime在只读审计期间保持不变；不把atime当作内容变化。

退出码为1；tmux已结束，worker不存活。无forward claim、预测manifest、geometry summary、资源记录、完成标记或预测归档。根据明确的失败调用栈与调用顺序，forward尝试及成功预测均为0。资源峰值证据尚未生成，不能据此评价显存或CUDA数值性能。

本机逐字节核验收回的17个文件，并将9个安装文件与原运输映射交叉比较；授权回执、runtime和launcher的哈希分别与原启动材料化回执一致，失败JSON及完整启动日志与初次观察一致。完整证据见frozen_evidence，逐文件清单及哈希见local_freeze_verification_v1.json。

两份权重均重新计算SHA256：

- T0：8671656b5a2b0843ed426868d9d06976a2ead816808f9f7c54ddadb83515ab07
- M0：bc6a489bcd4df5123a3bb6616105d7ec4628fc365e71313398ee516bcf72ef9a

factory、encoder及helper源码哈希与冻结request一致。未读取点云数组、加载checkpoint对象、导入模型或运行forward；只对权重原文件进行流式哈希。服务器无写入、无清理、无修改、无重新启动。

## 失败原因与测试缺口

入口把factory所在目录加入了sys.path，但传给FilePolicy的只读roots没有该目录；sys.path不授予文件读取权限。随后module()对已冻结factory文件做精确SHA核验时，其open被FilePolicy拒绝。该失败发生在构造P1模型之前，并非Mamba/CUDA计算或权重形状错误。

此前CPU人工完整循环使用builder替身，没有走到真实FilePolicy约束下的factory/encoder模块加载路径，因此未发现该接入遗漏。CPU通过的结论仅覆盖其实际执行的合同，不证明完整服务器启动路径可用。

## 后续限定实施范围（本轮未实施）

仅在新版隔离预测入口中增加factory与encoder两个已冻结精确源码路径的只读大小/哈希绑定，保留所有通用roots与payload/secret/链接守卫；不得放行整个依赖目录。对实际模块加载路径补人工CPU回归，覆盖文件读取与编译、encoder导入、字节码候选路径（如实际触发）、内容漂移、写入拒绝、邻近未绑定源码及链接拒绝；只处理实际必需的精确路径。

保持factory/encoder原源码、模型、权重、105例数据、210-forward预算与资源阈值不变。CPU回归与P3通过后再生成全新输出/control/tmux路径的新待授权request；本轮没有创建新request，也不重复已通过的GPU preflight。
