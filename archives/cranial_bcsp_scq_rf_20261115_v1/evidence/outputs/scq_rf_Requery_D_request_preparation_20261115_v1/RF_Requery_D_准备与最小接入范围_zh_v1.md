# RF-Requery Fold D 准备与最小接入范围

2026-11-15。本轮仅本机只读核对，不操作服务器、测试或训练。

S-ref_D正式冻结30项通过；D折数据、顺序和计数合同完整。冻结矩阵下一臂为Requery_D，Static_D在其后，不能颠倒顺序。

保持seed0、8k→8k、315病例/63来源、3900更新、100遍历、31,200曝光、300丢弃；原RF模型40,827,847参数、第二头231,171参数。复用已准入RF源码、两份初始化、loss、优化器、阈值及D折矩阵/就绪记录。已有Requery bridge功能与fold无关，可原样复用。

现有Requery_C入口仍限定C折，并要求Static_C先冻结。D折不能照搬该依赖：既定顺序是先Requery_D，再Static_D。因此需新增D专用入口，将同折参考绑定为S-ref_D，保留C阶段已冻结证据作为完成顺序及模型初始化来源；不要求尚不存在的Static_D。

可以沿用C阶段已冻结RF模型的完整初始参数/持久状态指纹作为同seed、同源码、同初始化的身份合同，但必须与D折顺序分开。C初始化记录中的order_sha256不能移植为D顺序；真正D顺序固定为2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838。不加载C或D已有checkpoint，不warm-start，不根据C折loss调整D设置。

下一步建议单独授权：Requery_D最小入口接入、一批针对性人工CPU验证及P3。集中覆盖D折完整authorize、S-ref_D冻结证据、模型初始化与顺序分离、真实RF重查询/梯度、几何日志、精确读取链及异常回溯。已有bridge、模型和runtime保持不变，无需重复GPU准入。

通过后再创建绑定最终哈希的待授权execution request。本次未创建可执行request或任何授权控制文件。
