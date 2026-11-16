# Requery_D 两文件补充包上传说明 v1

已在本机冻结，仅供手动上传。本轮服务器调用、测试、训练和执行控制材料化均为0。

## 上传文件

本机目录：`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\scq_rive_training_implementation_20261115_v1\Requery_D_request_preparation_v1\pending_transport_v1\upload`。

请将目录下四个文件原名上传到 `/home/jovyan/`：

- `bcsp_rive_Requery_D_pending_20261115_v1.tar.gz`：12264字节；SHA256 `a3fef516e809b92d5835be2377cad840e77c06e482ef2a0519cd0b7c8ba3e2d6`。
- `bcsp_rive_Requery_D_pending_20261115_v1.tar.gz.bytes`：6字节；SHA256 `cf406ffc941753810c803c1851b802bee91a6a55dcdda43fd03c6ef0d7df5e1e`。
- `bcsp_rive_Requery_D_pending_20261115_v1.tar.gz.contents.sha256`：356字节；SHA256 `913cf7d58b9877406d89b34915890b1175daf98209b79ff280e6c3c86366270b`。
- `bcsp_rive_Requery_D_pending_20261115_v1.tar.gz.sha256`：113字节；SHA256 `b41f7335a345460e9209b5f3689b2680fe2d01e796f3548ed102988146cf3b93`。

## 包内容与映射

归档包含3个常规成员：映射JSON（只审计，不安装）及2个payload（Requery_D request、Static_D正式冻结凭据）。仅计划向既有安装根新增这2个文件，使用xb不覆盖写入；72个复用文件不重复运输。模型、依赖、点集及训练合同不变。

request SHA256 `c7519213883f5ffd7014576ab482beac4456ace3e4656606bcc40714672efba1`；冻结凭据 SHA256 `d1637699a9e1e6813920c5feeae014db72500ef71b15e21d447c2d2e479a86ea`；映射 SHA256 `ee97d9473ffcfbd28a563d1638f76b5736eb96dcc48627bc7200b26c6b000e45`。

18项静态检查通过。冻结前发现Windows文本换行转换，已将三个校验文件写为精确LF字节并重新核验；归档及两份源文件、映射均未因此变化。当前服务器身份、目标不存在性及资源未重新检查。

## 下一步边界

上传后仅做单独授权的只读上传核验，不自动安装。后续安装前重验身份、上传包、72个复用文件、父目录及两个目标不存在，异常即停，不覆盖、删除或自动重试。未创建训练授权回执、runtime、launcher、claim或输出目录。

独立安装后冻结审计通过后，再对完整request SHA256单独授权训练。保持8k→8k、同初始化、D折顺序及3900步合同，不根据Static_D loss调参，不自动运行评价或BNCal。
