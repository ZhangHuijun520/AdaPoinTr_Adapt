# Static_D单request补充包冻结说明

仅本机冻结，未操作服务器。上传目录内四文件至`/home/jovyan/`：

- `bcsp_rive_Static_D_pending_20261115_v1.tar.gz`（8031字节）
- `bcsp_rive_Static_D_pending_20261115_v1.tar.gz.bytes`（5字节）
- `bcsp_rive_Static_D_pending_20261115_v1.tar.gz.contents.sha256`（241字节）
- `bcsp_rive_Static_D_pending_20261115_v1.tar.gz.sha256`（112字节）

压缩包SHA256：`1f349b82560ace2e04af6982fbdeb6dcd489f11618eae1769521308e5941e39b`。包内2个普通成员为request与仅审核安装映射；只安装request，入口/P3/数据全部复用，没有权重或执行控制。

request完整SHA保持`f2a9d28fae758c5e718c28bc463d9c90de8b07b752ec89d80441807827018fb2`，状态AWAITING_EXPLICIT_USER_AUTHORIZATION。冻结映射列明71复用文件，包含实际D折qualified与D-order；不按C折目录名推断数据。

包内成员和四sidecar关联已在本机重新打开核验；没有执行包内代码或测试。后续已有安装根必须存在且非链接，新request目标必须不存在；不覆盖写入、异常即停。保护已有C两臂控制和结果，不创建D执行控制或结果。

上传后下一步仅做单独授权的只读上传核验，不自动安装或训练。
