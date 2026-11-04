# 首个fresh V1：正式只读训练后冻结审计报告 v2

日期：2026-11-03。状态：FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS，38项检查全部通过。审计未写服务器文件、未导入模型、未执行forward或训练；checkpoint仅流式哈希，未反序列化。

## 唯一修订与边界

v1失败由审计普通文件16MiB上限误用于Python二进制造成。v2只为精确路径/opt/conda/envs/adapointr-mamba/bin/python3.10增加冻结大小17,331,920 bytes及SHA256 01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d校验。当前文件大小与哈希均匹配。

其余审计源码字节保持原样，普通文件16MiB、checkpoint512MiB、总量768MiB、120秒监测预算、512精确文件与32输出树条目上限均未改变；无链接/普通文件、冻结hash、atime排除后的前后指纹守卫保留。原失败v1和诊断材料保留，不复用执行记录。本次一次新审计耗时1.034秒、流式哈希457,284,899 bytes。

## 退出、计数与顺序

- 退出码0，指定tmux已不存在，原worker已退出，无failure/startup_failure标记。
- 100遍，epoch标签0–99；3900条连续更新记录，forward/backward/clip/optimizer step各3900次，LR/BN调度各100次。
- 实际3900批的病例、source、step/epoch/batch与冻结计划逐条一致；loss/梯度有限、clip10、两组LR和BN momentum时序逐条符合固定公式。
- 63训练来源、315病例，与本折21开发来源无交叉。使用曝光31200，丢弃曝光300；实际病例/source/丢弃Counter逐项与exposure.json一致，不宣称每例恰好100次。
- 顺序文件字节SHA256：6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d。
- 顺序canonical SHA256：349189dcada4c41b9e6b0152fa24695b2c71ce5fce4144865247d03c445f795f。completion、exposure和初始化记录一致。
- 3902条资源记录阶段和step序列正确，所有记录的内存/RSS/时间/输出限额与判定通过。PID命名空间差异仅诊断，不作为独占证明。
- BNCal、evaluation和resume均为false，并由冻结执行路径佐证；没有新增OS级独立访问追踪。

## checkpoint与初始化证据

实测checkpoint：380,368,111 bytes。

实测SHA256：`bef638c807de8ea41f79862311138f42d9993dcc6fb5a09d5321642a57acfa51`，与completion中记录一致；读取前后文件指纹稳定。

初始化seed0，参数指纹：`c864e2f77fc7c5999cf1df615ed720f4fc10ae0a6d19888e28e5058879f70a99`。

持久状态指纹：`9649b96c1f1287fa7d5670815b3e48798ab1a3883bb200f5a9db027980852f37`。

初始化JSON本身的hash、seed、指纹格式及顺序绑定均核验。审计没有重新构建初始模型或独立恢复随机初始权重；它冻结的是原运行记录及来源链。候选臂会在第一步前把实际fresh模型参数/持久状态指纹与此证据比较，不加载基线final权重。

optimizer_actual_defaults中lr、betas、eps、amsgrad符合固定版本。其全局默认weight_decay为0.01；实际两组weight_decay由冻结runtime的make_optimizer显式设为0和0.0005，不能把defaults字段误解成实际组设置被改成0.01。本审计不反序列化optimizer checkpoint，参数组设置以冻结源码链佐证。

## 来源链、稳定性与候选就绪

控制目录五个文件与真实授权材料化哈希匹配，request→授权→runtime单向绑定正确，唯一启动标记对应此request。新任务stage为BCSP_SAMPLING_AB_V1。

模型、provider及精确30项资产哈希通过；全部已读取文件的最终指纹及结果树前后稳定，排除读取自身引起的atime变化。完整读取清单和属性见audit_report_v2.json。

候选315个已安装NPZ全部流式hash匹配冻结清单，两臂case/source/目标数组hash/归一化/共同点序元数据一致，未解码NPZ。候选control、output及tmux不存在，GPU UUID/名称/driver/总容量仍与基线绑定相同。它们是审计时快照，未来执行前必须刷新，不是持续准入。

## 完整训练产物清单

| 文件 | bytes | 实测SHA256 |
|---|---:|---|
| ckpt-last.pth | 380368111 | `bef638c807de8ea41f79862311138f42d9993dcc6fb5a09d5321642a57acfa51` |
| completion.json | 557 | `72647463a54606da02e766b73a4e02c2253bdf4578aa45a0526e7afff32f0a08` |
| exit_code.txt | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| exposure.json | 19465 | `1203296e9aed5f177fe51b2278703828f3c14ed7d10a7f379ea39208e52dfb42` |
| initialization.json | 289 | `e8315461977374d067343282e03757c1bc7c6fcf6edc60256af8376c46fd6b07` |
| launch.log | 1242 | `0c5552d0f6078f0fad0c997e6e7948f2b866ac96482d5a09a4a71614a0a29ca2` |
| metrics.jsonl | 2567555 | `203b22b2f231b5b003e6350490dc5ce5844397290b8fa6bb16e48aad93713824` |
| optimizer_actual_defaults.json | 223 | `9d63cc1e4fb32d46c348688146a9e8b10356a7bc3e8c1eabb9c483bac7c6e592` |
| order_plan.json | 1248506 | `6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d` |
| resources.jsonl | 2864003 | `8d01ef4c38865ae0abe00693385c28a236b4476800b7f6d00c6d09abe8af7827` |
| worker.pid | 5 | `081beba90804fa05b1f2f5fbb9398a328351bc756da7f92ac1484a2ca05e7e1d` |

## 后续边界

本次通过后仅在本机生成配对初始化凭据和候选臂待授权request；未创建真实候选授权回执、runtime或launcher，未写服务器、未启动候选/BNCal/evaluation。训练loss仅用于日志完整性，不解释为补全性能或临床精度。
