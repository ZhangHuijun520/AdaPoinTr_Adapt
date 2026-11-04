# 图距离臂 Fold C：待授权训练 request v1

2026-11-04。状态：**AWAITING_EXPLICIT_USER_AUTHORIZATION**。本轮只在本机准备与核对，没有服务器调用、安装或模型执行。

固定surface_graph、Fold C、seed0、输入8192／输出8192。复用与欧氏臂逐字节相同的模型／训练实现、环境身份、配置、批次顺序及资源阈值，保持batch8、100次遍历、3900次更新、31200次曝光及300次丢弃。

初始化从scratch seed0创建，在首个更新前比较参数与持久buffer指纹。绑定欧氏臂39项正式冻结审计、实测checkpoint身份、初始化及顺序；不读取或加载欧氏臂最终权重作为初始化。绑定checkpoint哈希用于溯源，不是resume。

只运输3个新控制文件：paired_initialization_receipt_v1.json、qualified_training_receipt_v1.json、training_entry_request_v1.json。点集、源码、provider不重新运输或修改。315份图距离训练点集已在最初650文件安装时核验；欧氏训练后审计未重新读取图距离NPZ，因此本request明确要求执行前重新流式核验全部315份，不能把安装记录冒充最新实测。

9项本机限定读取检查通过，包括实际完整authorize/rebind路径、315训练元数据、初始化一致性接受、不同初始化拒绝及未授权拒绝。授权与runtime仅在RAM中模拟，未写真实执行文件。

新控制目录：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_blue_noise_ab_foldc_seed0_v1/control_surface_graph_v1`。
新输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_blue_noise_ab_v1/bcsp_blue_noise_foldC_surface_graph_in8192_out8192_seed0_train_v1`。
固定tmux：`bcsp_blue_noise_foldc_graph_seed0_train_v1`。

预算保持24小时、RSS8GiB、设备22528MiB、Torch峰值20GiB、输出2GiB及可用磁盘至少4GiB；监测式停止，不保证专属cgroup。失败即停，不自动重试／resume。开发评价、BNCal、其他fold／seed及额外训练仍不授权。

运输文件见本目录transport_v1的5个文件，上传到/home/jovyan。request完整SHA256：

1072fad5cbbb970fe37cf6300445d705b8dc99a38aba3fc20cb70cac6cf227d5

只有对完整request哈希的后续单独执行授权，才可执行上传／就绪核验、3文件不覆盖安装，以及授权→runtime→launcher的单向材料化和唯一一次图距离训练。当前没有这些执行内容。

准备过程曾遇到旧长文件名触发Windows路径长度限制，失败目录保留；本版只缩短本机目录及运输文件名，没有改变服务器路径、生产实现或科学合同。
