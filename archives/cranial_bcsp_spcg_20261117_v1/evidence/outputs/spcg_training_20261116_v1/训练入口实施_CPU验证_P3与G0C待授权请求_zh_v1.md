# SPCG首个G0_C训练入口：实施、CPU验证、P3及待授权范围

日期：2026-11-16。状态：本机implementation-only完成，唯一一批16项人工CPU检查通过，新P3通过，首个G0_C request保持待授权。未操作服务器、部署、运行GPU或训练；未重复已通过的CUDA准入。

## 最小实现

新增bcsp_spcg_training_entry_v1.py和bcsp_spcg_training_bridge_v1.py，复用冻结bcsp_p1_training_runtime_v1.py，不重写正式优化器循环、loss、LR／BN调度或数据加载。

入口仅接受G0、Fold C、seed0、8k→8k，scratch 3900更新，100遍、31200曝光、300drop。原始315训练病例及完整批次order复用；禁止development评价、BNCal、resume或自动重试。

G0采用已通过CUDA的原LQI factory，不加载旧训练checkpoint。使用CUDA证据原有“名称＋原始张量字节”指纹算法核验初态；不将其与helper另一个包含shape／dtype的指纹算法混比。G1/G2以后需分别绑定首组冻结证据及入口兼容性，当前不自动授权。

训练资源为3600秒、RSS8GiB、Torch20GiB、SMI22528MiB、每run全部输出1GiB，启动前按折块至少8.5GiB可用。静态config仍保留原历史资源字段，实际预算对象明确使用本轮request值，不修改原config。没有cgroup独占保证，超限按原监测规则停止。

每次同forward记录coarse/dense中心与半径、两项原loss。仅在更新1／39／390／1950／3900时保留Q梯度和多样性详细记录；梯度来自总loss，未新增forward、backward或autograd.grad。构造日志在原runtime claim_output完成后、首个before_step写入，避免破坏新输出目录合同。

## CPU验证及边界

16项检查通过，证据CPU_batch_v1/result.json。覆盖实际authorize路径、真实元数据验证器、315训练允许列表与完整100遍order、资源／GPU漂移拒绝、单向授权、POSIX启动器、初态证据绑定、同次观测、五个梯度记录步数、两项loss、人工3900次hook调度和失败移除hook。

明确限制：使用微型人工CPU模型和替代生命周期；未执行真实3900步优化器循环，也未训练Mamba或使用真实NPZ。原冻结runtime按内容哈希继承，既有文件策略回归证据复用；本轮没有重跑GPU preflight或声称完整训练显存已证明。

P3见training_P3_v1.json；最终序列化request与源码、bridge、P3、CUDA冻结审计绑定已静态复核。打包辅助脚本的一处Python字段名语法错误已修正，仅辅助脚本发生修正，CPU结果及生产入口／bridge均未改变或重测。

## 待授权request与运输

request完整SHA256：

`0f5a8aca25b1acd43c3bd258ae8ddf7ea3d06f81d020f2c38bde1ea7a944ef08`

路径：pending_transport_v1/payload/SPCG_G0_C_training_execution_request_v1.json。

新安装根：/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G0C_training_20261116_v1。

输出run：SPCG_G0_foldC_seed0_train_20261116_v1。最终ckpt-last.pth沿用原runtime保存结构；历史checkpoint stage标签仅作来源描述，真正科研身份由request及model_construction绑定。

上传pending_transport_v1中的bcsp_spcg_G0_C_training_pending_20261116_v1.tar.gz及.sha256、.bytes、.contents.sha256四文件。归档17,906bytes，9个拟安装文件＋映射。大数据、母版和provider均复用，不升级或重装。

本轮未重新核验服务器状态或新目标不存在，不能将本机P3当作服务器就绪。上传后在单独完整SHA执行授权下重验当前设备、所有复用源码／provider、315输入、order、磁盘及全部新目标，再不覆盖安装、材料化一次授权与launcher并单次训练。失败停止；成功需正式只读训练后冻结审计，再准备下一臂。
