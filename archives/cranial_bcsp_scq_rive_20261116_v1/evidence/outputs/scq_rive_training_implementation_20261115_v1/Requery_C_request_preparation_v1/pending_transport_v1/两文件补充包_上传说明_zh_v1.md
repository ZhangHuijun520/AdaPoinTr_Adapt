# Requery_C两文件补充运输包冻结说明

状态：仅本机冻结，未操作服务器、上传或安装。

仅将upload目录内四个文件手动上传至`/home/jovyan/`：

- `bcsp_rive_Requery_C_pending_20261115_v1.tar.gz`，11331字节。
- `bcsp_rive_Requery_C_pending_20261115_v1.tar.gz.bytes`，6字节。
- `bcsp_rive_Requery_C_pending_20261115_v1.tar.gz.contents.sha256`，356字节。
- `bcsp_rive_Requery_C_pending_20261115_v1.tar.gz.sha256`，113字节。

压缩包SHA256：`a9ade27d44d8ab13ae121bee131051b6e43b363b2f0080df2ed35901a070c7d4`。

包内共3个普通成员：Requery_C待授权request、Static_C正式冻结凭据，以及仅审核用安装映射。仅前两文件安装；69个既有文件只核验不复制，不更改模型、P3、点集、旧Static控制和结果。不存在权重、医学数据、安装器、执行授权、runtime或launcher。

本次独立重新打开归档并逐成员核验类型、路径、内容、哈希及sidecar。request SHA保持`45d37fc024dd4e97a82cd08c93ad25cebfcbd4a4f74ae8b2be9d22e4536392de`，状态仍为AWAITING_EXPLICIT_USER_AUTHORIZATION。

后续安装根已经存在，必须验证其为正确真实目录，而非要求其不存在；仅两个新目标必须不存在。不覆盖创建、异常即停。Requery控制与结果路径须保持不存在。

上传后下一步仅做单独授权的只读上传核验，不自动安装或训练。
