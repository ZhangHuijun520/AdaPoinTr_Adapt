# SPCG v3精确输出／回溯读取适配：当前状态

2026-11-16。本轮无服务器操作、SMI查询、模型调用或GPU。

已新增隔离候选bcsp_spcg_cuda_entry_v3.py，相对v2只改main并增加两个辅助函数：

- exact_output_paths：输出目录内固定real_D_00.npz至real_D_04.npz，向继承policy传入这五条允许写路径，save_memory复用同一列表。
- traceback_source_guard：复用现有精确FD／大小／哈希守卫，为已绑定parent_helper、helper、UTC实现及entry提供只读权限；未泛化放开目录或任意NPZ。

科学模型、head/factory/runtime、U/H、provider、资源和11／3／3／0合同未修改。以上仅为未验证候选，未部署。

## 唯一CPU批次失败

冻结12项CPU范围后执行一次。第1项“五个输出路径唯一且归属固定目录”通过。人工子进程随后初始化真实继承ExactSourceReads时抛出`RuntimeError: exact source hash drift`，未进入实际policy写入／traceback断言。

失败位置为继承守卫verify的os.read读取结果与Path.read_bytes冻结哈希比较。运行环境Windows。该守卫使用os.open(..., O_RDONLY)，未显式指定Windows O_BINARY；Windows文本描述符与CRLF源码的兼容性是待核查线索，尚未测定为根因。此记录不把CPU失败归为模型或Linux生产守卫失效。

保留CPU_batch_v3/failure.json、child_stdout.bin、child_stderr.bin、policy_child.py及人工fixture；未删除、修改或重跑。通过检查数为1，不是12项通过。

**新P3未通过／未完成，新execution request及运输包未创建。** 旧v2 request已消耗，不能复用。本轮不自动修复测试环境或放宽生产守卫。

下一步建议仅只读核查该人工Windows文件描述符读取的字节差异，确认是CRLF／文本模式还是实际源码绑定错误；查明后再限定修订测试兼容性或选择合适Linux人工环境，不改变科研公式或继续GPU试跑。
