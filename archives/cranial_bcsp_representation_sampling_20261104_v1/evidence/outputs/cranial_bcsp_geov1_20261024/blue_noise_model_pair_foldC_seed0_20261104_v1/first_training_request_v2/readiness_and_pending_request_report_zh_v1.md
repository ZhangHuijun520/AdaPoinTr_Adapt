# 欧氏／图距离 Fold C：服务器就绪核对与首运行待授权范围

日期：2026-11-04。状态：AWAITING_EXPLICIT_USER_AUTHORIZATION。

当前容器 shu-common-25721452-notebook-v2iwsa-0，UID1000，RTX4090D，GPU UUID GPU-34a1b996-2bd7-88e6-9dca-164b718caea6，驱动 570.190。SMI显存1MiB、无计算进程；磁盘可用10.18GiB。30个固定资产共18245900字节全部大小及SHA256匹配。三个新根目录不存在，父目录可写且无链接。Git查询返回128，原因是服务器副本不是Git仓库；保留失败查询及成功补证原文，以固定文件哈希绑定源码身份。第二版服务器查询返回0且完整观察落盘，本机随后摘要打印因字段分支产生KeyError；不影响已落盘的只读证据，未因此再发起查询。

保留原本机implementation目录。最终部署候选只替换contract的资源占位哈希及entry的contract哈希，runtime逐字节不变。既有20项CPU检查及840文件读取结果继续保留；最终绑定另做6项限定检查，包括实际rebind、完整authorize、训练元数据、批次、拒绝未授权和入口哈希启动。授权仅在RAM中模拟，没有真实授权文件。以上不是CUDA或模型训练验证。

运输包含两臂各315份训练点集，合计630份NPZ及固定代码/证据，共650个文件；不运输开发点集、原始体素、诊断选点或权重。安装映射使用精确Linux绝对路径，manifest内Windows路径只作溯源，不执行或猜测转换。

首个request仅覆盖一次Euclidean_elimination，FoldC、seed0、8k→8k、batch8、100遍历、3900更新、31200曝光及300丢弃。第二臂必须等待首臂训练后审计并绑定相同初始化指纹，再单独授权。资源合同保持24h、RSS8GiB、设备显存22528MiB、Torch峰值20GiB、输出2GiB及启动前可用磁盘4GiB。失败即停，不自动重试或resume。

request SHA256：`40a45089ed847261d9477993118b406048dadd09d15e492a402b455bddfdad74`。压缩包：`bcsp_blue_noise_ab_foldc_seed0_v1.tar.gz`，99377155 bytes，SHA256 `e5c46195f75eb672a69fea58767a352d16c534ecb5be210b24b0eab3b6ff17d4`。

运输文件位于本目录transport_v1；上传到/home/jovyan后，仍须先核验上传与目标不存在性。当前未上传、安装、材料化真实授权/runtime/launcher或启动训练。需另行明确授权完整request SHA256。
