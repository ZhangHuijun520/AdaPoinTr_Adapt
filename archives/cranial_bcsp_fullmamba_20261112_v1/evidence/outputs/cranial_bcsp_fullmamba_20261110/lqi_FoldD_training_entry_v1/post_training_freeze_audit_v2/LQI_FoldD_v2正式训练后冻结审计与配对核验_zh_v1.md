# LQI Fold D v2正式训练后冻结审计及配对核验

日期：2026-11-11。结论：**训练后审计42项通过，同折F0D及跨折LQIC配对核验16项通过**。退出码0，worker和tmux均结束。旧v1启动失败证据继续保留，不能混入此次成功v2。

checkpoint：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldD_seed0_train_20261111_v2/ckpt-last.pth`。

大小：478,810,419bytes；两次独立原始字节SHA256一致：

`2afd1b4540b856d4c829786729d8c2df80943edd65a0f01af412940fd973e5ed`

完整清单为26文件，前后哈希及内容相关指纹一致；25个非权重文件已下载核验。v2仅新安装4文件及6控制凭据；其余13份准入/C折/参考证据复用旧安装，不伪装为v2新安装。77条绑定资产重新核验，复用证据本机镜像的大小及哈希也逐条与不可变request核对。未下载或反序列化checkpoint，未运行新forward、backward或测试，无服务器写入。

计数：3900更新/forward/backward/clip，100次遍历，31200病例曝光，300次丢弃。3900个实际批次的病例、来源、LR、BN、clip和step提交字段逐条验证，并与冻结F0 D折完全一致。order_plan、optimizer defaults、parameter groups、exposure的原始文件字节也与F0D一致。曝光及丢弃独立重算通过。

完整持久初始化指纹与F0D、LQIC相同；总参数39,903,169。跨LQI C/D沿用相同模型/bridge/runtime、初始seed、静态loss、点数和更新/曝光合同；其数据折与顺序计划不同，这是正确的分折设计，不要求C/D病例顺序相同。相同初始指纹不能被解释为梯度逐位确定性。

3900条LQI几何摘要的step/epoch/batch/case_ids、有限性、质心/半径/包围盒维度与边界关系通过。这里只验证日志自洽，不重新生成dense点云或赋予其GT精度含义。

3902条资源记录按实际数值、阶段和原阈值核验通过。峰值Torch allocated 12.933GiB，reserved 13.758GiB，SMI显存14575MiB，RSS 1.558GiB；末段记录耗时1643.2秒（约27.4分钟）。资源是采样监测，不是专属cgroup硬隔离或宿主PID归属证明。

BNCal、evaluation、resume均为false。checkpoint SHA与completion和产物清单一致，但其内部模型/optimizer张量未经反序列化审查。本轮不产生LQI补全效果结论，也不根据训练loss调参。

下一步可核查LQI两折Native预测入口兼容性，准备每折105例、合计210次预测的待授权范围；复用已冻结F0基线预测，之后统一评分。若既有入口仍锁定F0，应先作限定LQI分派/读取绑定/元数据适配及CPU/P3，不重复GPU preflight。当前未创建预测request或运行评价。

机器可读记录：`post_training_freeze_audit_result_v1.json`及`F0D_LQIC_pairing_freeze_audit_result_v2.json`。
