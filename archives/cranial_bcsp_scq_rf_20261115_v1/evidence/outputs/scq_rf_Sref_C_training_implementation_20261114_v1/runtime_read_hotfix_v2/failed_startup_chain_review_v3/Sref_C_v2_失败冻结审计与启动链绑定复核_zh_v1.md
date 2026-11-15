# SCQ-RF S-ref_C v2 失败冻结审计与同启动链读取绑定复核

日期：2026-11-14。范围：正式只读失败冻结审计，以及当前唯一训练启动链的有限源码复核。

## 1. 结论

**失败证据冻结核验通过；训练没有通过启动。** 24项核验通过，34个文件共3,106,280字节在采集前后内容和内容相关属性一致。服务器采集耗时3.891秒；只读取冻结源码、初始化载体和失败证据，没有读取真实NPZ数组、加载checkpoint、执行模型或重试训练。

当前容器：`shu-common-25721452-notebook-zbpgzu-0`，UID1000。退出码1，固定tmux会话不存在，原worker PID10974对应训练进程不再存活。输出仅有`startup_failure.json`、`launch.log`、`exit_code.txt`、`worker.pid`及空的`tmp`目录；没有训练指标、初始化记录、顺序记录、完成文件或checkpoint。

结合首错发生位置可确认：模型构造和训练dispatch尚未到达，训练更新为0。原尝试已执行CUDA可用性和设备检查，因此不能把“未做模型forward”写成“整个尝试没有触及CUDA”。本次审计没有创建CUDA上下文。

已消耗的v2 request：

`b387a08bd2de575723d8f89a6f0c7fb1665590108eed0ef62c00d28b8394d4f1`

**不得复用、resume或自动重试。** 本次不创建新request、不修改生产实现、不运行CPU契约测试，也不重复已通过的GPU准入。

## 2. 证据完整性

- 7个安装payload与冻结映射一致；加4个control，共11个安装文件。
- 授权回执、runtime控制文件、launcher与本机已授权材料逐字节一致；request完整哈希、单向回执绑定及单次claim一致。
- 14个复用实现源码、原SCQ初始化载体，共15个相关文件，大小及SHA256全部符合request。
- 上传压缩包及3个校验文件符合本机冻结副本。
- 4个输出文件与上述安装、相关文件构成30份下载证据；全部回读哈希符合服务器新测值。
- 清单前后比较不包含atime，避免读取本身造成误判；文件类型、路径链接和目录集合已核查。

第一次审计采集被辅助工具2 MiB单文件上限阻断，原因是原初始化载体2,784,780字节。该失败产物已保留。随后仅对此已冻结大小和哈希的初始化文件增加精确例外，仍保留40文件、8 MiB总量、60秒和其他文件上限；新版采集完成。这是审计采集问题，不是新的科研执行失败。

## 3. 首错与次级错误

### 3.1 首错：bridge源文件未被安装后的读取策略覆盖

入口在安装audit hook后，依次加载6个模型源码，再执行同一行中的`factory → bridge → runtime`。

v2已把原runtime加入精确读取守卫，但bridge仍位于旧v1目录，而当前entryroot为新v2目录。request中绑定了bridge大小与哈希，只能证明授权资产身份；它不会自动赋予audit hook安装后的读取权限。

`source_module`首先调用`exact`并读取源码计算哈希。此处被读取边界拦截，尚未执行bridge代码，也尚未执行后面的runtime加载。本次bridge本身大小与哈希正确，未发现资产损坏。

### 3.2 次级错误：异常回溯重读旧budget源码

`launch.log`在`Original exception was:`之前还记录了旧`inherited_training_budget_v1.py`读取被拒绝。它属于打印异常时读取栈帧源码的次级失败；首个结构化`startup_failure.json`明确指向bridge，不能把budget误认成训练资源超限或最初根因。

这说明“在hook前已加载”不等于“hook后永远不再读源码”：异常回溯也可能触发精确源码读取。同链其他预载辅助源码应一起明确处理，避免再次只补首个文件。

## 4. 有限读取链清单

本轮穷举当前request中的15个implementation记录，加原初始化载体，共16条绑定；没有扩展到通用环境库存。完整路径、字节数、SHA256与分类见同目录JSON/CSV。下表区分正常路径与异常回溯路径。

|记录|实际用途|当前hook后覆盖|结论|
|---|---|---|---|
|encoder、factory、lqi_decoder、lqi_factory|正常模型源码加载|4条继承精确绑定|已覆盖|
|scq_residual、scq_factory|正常SCQ源码加载|2条额外精确绑定|已覆盖|
|initialization|SCQ构造读取冻结初始化|精确绑定|已覆盖|
|runtime|正常源码加载；bridge再次读取其文件核对哈希|v2新增精确绑定|已覆盖；本次正常流程尚未到达该加载点|
|bridge|正常源码加载|不在既有根目录或精确绑定中|本次首错，必须补齐|
|budget_parent|hook前加载；hook后执行资源逻辑；异常时重读源码|源码文件不在hook后读取范围|日志确认次级缺口|
|timezone、contract、native_helper、cuda_entry|hook前加载；可能在异常栈中重读其源码|源码文件不在hook后读取范围|有限链潜在诊断读取缺口，不是已观察到的正常加载首错|
|entry|当前进程入口及异常栈源码|当前entryroot|已覆盖|
|preflight_helper|hook前加载及项目导入策略|既有model_root|已覆盖|

以下路线按既有代码和冻结范围核对，不要求新增目录放行：

1. 授权材料、静态配置、QC、顺序及CUDA准入证据在hook前读取。不能因这些文件位于旧目录就放开整个目录。
2. 母版forward源码通过`original.__code__.co_filename`读取并核验固定哈希，走已冻结model_root；base_model.yaml、项目adapter和有限项目导入也沿用该范围。
3. 原训练contract在authorize阶段以固定模块名预载；runtime导入同名模块使用已有模块，不需要重读另一份未绑定contract。
4. bridge对`parent_runtime.__file__`的再哈希仍是同一个已绑定runtime路径。
5. provider与环境依赖保持既有冻结scope、版本和读取根；不更换后端、不安装或升级环境。
6. 真实训练NPZ保持315份精确allowlist；产物保持当前run拥有的路径与最终checkpoint规则。

**边界：** 这是当前有限启动源码链的静态复核和本次失败证据核验，不是所有未来第三方惰性导入的执行证明；不能承诺修订后训练必然成功。

## 5. 现有CPU验证为何漏检

v2子进程回归确实在真实读取策略下执行了原runtime的源码加载，也验证了模型源码及初始化读取；但未在相同策略下加载bridge。外层bridge验证使用spy/delegate，因此没有覆盖“新entry目录＋旧bridge目录”的实际部署关系。

问题是集成验证切面不完整，并非CPU数值测试失效。36项通过不等于真实完整启动链通过；先前GPU零更新通过也不会自动覆盖新训练bridge的文件权限。

## 6. 建议下一次限定实施一次性收尾

**本节只是建议，尚未实施或创建request。**

1. 将当前request已冻结的implementation源码记录统一纳入现有精确只读守卫，连同原初始化；按路径去重，冲突拒绝。总集合只有本表16条，保留逐文件大小、SHA256、链接与禁止写入校验；不增加目录根，不放行相邻文件，不另建库存框架。
2. 这样同时覆盖正常bridge加载，以及已加载辅助源码的异常回溯。资源、数据、payload、秘密、checkpoint和输出写入边界均保持不变。
3. 一批人工CPU回归按实际新旧目录关系安装策略，依次走真实`source_module`的模型源码、factory、bridge、runtime加载，并覆盖bridge对原runtime的再哈希。加载测试不实例化真实模型或使用真实数据。
4. 同批回归覆盖：故意抛错后可打印包含budget等旧目录源码的原始异常；绑定源码写入拒绝、哈希/大小漂移拒绝、未绑定相邻文件拒绝、非授权NPZ拒绝。明确区分首错与次级错误。
5. 静态复核与限定CPU验证通过后完成新P3，再创建全新输出路径和单次claim的新待授权request。失败即停，不自动修补重跑。

无需修改模型、初始化字节、provider、loss、显存阈值或3900-step合同；无需重复GPU准入。应把这次工作限制在短入口的精确读取集合与真实启动顺序回归，避免再按首个报错逐文件试跑。

## 7. 科研解释

当前没有S-ref_C训练结果，不能据此评价SCQ-RF是否有效。失败发生在模型构造和优化之前，既不能说明模型、Mamba梯度、数据或loss有问题，也不能证明这些后续执行一定无误。科学合同仍为8k→8k、3900更新、31,200曝光、300丢弃事件；本次未改变任何科研设置。

## 8. 证据文件

- `freeze_verification_v2.json`：正式冻结审计，24项核验及34文件清单。
- `startup_read_binding_matrix_v2.json` / `.csv`：16条精确读取绑定、路径、大小、完整SHA256及覆盖分类。
- `downloads/output/`：结构化首错、原始日志、退出码、PID。
- `inventory_before_result_v1.json` / `inventory_after_result_v1.json`：稳定性证据。
- `collection_complete_v1.json`：只读采集耗时与操作边界。

先前v1矩阵中覆盖根的通用标签已在v2明确为existing_read_root；最终引用本报告列出的v2审计与矩阵，原始版本保留，不覆盖历史证据。

## 附录：关键路径与完整哈希

- **bridge**：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/bcsp_scq_rf_training_bridge_v1.py`；703字节；SHA256：`9f282d1ce07e9c89ba7cac246d99c2c9f0ac2086f1f5de80151ae2a73723c6dd`。
- **runtime**：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/bcsp_p1_training_runtime_v1.py`；11268字节；SHA256：`939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee`。
- **budget_parent**：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/inherited_training_budget_v1.py`；20395字节；SHA256：`095cabb0ab9b098172840432d40699dd18279671cf650894fab9eb9b54575ebe`。
- **initialization**：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/initialization_v1.bin`；2784780字节；SHA256：`e7858ee3ae4c0bf6d68e447727c36514f5bbab42b95e1935f1686620ec089416`。
