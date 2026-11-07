# H2-AUX Fold C 正式只读训练后冻结审计

日期：2026-11-07。结论：PASS；25项检查全部通过。

## 完整计数与边界

退出码0，worker及固定tmux会话均已退出；完整3900次forward/backward/clip/optimizer更新，100次遍历，31200次病例曝光，300次丢弃。3900条指标和3902条资源记录均完成复核。BNCal、评价、resume均为false。本次审计没有写服务器、加载权重或运行模型。

## 最终checkpoint

文件：ckpt-last.pth；大小407239343字节。服务器重新读取文件字节计算的SHA256与completion及payload manifest一致：

`	ext
15c8c3f717c340a2661b78d9e17d33f56ceb79dfdadd10908015b02f7dfc9538
`

## 初始化、顺序与H2合同

原M0 factory全部共有构建证据与冻结初始化记录精确一致；新增范围头的零初始化检查及首批8个delta全0均通过。原362组优化器参数记录保持不变，仅新增范围头weight/bias两项，共1025参数；原optimizer defaults保持不变。完整3900个实际批次、来源、LR、BN日程、曝光与丢弃计数逐条匹配原冻结顺序。

H2始终为AUX，H1关闭；所有病例的scale为1，raw/used中心与半径完全一致。3900步均复算并核对log半径目标、SmoothL1、0.1权重及总loss相加关系，未发现重复加权或缺失。训练日志中的loss_reconstruction沿用父字段，包含H2辅助项；纯原始重建损失应读取loss_original_reconstruction。

## 产物与资源

15个精确输出文件及72个冻结资产重新核验哈希；产物清单成员、大小及哈希一致，审计前后目录inode、大小、权限和mtime无变化，atime不作为内容变化判据。峰值Torch allocated约12.47 GiB、reserved约13.40 GiB，设备显存14210 MiB，进程RSS约1.58 GiB，全部记录满足原资源预算。

3902条记录均存在PID口径警告，符合已确认的DIAGNOSTIC_ONLY策略，不推定跨命名空间进程归属，也不宣称硬隔离。

## 证据限制与下一阶段

H2加入零参数后，模型全量初始指纹与无H2的M0不同是预期现象；本次比较共有factory初始化证据、已绑定源码中的不变性断言和首批零输出，没有重建初始张量。checkpoint仅进行字节哈希核验，没有反序列化其权重或内部H2元数据。有限原生Mamba梯度非确定性继续按既定政策披露。

本结论证明该运行完成且冻结证据自洽，不代表开发集补全质量或接口吻合改善。下一步建议仅准备同折H2-COUPLE配对训练request，绑定本审计、同初始化及同完整批次顺序；仍需单独执行授权。不根据本次训练loss修改超参数。
