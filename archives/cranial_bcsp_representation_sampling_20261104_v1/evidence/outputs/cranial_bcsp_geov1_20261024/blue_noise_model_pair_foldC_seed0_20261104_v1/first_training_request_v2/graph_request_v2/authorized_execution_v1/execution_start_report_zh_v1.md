# Fold C 图距离臂：唯一一次授权训练启动记录

2026-11-04，训练运行中。用户原文“已上传，单独授权上述完整哈希”，解析为完整scope SHA256 `1072fad5cbbb970fe37cf6300445d705b8dc99a38aba3fc20cb70cac6cf227d5`。

5个上传文件与3个新控制文件映射核验通过，315份图距离训练NPZ重新流式核验哈希；欧氏臂completion、initialization及checkpoint重新按冻结大小／哈希核验。3个新控制文件以不覆盖方式安装，未修改数据、生产源码、provider或欧氏结果。

按授权回执→其SHA256→runtime→launcher顺序材料化，创建一次claim后仅启动一次固定tmux。会话 `bcsp_blue_noise_foldc_graph_seed0_train_v1`，worker PID `51600`。观察到67/3900个已提交更新，未见退出码或失败文件。初始化参数、持久buffer、seed和顺序指纹与冻结欧氏证据完全匹配；真实入口在首更新前执行相等性断言，没有加载欧氏最终权重。

本轮资源观察：SMI 14074MiB，Torch allocated峰值 12.30GiB，RSS 1.17GiB，原阈值检查通过。PID仍按既定diagnostic-only合同记录。

训练保持8k输入／8k输出、同初始化与批次顺序、100遍历、3900步、31200曝光和300丢弃。未进入BNCal、开发评价、额外训练或自动重试。完成后仍须单独正式只读冻结审计及两臂配对核验，本记录不代替最终审计。

输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_blue_noise_ab_v1/bcsp_blue_noise_foldC_surface_graph_in8192_out8192_seed0_train_v1`。
