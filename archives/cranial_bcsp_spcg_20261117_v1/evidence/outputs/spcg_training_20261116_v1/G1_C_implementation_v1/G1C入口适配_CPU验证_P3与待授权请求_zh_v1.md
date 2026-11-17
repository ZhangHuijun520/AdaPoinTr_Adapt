# SPCG G1_C入口、CPU验证、P3与待授权范围

2026-11-16。本机限定implementation-only完成，唯一一批16项人工CPU检查通过，新P3通过；未部署、连接服务器、训练或重复GPU准入。

## 科学设置与配对

G1为原计划的全局256个Memory聚合与共享坐标生成头，固定Sobol256、8192输入／8192输出、256coarse及原FC每中心32点。直接生成Q，不先生成旧Q0、不加A残差、额外loss或clamp。

G0_C正式冻结作为配对前提。相同未训练LQI母版、同设备身份、Fold C数据／完整批次order、AdamW与调度、3900更新／100遍／31200曝光／300drop。G1是scratch，**不加载G0最终训练checkpoint**。原U／H字节从已有冻结资产直接读取，保持与CUDA准入G1初态相同，不因G0训练loss重抽或调参。

G1头1,845,763参数，原head删除，完整模型预期39,912,132参数；共同模块初始化在替换前匹配G0 scratch指纹，替换后匹配CUDA G1完整指纹。不得把两种不同state fingerprint算法混比。

## 实施

新增G1_C专用entry和bridge：entry只接受G1_C，加载bridge→head→observe→原training runtime后，按精确绑定加载SPCG factory；build_G1先核对scratch母版，再装入G1 head、U/H并核对完整初态。head初始化和U的精确只读记录纳入文件guard，不扩展目录读取权限。

bridge相对G0只有arm守卫G0→G1，原3900-step训练runtime、优化器、loss和调度未修改。继续同forward观测、3900条几何日志及1／39／390／1950／3900五个总loss Q梯度步，无新增forward或backward。

保留UTC-first、完整异常在guard关闭前落盘及SystemExit(1)路径。资源保持3600秒、1GiB输出、8GiB RSS、20GiB Torch、22528MiB SMI。启动前重验至少8.5GiB可用及全部复用资产；本轮不能证明服务器实时容量。

## CPU及P3

16项通过，包括实际G1 factory/head、原母版forward／FC／loss路径，U/H字节、旧head移除、Q梯度、初态算法、G0冻结／order绑定、GPU漂移与scope拒绝、授权单向runtime合同及不变源码。

骨干和loss为人工替身，未重新运行真实Mamba或生产cdist loss。真实导入链、文件策略／异常收尾及原生命周期CPU证据继承，未冒充本轮重新执行。没有开发集评分或基于结果调整。

## 请求与交付

状态AWAITING_EXPLICIT_USER_AUTHORIZATION。完整request SHA256：

`2d8ef3fff5db90653d0408ac6db72911e2c84b75aa61c9f03c8033aaf56ac0e4`

位置pending_transport_v1/payload/SPCG_G1_C_training_execution_request_v1.json；全新run：SPCG_G1_foldC_seed0_train_20261116_v1。

上传pending_transport_v1中的bcsp_spcg_G1_C_training_pending_20261116_v1.tar.gz及.sha256、.bytes、.contents.sha256。归档18,177bytes，9个拟安装文件＋映射；数据、U/H和provider大资产复用，不重装依赖。

未材料化真实授权回执、runtime、launcher或claim。上传后需单独完整SHA执行授权；重验当前身份／资源、复用hash／315输入／order、G0冻结凭据和全新目标后才可不覆盖安装、唯一一次训练。无需重复GPU准入，失败即停，结束后独立只读冻结审计，再准备G2_C。
