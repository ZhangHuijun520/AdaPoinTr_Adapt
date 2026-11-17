# G0_C UTC顺序修订、CPU验证与v3请求

2026-11-16。生产入口相对v2仅新增一行`if utc.allow(filename,write):return`，位置在整数FD判断之后、source guard之前。既有UTC精确链接／目标／大小／SHA只读验证不变，不泛化放行其它链接。模型、head、bridge、runtime、loss、数据、order、3900步和预算均不变。

12项CPU合同回归通过。使用实际入口嵌套Policy和真实继承训练policy，人工UTC／source行为验证精确UTC读取优先、写入与校验漂移拒绝、其它链接拒绝、源码只读、未授权NPZ拒绝及整数FD路径。真实Linux UTC资源在上一轮只读审计已确认，本轮不导入生产依赖或运行GPU。

准备阶段因测试文件已创建目录而mkdir失败，随后的测试启动尚未读到scope、未进入合同断言；保留当时空目录。完成准备后在全新CPU_contract_batch_v3仅执行一次12项合同检查，没有失败断言后的自动修复重跑。

新P3见training_P3_v3.json，继承真实加载链与人工训练生命周期CPU证据；原正式CUDA冻结不变。完整序列化request及授权／单向runtime／POSIX启动器仅静态内存检查，未生成真实执行控制文件。

request完整SHA256：`871c5216815d5e479446108da979e8c77ce6ea5aec2578ac0573652e51a75d63`。

状态AWAITING_EXPLICIT_USER_AUTHORIZATION。新root/run/control/tmux均为v3，旧v2已消耗，不覆盖或复用。

上传pending_transport_v3中的bcsp_spcg_G0_C_UTC_order_pending_20261116_v3.tar.gz及.sha256、.bytes、.contents.sha256。归档13,933bytes，8个拟安装文件＋映射；复用所有未改大资产，不升级或重装。

本轮无服务器调用、模型运行或GPU准入。上传后需单独完整SHA执行授权并重验当前设备／资源、复用哈希／315输入、order、新目标及父目录，才可不覆盖安装和单次训练。失败即停；无需重复GPU准入。
