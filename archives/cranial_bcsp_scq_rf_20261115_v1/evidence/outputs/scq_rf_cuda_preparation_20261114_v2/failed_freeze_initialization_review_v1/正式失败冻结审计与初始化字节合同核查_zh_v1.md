# SCQ-RF v2正式失败冻结审计与初始化字节合同核查

2026-11-14。仅只读审计；未修改实现、未重生成随机值／初始化、未导入torch或模型、未运行测试／forward／CUDA、未重试。

## 1. 结论

**正式失败冻结审计通过，23项检查全部满足。实际加载的冻结初始化文件完整且与本机原件逐字节一致；本次阻断来自加载器附加的随机值重生成逐位比较。CUDA准入仍未通过。**

初始化文件924,684字节，SHA256：

`a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e`

该值同时匹配request、服务器实际路径文件、本机原件及冻结来源清单。四个参数块的独立SHA256匹配；231,171个FP32值全部有限，V2.weight／bias逐字节为零。因此现有证据排除了这份实际文件的字节损坏、拿错冻结文件或零输出层缺失。

这里不宣称已测量随机值差异大小，或已证明差异唯一由PyTorch版本导致。运行时重新生成的数组没有保存，本轮严格没有补算它们。

## 2. 失败冻结结果

已消耗request完整SHA256：

`09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf`

核验仍为冻结容器`shu-common-25721452-notebook-zbpgzu-0`及GPU身份，退出码1，worker与固定tmux均已结束；该request不得复用。

两次读取共26个文件、唯一内容1,371,309字节，在32文件／8MiB／60秒预算内。失败输出6个、新安装及控制文件11个、初始化相关文件5个、上传包及校验文件4个，清单／哈希及排除atime后的内容属性全部稳定。七个新安装文件、上传包与校验文件、授权回执及单向runtime、launcher与claim均匹配冻结记录。

实际计数仍为**1 forward／0 full loss／0 backward／0 step**。五个事件严格对应S-ref参数分类、调用前claim、坐标消费者诊断、S-ref阶段完成及恢复；没有RF阶段forward或loss事件。

本次有一项明确的进展：**v2的双调用采集在S-ref原生forward中通过了六项逐消费者比较，最大绝对差均为0。** query-MLP、decoder query、第一次query位置编码、第二次Memory位置编码、FC条件和dense中心均按角色精确匹配，位置编码调用次数为2。这是该阶段的运行证据，不能扩大为两RF臂已通过。

日志记录S-ref参数未变，eval RNG一致，状态／模式／BN动量恢复和梯度清理均为true；审计没有重新加载模型复演恢复。资源样本阈值独立重算全部通过，记录峰值RSS1,603,473,408字节、SMI719MiB、torch allocated245,335,552字节、reserved283,115,520字节。监测样本不能当作连续峰值保证。

## 3. 初始化合同核查

实际加载器按以下顺序执行：

```mermaid
flowchart LR
    accTitle: 冻结初始化加载中的额外约束
    accDescr: 文件字节、哈希、布局与零输出层校验通过，之后额外的运行时种子重生成逐位比较失败。
    bytes_ok[大小与SHA256匹配] --> layout_ok[FP32布局 有限性 零输出层]
    layout_ok --> regenerate[当前环境重新生成随机值]
    regenerate --> equal_test[要求逐位相同]
    equal_test --> stopped[本次停止]
```

`load_initialization()`先检查大小、整个文件SHA256、固定布局、有限性及零输出层，随后才执行`expected=initialization_values()`和`torch.equal`。首错为`RF fixed private-seed values`，与上述顺序一致。错误发生在RF构造函数将加载结果传入`load_state_dict`之前，尚未进入RF forward。

标准库逐块解析结果如下，不调用加载器或随机数函数：

| 参数块 | shape | FP32元素数 | 字节校验与内容 |
|---|---|---:|---|
| V1.weight | 128×1802 | 230,656 | 分块SHA256匹配，全部有限 |
| V1.bias | 128 | 128 | 分块SHA256匹配，全部有限 |
| V2.weight | 3×128 | 384 | 分块SHA256匹配，全部为零 |
| V2.bias | 3 | 3 | 分块SHA256匹配，全部为零 |

生成清单和既有CPU验证记录的PyTorch版本为2.5.1；实际执行入口已检查的版本合同为2.4.1+cu118。这两份记录不同，但本次未保存生成数组的差异张量、逐块误差、运行时默认dtype／device或CPU派发信息。因此，**不能把“环境版本不同”直接写成唯一且已实测的根因**，也不能声称只是一个ULP或只影响V1某一项。

可以确认的是：冻结字节已经满足已绑定的文件与结构合同，加载器却额外要求当前环境用seed重新生成的值逐位相同。这是比“加载同一份冻结初始化”更强、且本次失败的运行时约束。没有证据要求重新生成或替换已验证的冻结文件。

## 4. 次级退出错误

日志同时保存了退出时的`KeyError`与`Original exception was`下的原始首错；`failure.json`明确保留首错为`RF fixed private-seed values`。精确读取守卫在finally中关闭fd后，Python格式化traceback的linecache再次读取已绑定源码，触发次级错误。它发生在原始失败之后，不能替代首错，也不解释初始化数值为何不同。本轮只记录这一退出证据，没有修复或扩展通用守卫。

## 5. 建议的最小后续范围

下一次如授权实施，应只修订初始化加载合同：**继续以冻结二进制为唯一权威**，保留大小／SHA256、固定布局、FP32、有限性及零输出层检查；将seed保留为生成来源记录，不在运行加载时重新生成并要求跨环境逐位相同。不更换初始化、不改模型数学公式、provider、数值阈值或5／4／4／0预算。

针对性CPU回归应证明：相同冻结文件加载结果一致；损坏字节、错误哈希／大小、非法布局或非零输出层仍被拒绝；加载不调用随机值重生成函数、不消耗共有RNG。通过新P3后，再创建绑定新加载器哈希的新request。本次不实施、不创建request或重跑。

## 6. 证据索引

- [正式冻结审计JSON](formal_failure_freeze_audit_v1.json)
- [初始化字节与校验合同JSON](initialization_byte_contract_findings_v1.json)
- [实际失败记录](downloads/output/failure.json)
- [实际加载器源码](downloads/related/0_bcsp_scq_rf_residual_v1.py)
- [服务器初始化来源清单](downloads/related/3_rf_initialization_manifest_v1.json)

这些证据保存于本机项目内，未修改服务器文件，也不构成训练授权或RF科研效果结论。
