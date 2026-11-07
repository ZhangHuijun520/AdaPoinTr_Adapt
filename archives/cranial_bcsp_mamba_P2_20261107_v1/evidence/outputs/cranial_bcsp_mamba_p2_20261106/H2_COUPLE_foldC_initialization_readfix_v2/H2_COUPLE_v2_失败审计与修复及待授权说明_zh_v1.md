# H2-COUPLE Fold C v2：失败冻结与精确只读绑定修复

2026-11-07。v1失败审计通过；v2本机P3通过，状态AWAITING_EXPLICIT_USER_AUTHORIZATION。

## v1已消耗，不得复用

正式只读审计重新核验了5个失败输出、15个安装/控制/引用文件；审计前后inode、大小、权限和mtime稳定（排除atime）。退出码1，worker/tmux均退出。resources.jsonl为空，未创建训练metrics、checkpoint、order或本运行初始化文件。冻结源码显示异常发生于模型构造后、dataset构造与train_lifecycle调用之前，未进入训练更新循环；这不是独立CUDA内核跟踪结论。

被拒绝的文件仍为289字节，SHA256为f1622a6a792b347ebbaea21884ad3a5f89862e2662a3b95f6795bec91a2414fe，内容未发生变化。失败根因是原运行期read_roots没有包含该精确AUX初始化JSON，而不是模型数值或资源超限。

## 唯一生产变化

隔离v2入口仅在原read_roots列表中增加Path(q["aux_pairing"]["initialization"]["path"])。新增的是精确文件，不是父目录。文件策略原有禁止外部写入、链接/秘密/payload守卫保持不变；实际json_bound()继续核验大小和SHA256。AUX及v1入口保留原字节，不覆盖。

模型、三个H2模块、优化器、数据、批次顺序、零初始化、8k输入/8k输出、3900更新、100遍历、31200曝光、300丢弃及全部资源阈值保持不变。不根据loss调参，不重复GPU preflight。

## 人工CPU回归与P3

新版40项检查通过。其中子进程启用了实际FilePolicy.audit，通过实际入口read_roots表达式构造策略：重现旧策略拒绝；新策略下json_bound精确读取成功；拒绝相邻JSON、该文件写入、秘密、未授权checkpoint/NPZ；哈希和大小不匹配仍拒绝；原自有日志写入保持允许。

本次首批测试在继承的test32连续字符串断言停止。仅将该断言改为AST列表成员检查，失败源码及回执保留；生产入口未因此修改，实际audit-hook子进程检查仍必须通过。最终通过批次为artificial_cpu_batch_v2。

P3核验了生产入口相对v1只有上述一个表达式增量、共享实现哈希不变、完整COUPLE分派及同初始化/同顺序合同不变。CPU使用人工模型facade，不代表新的CUDA训练或科研效果证明。

## 新待授权request与运输

完整request SHA256：

```text
da96af70b5e3018c4a64c13815348f70f61575b3c455139fab155f2bd801fd90
```

运输包：bcsp_p2_H2_COUPLE_foldC_pending_20261107_v2.tar.gz，大小21664字节，SHA256：`c4d2a0035f96e6a92fedd8e9f1c1f4d4e97c53cf63c7c6cae709d2b00169f475`。

上传final_pending_request_v2目录中的tar.gz、.sha256、.bytes、.contents.sha256四文件到/home/jovyan。v2包含8个不覆盖安装目标；使用全新安装根、run目录、tmux和control绝对路径。v1保持ATTEMPT_CONSUMED_FAILED_BEFORE_TRAINING_NO_REUSE，失败正式审计也绑定在v2请求中。

本轮服务器仅进行了授权的失败只读取证；没有部署v2、训练、评价、BNCal或resume，也没有材料化正式授权回执、runtime、launcher及attempt claim。包内仅为待授权launcher模板。执行前仍须复核当前身份/资源、上传包、全部新目标不存在及复用资产。下一步需要针对本v2完整哈希单独授权不覆盖安装与唯一一次训练。
