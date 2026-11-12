# F0 Fold D正式只读训练后冻结审计与C/D配对核验 v1

日期：2026-11-11（Asia/Shanghai）。**Fold D正式冻结审计通过，C/D训练配对合同核验通过，共53项检查。** 本次没有模型加载、checkpoint反序列化、新forward、重训、BNCal或评价。

## 产物身份与完整性

Fold D run：F0_foldD_seed0_train_20261110_v1；request SHA256 `ea45165142676c16b0c18e5616494ee78e1231970590ce4b314bf4c479bcd8b0`；容器n8xph5-0、UID1000。退出码0，固定tmux和worker PID均已退出，无失败产物。

流式哈希固定范围40个文件，共502893233 bytes：16个运行输出、18个冻结安装文件和6个控制文件；目录仅有tmp和control。D折采集前后SHA、大小、inode、mode及mtime/ctime完全一致，排除读取造成的atime干扰。32/39等旧数量没有沿用：本轮实际取回39个非checkpoint文件并逐个对照服务器清单。原payload_manifest的12项完整匹配。

原request、18文件运输映射、授权回执、单向runtime、唯一claim及launcher原字节均匹配。77条实际复用的非payload记录再次哈希匹配；本轮不重新读取NPZ数组。

## 最终checkpoint实测

C与D的ckpt-last.pth均为478810419 bytes。D折在两个清单快照中独立流式哈希，C折按原审计精确清单重新流式哈希；结果均与各自完成记录及冻结证据一致：

| Fold | SHA256 |
|---|---|
| C | `4fd73dd8c265781225ba63a712a5589b175c94f0ea0878a69ebf466265ebebe9` |
| D | `c4f29a8df3e36af2c87a20dc4888eb4b6a344bb448baa6403fb6c9c86023edaa` |

C折checkpoint及六项配对元数据的新哈希仍匹配原正式审计。没有下载权重或torch.load；未展开checkpoint内部模型/optimizer张量，本审计不能作为权重已在本机长期备份或可以删除服务器权重的确认。

## 完整计数、顺序与曝光

D折3900条metrics逐步验证：forward/backward/clip/optimizer step各3900，LR scheduler与BN scheduler各100；每批8、每遍39批、100 traversals。全部case/source批次严格匹配历史M0同折D的既定顺序，未用C折顺序替代。固定315训练例、63来源，与D折21个开发来源分离。

由所有批次和drop列表独立累计：31200次病例及来源曝光、300次drop，每病例“曝光＋drop”为100。对应exposure文件和completion一致；初始化/曝光/完成记录canonical order SHA一致。实际LR、BN momentum、clip10、有限loss/grad_norm及step提交标记逐条通过。

C折已冻结的相同计数保持。两折合计7800次更新、62400次曝光、600次drop；这不是独立患者数，两折使用同一已开放84来源的预注册折分，来源存在重叠，不视为两个独立队列或随机seed重复。

## 初始化与科学合同配对

完整初始参数SHA256两折相同：`2c7d4e3094a98834ed7e2627c610b8015d183146e10270db1a2dccc56c751d8e`。

完整初始persistent state SHA256两折相同：`beabbeb8c06c387d6ac54c3ec1825fbe7cd6bd529428c4f79299a5525cef301b`，并与原native GPU准入初始模型一致。实际完整factory构造证明、参数总量及encoder/decoder/other划分一致；scratch、seed0及固定私有初始化流未改变，D折没有从C折训练后checkpoint warmstart。

C/D两折实际AdamW defaults和411条参数分组逐项相等：39,903,169参数，encoder9,929,472、decoder21,356,160、other8,617,537。22个A_log和22个D保留no-decay；实际各组weight_decay为0/0.0005。defaults中0.01是已被每组显式覆盖的构造器默认值，不误作实际衰减。

模型、loss、runtime、point count、资源及数值政策相同；分派入口仅按授权折分与证据绑定做差异。C/D的order SHA分别为 `6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d` 和 `4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720`，有意不同。相同的是训练策略与初始化，病例顺序各自对齐相应M0基线，不要求跨折case列表相同。

## F0几何与资源

D折F0_geometry.jsonl精确3900行，与metrics的每一步epoch/batch及8个case对应。coarse/dense质心、半径和min/max形状正确、数值有限，半径非负，质心与包围范围一致。坐标为D-only normalized，不是world-mm或临床接口精度；日志不替代Native预测评分。

3902条资源记录完整覆盖3900个after_step、before_final及after_final，所有GPU条件从实际值独立重算一致；RSS、输出和wall范围均通过。D折采样RSS峰值约1.554GiB，Torch allocated约12.932GiB、reserved约13.785GiB，SMI最高14604MiB。completion生命周期计时约25.47分钟，不与旧设备基线据此宣称速度优势。

维持原采样监测局限：没有专属硬cgroup保证；PID命名空间差异仅诊断，不声明GPU所有权。最小磁盘空间由固定local guard执行，资源行无逐条free-disk字段，不虚构该遥测。attention-free固定模块/源码准入被继承，本次不重新逐kernel审查3900步的opaque扩展内部。

## 冻结结论与下一步

两折BNCal/evaluation/resume均为false；模型梯度的有限非位级确定性披露保留。训练后checkpoint不同符合不同折训练的事实，不要求训练后权重或loss相同。

本机保存完整D折审计与C/D配对证明，机器文件为post_training_freeze_audit_result_v1.json和C_D_pairing_freeze_receipt_v1.json。Fold C复核原始记录见counterpart_stdout_v1.bin。两折服务器权重继续保留。

下一步应核对F0预测入口兼容性，按原计划准备每折105例、共210次Native开发集预测的待授权范围；复用既有T0/M0预测参照，不调参、筛病例或重复训练/preflight。不自动运行预测、BNCal、评分或额外机制forward；尚不能从训练loss判断补全精度或接口吻合是否改善。
