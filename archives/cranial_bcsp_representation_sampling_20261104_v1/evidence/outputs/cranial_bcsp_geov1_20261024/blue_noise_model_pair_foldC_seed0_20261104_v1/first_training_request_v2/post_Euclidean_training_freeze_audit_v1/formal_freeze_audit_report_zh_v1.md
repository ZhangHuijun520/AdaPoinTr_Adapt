# Fold C 欧氏距离采样臂：正式只读训练后冻结审计 v1

日期：2026-11-04。结论：**FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS，39/39项全部通过。**

本次使用既有WSL＋hpc5000短入口进行一次独立只读审计。没有写服务器、反序列化checkpoint、重建模型、读取NPZ为张量、运行forward、重训、BNCal或开发评价。审计流式哈希读取共457,419,802 bytes；保留120秒、768MiB总读取、512MiB checkpoint、512文件上限。精确Python二进制仅按原冻结17,331,920 bytes及既有SHA256例外校验，未扩大普通文件上限。

## 计数、顺序及执行状态

| 项目 | 实测／核对结果 |
|---|---|
| 退出码、tmux、worker | 0；会话及worker均已退出 |
| 更新／遍历 | 3900／100 |
| 病例曝光／drop_last丢弃 | 31200／300 |
| 完整metrics／resources记录 | 3900／3902 |
| forward／backward／clip／optimizer step | 各3900，completion与冻结runtime交叉支持 |
| LR scheduler／BN scheduler | 各100 |
| BNCal／evaluation／resume | 均false |

逐条核对3900条实际日志中的step、epoch、batch、病例与来源顺序、optimizer提交、有限loss和梯度、LR与BN momentum；从实际批次重建case/source/drop曝光计数并匹配exposure.json。运行order_plan与冻结文件逐字节相同，canonical哈希与初始化、曝光及completion一致。

## Checkpoint及冻结清单

路径：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_blue_noise_ab_v1/bcsp_blue_noise_foldC_Euclidean_elimination_in8192_out8192_seed0_train_v1/ckpt-last.pth`。

大小：**380,368,111 bytes**。本次独立流式实测SHA256，匹配completion：

```text
f2ec18c5f3e6ded420f5c3026e1a0046346589121b354225c9b9b39ac789e624
```

结果目录精确包含11个文件和一个空tmp目录，无failure/startup_failure。5个控制文件与授权材料化预期大小／哈希一致，授权→runtime保持单向绑定，single-attempt marker匹配完整scope及inner request。全部读取文件及结果树的内容相关属性前后稳定，atime不参与判定。

| 输出文件 | bytes | SHA256 |
|---|---:|---|
| ckpt-last.pth | 380368111 | f2ec18c5f3e6ded420f5c3026e1a0046346589121b354225c9b9b39ac789e624 |
| completion.json | 559 | d4857955bfcc8da2c73635cd33d158b417bf540ae229df2276cdb8d1e0d8847d |
| exit_code.txt | 2 | 9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa |
| exposure.json | 19465 | 1203296e9aed5f177fe51b2278703828f3c14ed7d10a7f379ea39208e52dfb42 |
| initialization.json | 289 | e8315461977374d067343282e03757c1bc7c6fcf6edc60256af8376c46fd6b07 |
| launch.log | 1242 | 3bca7dfcd4c005a2744616f101b90e71f83f0761363eff201d6ad7ec13b3e331 |
| metrics.jsonl | 2567974 | 93a471fbbc4238703477955e43f8b2bc5d7dd33374a3ffad6e3fb5aacb556ac6 |
| optimizer_actual_defaults.json | 223 | 9d63cc1e4fb32d46c348688146a9e8b10356a7bc3e8c1eabb9c483bac7c6e592 |
| order_plan.json | 1248506 | 6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d |
| resources.jsonl | 2867912 | 665822b9b8ef18effa9450279b6fda73ab5a7efebd5e074e1ff7e53e361d623c |
| worker.pid | 6 | d9c5bf47d4408c2a9e7c6db0daaf80f6fe3df5b488be0ed52305d63a923b2da3 |

## 初始化与训练来源

Scratch seed0；参数指纹 `c864e2f77fc7c5999cf1df615ed720f4fc10ae0a6d19888e28e5058879f70a99`，持久状态指纹 `9649b96c1f1287fa7d5670815b3e48798ab1a3883bb200f5a9db027980852f37`。记录与同源码、同配置、同seed0的既有已冻结参考一致，当前请求没有父权重。顺序canonical SHA256为 `349189dcada4c41b9e6b0152fa24695b2c71ce5fce4144865247d03c445f795f`。

本次验证的是绑定runtime保存的初始化记录及其一致性，没有通过重新构造模型独立恢复初始权重。后续图距离臂仍须在其首更新前比较同一参数／buffer指纹，不能把本次通过当作未来配对已经完成。

315个欧氏臂训练NPZ逐文件流式哈希与冻结manifest一致，未解码payload；63训练来源与21开发来源互斥。图距离臂仅核对既有配对元数据中的目标、归一化和共同点序，不读取该臂NPZ、不创建其执行内容。30个固定模型／provider／环境资产重新核验通过。优化器默认值按记录核验，实际分组weight_decay仍由已绑定runtime及合同支持；defaults中的0.01不代表各分组最终采用值。

## 资源与解释范围

3902条资源记录均符合顺序、阈值及停止合同。记录峰值：Torch allocated 12.30GiB、reserved 13.27GiB；SMI 14074MiB；RSS 1.18GiB。SMI PID与容器PID差异继续仅作诊断，不保证硬隔离或GPU独占。

训练loss：首批0.844093，末批0.036060，最后一遍历39批均值0.038218。这些是训练指标，不能据此判断采样方法的开发集收益。forward/backward等计数由冻结路径与日志交叉支持，没有独立GPU trace；BNCal/evaluation=false亦不等于进行了全系统文件访问追踪。

## 后续边界

本次仅冻结欧氏臂训练结果，不创建或启动图距离臂request。下一科研步骤可单独准备图距离臂的待授权request，复用既有点集，绑定本次初始化、同一环境、同一顺序与3900步合同；待两臂训练及独立审计完成后，再按阶段进行开发集配对评价。

机器可读审计报告SHA256：`4fad73d8458e5788b6cfb23113a84f98601f45cc8b47c7827ac9ffe2a44cb689`。
