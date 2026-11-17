# TRACE D0正式只读安装后冻结审计

日期：2026-11-17。结论：**FORMAL_TRACE_D0_POST_INSTALLATION_FREEZE_PASS**，10项核验通过。

本次独立重新连接服务器并读取已安装文件，不使用安装时即时回读替代正式审计。

## 核验结果

- 当前容器`shu-common-25721452-notebook-yxwd3w-0`，uid=1000，与冻结映射一致。
- 安装根`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_trace_D0_20261117_v1`精确包含6个目标，无额外文件或目录；安装路径和父路径无符号链接。
- 6个文件的新鲜大小／SHA256与冻结映射、安装回执逐一一致；所有者uid=1000，权限0644，读取期间内容相关属性未变化。
- request／准备范围／P3交叉绑定、80次零更新计数及固定病例输入一致；P3状态为`TRACE_D0_LOCAL_P3_PASS`。
- request保持`AWAITING_EXPLICIT_USER_AUTHORIZATION`，`execution_authorized=false`。
- 生产授权回执、runtime、launcher、单次claim及D0结果目录5个路径全部不存在。

request完整SHA256仍为：

`7ad5a27aee302b877af7903b00da107c47560250d18135566315609b12a01b0f`

## 范围与限制

本次读取已核验运输包中的冻结映射并重新核验6个已安装目标，没有导入或运行包内源码。没有服务器写入、测试、GPU、forward、loss、backward、optimizer step或训练。

本次不重复77个复用文件哈希核验，也不重新采集GPU／磁盘资源；它们须在真正执行前按request再次核验。正式安装冻结通过不表示执行时资源仍可用，不代替执行授权或未来的post-diagnostic审计。

机器可读判据及证据绑定见`formal_freeze_verification_v1.json`。原始stdout／stderr、调用退出码、审计源码和固定查询范围均保存在本目录。

## 下一阶段边界

下一步可对上述request完整SHA256单独执行授权。获得授权后，才可重新核验执行条件并按单向依赖材料化生产授权回执、runtime和单次launcher，启动唯一一次四模型、40病例、80次完整forward、零更新D0诊断。失败即停，不自动重试；本文件不授权该执行或任何G3／训练。
