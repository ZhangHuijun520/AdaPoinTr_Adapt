# RIVE Static_C最小运输包冻结说明

状态：仅本机冻结；未上传、未安装、未执行。

## 上传位置

请仅将 `upload` 目录中的以下四个文件手动上传至服务器 `/home/jovyan/`：

- `bcsp_rive_Static_C_pending_20261115_v1.tar.gz`（41020字节）
- `bcsp_rive_Static_C_pending_20261115_v1.tar.gz.bytes`（6字节）
- `bcsp_rive_Static_C_pending_20261115_v1.tar.gz.contents.sha256`（1277字节）
- `bcsp_rive_Static_C_pending_20261115_v1.tar.gz.sha256`（112字节）

压缩包SHA256：`97fcdbe8fe31e410127301581dd7280588b71da0361059937e84015881396445`。

原训练request SHA256保持：`fdcb6cacef71bfae9395baf7b3bd05506b34b4053b75bfb03f54bff6bbe82bda`，状态仍为 `AWAITING_EXPLICIT_USER_AUTHORIZATION`。

## 冻结范围

- 11个新目标：entry、bridge、request、P3、pair contract、原设备训练冻结凭据、R01只读核对凭据、CPU结果、CPU测试源码、静态审查、CPU读取策略stdout。
- 压缩包共12个普通文件；安装映射仅用于审核，不安装到代码目录。没有安装器或可自动运行的shell脚本。
- 58个既有源码/初始化/配置/provider文件仅列为只读复用核验对象，没有打包、恢复或改写它们。
- 不包含权重、真实NPZ、原始医学数据、CPU fixture目录、生产授权回执、runtime或launcher。
- CPU测试源码仅作P3来源证据，本轮安装不执行测试，也不声称该最小包是独立的完整测试环境。
- P3与旧证据内的Windows本机路径是历史溯源记录，不是服务器执行或下载路径。

## 安装边界

安装根为 `/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1`。本轮未核查其现场状态，不能宣称其不存在。后续写入前必须新鲜核验容器身份、所有复用哈希、根目录及11目标不存在、父目录非链接；仅用不覆盖创建，异常即停，不自动清理或重试。安装不得创建control、结果目录或任何执行控制。

本次只重新读取压缩包、逐成员核验大小/SHA、类型、唯一名称及sidecar一致性，没有执行源码或重跑CPU测试。

上传完成后下一步仅做授权的只读上传核验；上传不等于安装或训练授权。完整四运行空间仍未认证，首运行执行时另需新鲜资源检查。
