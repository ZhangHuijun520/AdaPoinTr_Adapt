# SPCG G2_D 正式只读训练后冻结审计及G1_D／G2_D配对核验

2026-11-17。结论：`FORMAL_SPCG_G2_D_POST_TRAINING_FREEZE_PASS`，机器可读审计结果全部检查通过。

## 范围与身份

当前容器yxwd3w-0。request完整SHA256：`2885c64fca8717e16a57bdaac2ad5bbf6290b36539d893893d4ef161a0e807b9`。

本次仅只读服务器冻结文件和日志，并在本机保存证据。checkpoint仅流式读取原始字节计算哈希；服务器写入、checkpoint反序列化、模型调用及GPU执行均为零。未启动评价、BNCal或后续实验。

## 完成与产物

| 项目 | 核验结果 |
| --- | --- |
| 退出码／进程 | 0；worker和固定tmux均已退出 |
| forward／backward／clip／optimizer step | 各3900次 |
| 完整遍历／曝光／drop | 100／31200／300 |
| metrics／SPCG geometry／resources | 3900／3900／3902条 |
| 耗时 | 1527.555秒，约25分28秒 |
| checkpoint大小 | 478923818 bytes |
| BNCal／evaluation／resume | 均为false |

checkpoint路径：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G2_foldD_seed0_train_20261117_v1/ckpt-last.pth`

本次重新实测SHA256：

`61aec7309b20a67bb0db74dcec7a78d3148265e80fd04fff6699ca0d459ededb`

与completion和manifest一致。产物精确集合、文件大小和哈希、manifest唯一性、空tmp目录、11个安装文件、复用implementation哈希均符合冻结记录。授权回执、单向runtime绑定与单次claim通过核验。

## 核心配对合同

G1_D／G2_D两组启动阶段已保存的实测GPU记录均为 `GPU-4b19574a-832d-b4fe-e655-a57462954d6a`，驱动均为570.190，与request身份相同。该核验使用已有启动观测，不在审计中重新执行GPU计算。两组hostname、环境、GPU选择器及资源合同一致。

两组初始化记录完全一致，包括seed、参数指纹、persistent-state和order指纹；与准入一致的完整raw-state指纹为 `3cfdbac9149b99e24ea6641fb9e00cf975754ad21c7a88fc6d34e17e01724ab9`。相同scratch母版与U/H字节，不加载已训练G1_D权重。初始化身份依据冻结源码、运行时构建断言和准入证据，本次未重新构建模型或读取checkpoint张量。

两组全部3900条metrics按step、epoch、batch、case_ids、source_ids、LR、BN momentum及clip阈值逐条相同。order_plan字节完全一致，完整exposure字典相同。实际曝光31200次、drop300次与100轮冻结计划相符。

D折order原始SHA256为 `4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720`，canonical order指纹在初始化、completion和exposure之间一致。G1_D既有metrics、初始化、顺序、曝光、构建及优化器证据重新计算哈希后未改变。

优化器默认值及逐参数分组完全一致，数据根、static config、counts、science、U/H、母版源码和共同G0 scratch初态绑定相同。G2原head已删除，只替换首次coarse生成的一个表达式，head1845763参数、净增8963。G0_D及G1_D冻结凭据当前哈希均符合request，G1_D request绑定一致。

## 几何、数值与资源

全部3900条SPCG几何日志与metrics及order逐步对应，坐标口径为D-only normalized，coarse/dense中心与半径、coarse_CD/dense_CD无非有限数值。loss加和按实际FP32舍入口径验证，未改loss定义。指定step 1、39、390、1950、3900总loss Q梯度记录完整，L2有限且大于零；不能据此推断接口几何或coarse监督的独立贡献。

所有3902条资源记录守卫通过。峰值RSS1669283840 bytes，Torch allocated13930625536 bytes、reserved14810087424 bytes，SMI显存14612 MiB。两组启动阈值6GiB、运行期间4GiB下限及原1GiB输出上限一致。PID口径差异仍按既有诊断性合同披露，不声称认证GPU进程所有权。

## 科研解释边界与下一步

G1_D／G2_D满足本次核心同设备、同初态和同顺序训练合同，但有限梯度非确定性仍存在。**G0_D仍为跨设备参照**，不能把三臂全部描述为严格同设备对照。

至此，依既有分别冻结的证据，G0/G1/G2 × C/D六组预定训练均已完成各自正式冻结；本次没有另行执行六运行整体完整性审计或比较性能。训练loss不能代替开发集补全精度、接口吻合和风险评价。

下一步核对六模型Native预测入口及冻结资产兼容性，再准备每模型105例、合计630次预测的待授权范围；不按训练loss调参、筛病例、追加训练或自动进入BNCal。本次未创建预测request或运行forward。

同目录保存正式结果JSON、五阶段只读脚本、原始stdout/stderr、各阶段结构化证据及本机SHA256清单。
