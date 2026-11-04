# 欧氏／图距离 Fold C：图距离臂正式冻结审计与两臂配对核验

日期：2026-11-04。结论：**FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS，49/49项全部通过。** 两个既定运行已完成训练及各自正式冻结审计；尚未进行本对照的开发集预测或评分。

## 执行范围

本次仅通过WSL＋hpc5000执行一次有界stdlib只读审计，服务器写入0，模型导入0，forward0；未反序列化checkpoint或NPZ、未恢复模型、未重训、未进入BNCal或开发评价。总流式哈希读取464,135,253 bytes。继续采用120秒、768MiB总读取、512MiB单checkpoint、512文件预算，以及既定Python二进制精确17,331,920 bytes／SHA256例外。

## 完成计数及执行证据

| 项目 | 图距离臂核验结果 | 与欧氏臂关系 |
|---|---|---|
| 退出码及存活状态 | 0，固定tmux与worker已退出 | 两臂均正常退出 |
| 输入／输出 | 8192／8192 | 一致 |
| 来源／训练病例 | 63／315 | 一致，开发来源互斥 |
| optimizer更新／遍历 | 3900／100 | 一致 |
| 曝光／丢弃 | 31200／300 | 逐病例、逐来源及drop集合一致 |
| metrics记录 | 3900 | 全部step、epoch、batch、病例／来源顺序、LR、BN momentum、clip与提交标记一致 |
| resources记录 | 3902 | 各自原阈值与顺序全部通过 |
| forward／backward／clip／step | 各3900 | completion与冻结runtime交叉支持 |
| LR／BN调度调用 | 各100 | 一致 |
| BNCal／evaluation／resume | 均false | 一致 |

逐条读取3900个metric事件，检查有限loss／梯度、loss分项求和、学习率和BN momentum公式；重建曝光及丢弃计数并对照exposure.json。两臂的loss、梯度和最终权重允许不同，不将其要求相等。

## 实测checkpoint与产物清单

图距离臂路径：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_blue_noise_ab_v1/bcsp_blue_noise_foldC_surface_graph_in8192_out8192_seed0_train_v1/ckpt-last.pth`。

大小：**380,368,111 bytes**。本次独立流式实测SHA256，与completion一致：

```text
19bb53f61ef618ad1eca9b5acc45dae1ec1d6f3f56f6c97bca0098b1c20f216a
```

欧氏臂沿用此前正式实测SHA256 `f2ec18c5f3e6ded420f5c3026e1a0046346589121b354225c9b9b39ac789e624`，本次确认大小、inode和mtime_ns仍匹配此前冻结记录，并检查审计期间属性稳定；没有再次读取整份欧氏权重或声称重算了该哈希。欧氏臂所有非权重输出重新读取／哈希并与此前正式冻结清单匹配。

图距离结果目录精确为11个文件及一个空tmp目录，无failure／startup_failure。7个控制文件与冻结材料化预期大小／SHA256匹配，授权→runtime单向绑定和唯一attempt标记均通过。所有哈希文件与结果树内容相关属性前后稳定，排除atime干扰。

| 图距离臂输出文件 | bytes | SHA256 |
|---|---:|---|
| ckpt-last.pth | 380368111 | 19bb53f61ef618ad1eca9b5acc45dae1ec1d6f3f56f6c97bca0098b1c20f216a |
| completion.json | 559 | 7caa347a3bcd1ce8d36c7ed5e564db380709b42bdb82bf7226cc5fee17a5e8ec |
| exit_code.txt | 2 | 9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa |
| exposure.json | 19465 | 1203296e9aed5f177fe51b2278703828f3c14ed7d10a7f379ea39208e52dfb42 |
| initialization.json | 289 | e8315461977374d067343282e03757c1bc7c6fcf6edc60256af8376c46fd6b07 |
| launch.log | 1242 | f59ca4c58e2e5503369a09e8d485e1a5d22bdb70a298883d2b2b3b354b7483de |
| metrics.jsonl | 2568096 | d5cdd18c756e96c47a03f8a645333f6c767985118944f013f6c95009c809e229 |
| optimizer_actual_defaults.json | 223 | 9d63cc1e4fb32d46c348688146a9e8b10356a7bc3e8c1eabb9c483bac7c6e592 |
| order_plan.json | 1248506 | 6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d |
| resources.jsonl | 2867917 | a2401f12c78bd165031d140d2201c1e3ef1ca240b081606bf45a12ae89857fb9 |
| worker.pid | 6 | 7e0bd931dcf260398557bcbd2ce31b86314f61b184514c4c27a2d465d034b2dd |

## 配对一致性

两个运行的模型、entry／contract／runtime／helper、环境身份、PointNet2 provider、cdist后端、静态配置、固定fold来源、order文件和资源预算绑定一致。30个固定模型／provider／环境资产重新按大小与SHA256核验通过。实际optimizer默认记录一致；分组衰减等行为依赖同一冻结runtime，不把defaults中的weight_decay=0.01误认为所有参数组最终值。

初始化seed0，参数指纹 `c864e2f77fc7c5999cf1df615ed720f4fc10ae0a6d19888e28e5058879f70a99`，持久buffer指纹 `9649b96c1f1287fa7d5670815b3e48798ab1a3883bb200f5a9db027980852f37`；两臂记录完全相同，并匹配图距离请求中的欧氏冻结证据。顺序canonical SHA256 `349189dcada4c41b9e6b0152fa24695b2c71ce5fce4144865247d03c445f795f`。初始化由冻结运行入口在首更新前比较，本次复核保存记录；未独立重建初始模型权重。

全部3900条实际批次序列与LR／BN／clip／提交标记一致；case、source及dropped_case计数完全一致。配对目标数组哈希、D-only归一化及共同点序元数据一致。315份图距离训练NPZ重新逐文件流式哈希，与冻结manifest一致；未解码这些NPZ或再次计算其中的目标数组哈希，目标一致性依赖此前实际数据QC及本次文件身份与元数据绑定。

## 资源与科研解释

记录峰值：allocated 12.30GiB，reserved 13.27GiB，设备SMI 14074MiB，RSS 1.18GiB，均在原预算内。PID命名空间差异继续仅诊断，不代表专属GPU或cgroup硬隔离。

图距离臂训练loss首批 0.842774，末批 0.037854，最后一遍历均值 0.040012。这些是训练量，不据此判断欧氏或图距离采样胜负。计数由固定runtime、completion和日志交叉支持，没有独立GPU trace；BNCal/evaluation未执行同样不是全系统文件访问追踪结论。

## 下一阶段

训练配对核验通过后，可单独准备两臂Fold C开发集配对评价request：每臂105病例、共210次预测，同一GT和指标，使用最终native权重，不自动BNCal／TTA或追加训练。主要回答未知表面补全与接口吻合是否改善，按来源等权汇总；单fold、单seed探索对照不构成最终泛化或显著性结论。本次没有创建或执行评价内容。

图距离机器可读审计SHA256：`1fdcd9fc35a4f000f0848b211d2bd888f83ac0dbe6c7700c2de30411c5c29539`。欧氏父审计SHA256：`4fad73d8458e5788b6cfb23113a84f98601f45cc8b47c7827ac9ffe2a44cb689`。
