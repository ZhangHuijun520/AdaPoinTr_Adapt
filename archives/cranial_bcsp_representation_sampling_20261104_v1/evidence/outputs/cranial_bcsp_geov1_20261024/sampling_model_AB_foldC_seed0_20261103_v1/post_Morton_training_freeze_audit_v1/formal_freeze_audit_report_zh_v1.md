# Fold C Morton 8k：正式只读训练后冻结审计 v1

## 结论

**通过，45/45 项检查全部为 true。** 候选臂与已审计 V1 组满足本次单折、单 seed 的训练配对合同；尚不能据此判断采样方案是否提高预测质量。

## 授权与执行边界

用户单独授权正式只读训练后冻结审计。通过既有 WSL＋hpc5000 短入口执行一次 stdlib 只读核验，不修改服务器文件，不导入模型、不运行 forward，不加载 checkpoint／NPZ 内容为张量，不重训、不进入评价或 BNCal。

本次流式哈希共读取 464,000,387 bytes，服务器审计耗时 0.905 秒。保留既有 120 秒、768 MiB 总读取、512 MiB 单 checkpoint、512 文件上限与精确 Python 二进制大小／哈希例外，未放宽通用守卫。

## 完成状态与计数

| 项目 | 核验值 |
|---|---|
| 退出码／存活状态 | 0；固定 tmux 不存在，worker 已退出 |
| 更新／完整遍历 | 3900／100 |
| 病例曝光／drop_last 丢弃 | 31200／300 |
| 实际 metric／resource 记录 | 3900／3902 |
| forward／backward／clip／optimizer step | 各3900 |
| LR scheduler／BN scheduler | 各100 |
| BNCal／evaluation／resume | 均 false |

完整扫描3900条记录，核对每条 epoch、batch、病例／来源顺序、更新提交、有限 loss／梯度、LR 及 BN momentum；重建并核对病例、来源及丢弃计数。3902条资源记录的顺序、阈值与通过状态均核验通过。

## 实测 checkpoint 与产物清单

路径：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_sampling_ab_v1/bcsp_sampling_ab_foldC_Morton_in8192_out8192_seed0_train_v1/ckpt-last.pth`

大小：**380,368,111 bytes**。本次独立流式实测 SHA256，与 completion 一致：

`2c27034cda17ee55f6724bf14d53ba305ba2410531cf23a4c694dafdec1cbb84`

输出目录精确为11个文件和一个空 tmp 目录，无 failure/startup_failure 标记；7个控制文件与授权材料化预期一致。授权／runtime 保持单向绑定。读取前后内容相关属性稳定，排除 atime 影响。

| 输出文件 | bytes | SHA256 |
|---|---|
| ckpt-last.pth | 380368111 | 2c27034cda17ee55f6724bf14d53ba305ba2410531cf23a4c694dafdec1cbb84 |
| completion.json | 555 | 5895cdc82df3a01279c5f39848b0fc6bb4770305c8e637aaa4201c451e0908a4 |
| exit_code.txt | 2 | 9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa |
| exposure.json | 19465 | 1203296e9aed5f177fe51b2278703828f3c14ed7d10a7f379ea39208e52dfb42 |
| initialization.json | 289 | e8315461977374d067343282e03757c1bc7c6fcf6edc60256af8376c46fd6b07 |
| launch.log | 1242 | 9b9c62f67e73b00919f3d9d51a2c7c77e0a0cce79b1ef4efa5f18aaf438ee4a5 |
| metrics.jsonl | 2567435 | 4a6e8a0ec6eb56231933fc418a0c042639792d9ebbe89db16df2b0a28b71eef6 |
| optimizer_actual_defaults.json | 223 | 9d63cc1e4fb32d46c348688146a9e8b10356a7bc3e8c1eabb9c483bac7c6e592 |
| order_plan.json | 1248506 | 6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d |
| resources.jsonl | 2867914 | 3b81f24bd919f539c4c7651ff76ef95bb6f8a993f9a072d47769cbe11e7ea2f9 |
| worker.pid | 6 | 48e6745f1df4b60156762fa262616a8fdc6b7d5d479a9e0fcc558127a7f11dcb |

## 与 V1 的配对一致性

重新哈希 V1 的训练日志、初始化、曝光、顺序、完成记录等非权重产物，并匹配其先前正式冻结审计。两个运行的模型／实现哈希、环境身份、配置、固定训练来源、GT／归一化框架／共同点顺序、完整批次顺序、LR／BN 序列、优化器默认参数、更新与曝光计数一致。候选315个NPZ逐文件哈希与冻结manifest一致。两臂允许的差异是输入采样方案；loss 与最终权重不要求相等。

初始参数指纹：`c864e2f77fc7c5999cf1df615ed720f4fc10ae0a6d19888e28e5058879f70a99`

初始持久状态指纹：`9649b96c1f1287fa7d5670815b3e48798ab1a3883bb200f5a9db027980852f37`

两者均与 V1 初始化记录完全相同；seed为0。实际批次顺序 canonical SHA256：`349189dcada4c41b9e6b0152fa24695b2c71ce5fce4144865247d03c445f795f`。

V1 checkpoint 本次不重复流式哈希，使用此前正式审计的实测哈希，并只读确认当前文件大小、inode 与 mtime_ns 未改变；候选 checkpoint 已在本次完整流式实测。未反序列化或重建初始权重。

## 资源与解释限制

候选记录峰值：torch allocated 13,206,299,648 bytes、reserved 14,248,050,688 bytes，SMI 14074 MiB，RSS 1,264,517,120 bytes；全部在冻结预算内。SMI PID 与容器 PID 的差异按既定合同仅诊断，不保证硬隔离或GPU独占。

步骤及 forward/backward 等计数由冻结实现与保存记录交叉支持，未采集独立GPU trace。BNCal/evaluation未执行由冻结路径及记录支持，未开展全系统文件访问追踪。训练 loss 不是开发集指标，不用于宣布候选胜出。

## 下一步

本次到此结束。下一科研步骤是对 V1 与 Morton 两臂进行同一 Fold C 开发集配对评价，使用共同 GT 和指标回答未知表面与接口吻合是否改善；先单独冻结评价合同并创建待授权 request，不自动启动预测、BNCal 或追加训练。

机器可读审计报告 SHA256：`095149d2a3278b16c70d285640c75881e1f56d1fc518c41a6630b3b48390bb90`。
