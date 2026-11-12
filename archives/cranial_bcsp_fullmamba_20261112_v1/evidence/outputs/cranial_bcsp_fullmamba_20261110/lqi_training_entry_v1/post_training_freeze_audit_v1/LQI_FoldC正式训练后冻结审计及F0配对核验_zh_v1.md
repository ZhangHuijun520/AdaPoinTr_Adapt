# LQI Fold C正式训练后冻结审计及F0配对核验

日期：2026-11-11。结论：**训练后审计42项通过，F0配对核验12项通过**。退出码0、worker与tmux均结束。本轮无服务器写入、新forward、测试、权重反序列化或后续实验。

最终checkpoint：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldC_seed0_train_20261111_v1/ckpt-last.pth`。

大小：478,810,419 bytes。

实测SHA256（两次独立原始字节哈希一致）：`d8d819ffb9ed1f931c60f0ee96e9ae9c4093d61c73c2152a52f13b8cd95a0ddf`。

33个服务器产物/安装凭据的完整清单、前后文件指纹和哈希稳定；32个非权重证据文件已下载并核验。checkpoint仅在服务器只读哈希，没有下载或加载。授权回执、单向runtime、单次claim、原launcher、安装映射及70份复用资产哈希核验通过。

计数：3900次forward/backward/clip/optimizer step，100次遍历，31200次曝光，300次丢弃。实际3900批的病例与来源、LR、BN momentum、裁剪上限和提交状态逐条验证，并与F0逐条相同。病例曝光及丢弃从实际顺序独立重算，与exposure及completion一致。BNCal、evaluation、resume均为false。

完整持久模型初始化SHA256与冻结F0相同；order_plan、optimizer defaults、parameter groups和exposure四份文件的原始字节哈希也相同。原数据/QC、静态loss及点数合同不变，实际参数总数39,903,169，22个A_log和22个D均按原合同不weight-decay。模型执行布局确实由绑定的LQI源码分派，日志标识query-aligned interleaving及历史trace字段的新语义。

3900条LQI几何日志的step/epoch/batch/case_ids与训练记录对齐，coarse/dense质心、半径、包围盒的维度和有限性及坐标边界关系通过。这些是无GT的归一化几何摘要，不是实际几何精度评价；没有加载模型重新生成点云验证这些摘要。

3902条资源记录逐条重算原阈值通过。峰值Torch allocated 12.933GiB，reserved 13.758GiB，SMI显存14575MiB，RSS 1.555GiB；末段记录耗时1666.8秒，约27.8分钟。资源为采样值，不构成独占cgroup或宿主PID归属证明。

**本结论只确认训练与配对合同，不判断LQI优于F0。** 初始状态/顺序相同不等于梯度逐位确定性；既有有限梯度非确定性披露保留。checkpoint内部张量和optimizer内容未反序列化审查，SHA256与completion、产物清单一致。

下一步按预定两折合同准备Fold D LQI待授权训练request，保持8k→8k、同折初始化及批次顺序、3900步，不根据C折训练loss调参或筛病例。先核对入口的Fold D分派；现入口限定Fold C，不能直接把request的fold改成D。如需专用入口应集中做最小适配、CPU验证/P3，再创建待授权request，不重复GPU preflight。

本轮没有创建Fold D request，没有启动训练、BNCal或评价。

证据：`post_training_freeze_audit_result_v1.json`与`F0_pairing_freeze_audit_result_v1.json`。
