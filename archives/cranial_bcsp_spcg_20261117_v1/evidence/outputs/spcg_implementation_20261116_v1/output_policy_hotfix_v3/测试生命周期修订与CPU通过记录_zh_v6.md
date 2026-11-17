# SPCG v3文件策略：测试生命周期修订与CPU v6结果

2026-11-16。

本轮仅修改人工测试fixture：删除坏SHA负例之前的g.close，将精确源码守卫关闭移至所有文件策略断言和结果输出之后的finally。保留先前Windows只读二进制兼容及人工脚本自身精确只读绑定。没有修改生产守卫、模型、runtime或v3候选入口；已逐项回核原冻结SHA一致。

唯一一次全新CPU_batch_v6执行通过，12项检查全部通过。使用真实继承make_policy与sys.addaudithook的子进程验证：

- 五个固定NPZ观察输出可写；相邻第六文件被拒绝。
- 输入文件写入被拒绝；绑定源码和人工脚本自身可读、不可写；邻近未授权源码被拒绝。
- 四份已冻结基础源码可经linecache和实际traceback.format_exception读取。
- 坏SHA绑定在守卫仍开启时被正确拒绝，全部断言结束后才关闭描述符。
- v3对v2仅有既定main变更和两个精确路径／读取辅助函数；计数、fixture和资源合同不变。

证据：CPU_batch_v6/result.json、child_stdout.bin、child_stderr.bin、completion_receipt_v6.json；本轮冻结范围Windows_CPU_scope_v6.json。此前失败批次保留，未复用、删除或覆盖。

没有服务器操作、SMI查询、模型／CUDA运行或训练。这是文件策略人工CPU回归通过，不是完整CUDA准入，也不代替最终P3与新request冻结。下一步可汇总本次最终字节的新P3，创建全新待授权request；不得复用已消耗的v2授权。
