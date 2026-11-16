# Static_D 正式只读安装后冻结审计 v1

结论：通过。独立审计远端退出码为 0，无本机超时。

- 当前身份与冻结 qx2k0r-0、UID 1000 一致。
- 原上传包实测 8031 字节，归档 SHA256 及映射 SHA256 与冻结值一致。
- 唯一安装目标实测 15491 字节，与归档成员逐字节一致；SHA256 为 `f2a9d28fae758c5e718c28bc463d9c90de8b07b752ec89d80441807827018fb2`。
- 目标为普通文件，UID 1000，权限 0644；读取前后内容相关属性一致。
- request 保持 AWAITING_EXPLICIT_USER_AUTHORIZATION，execution_authorized=false。
- 安装根直属名称集合与既有 11 文件、已安装 C 补充两文件、既有 control 目录及新 D request 精确一致。
- D 控制目录、结果目录、attempt claim、授权回执、runtime、launcher 共六个路径均不存在。

本次不重新散列 71 个复用文件、C 权重或 315 个 D 训练 payload；不构成训练资源准入。服务器写入、测试及训练均为 0。未创建训练执行内容。

下一步可单独明确授权上述完整训练 request SHA256；授权后仍需重新核验当前资源、315 份 D 输入和输出路径，再按冻结合同启动唯一一次 Static_D、8k→8k、3900 步训练。失败即停，不自动重试或 resume，不运行评价或 BNCal。
