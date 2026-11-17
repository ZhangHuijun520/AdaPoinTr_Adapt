# TRACE P0有限差量核对与D0准备记录

日期：2026-11-17。结论：**P0有限核对通过，具备准备观察入口的条件；尚不具备执行授权或实现P3。**

## 实测结果

| 对象 | 结果 |
|---|---|
| 当前容器 | `shu-common-25721452-notebook-yxwd3w-0`，uid=1000 |
| GPU／驱动 | NVIDIA GeForce RTX 4090 D，`GPU-4b19574a-832d-b4fe-e655-a57462954d6a`，570.190；与原Native设备一致 |
| GPU快照 | 总显存24564 MiB，已用1 MiB，利用率0% |
| 磁盘余量 | 7875854336 bytes，约7.33 GiB |
| 源码／配置／provider／U/H | 18个固定文件，全部新鲜大小及SHA256匹配 |
| 开发输入 | 40病例／40来源，40个文件大小及SHA256匹配；未解码数组 |
| G1_C/G2_C/G1_D/G2_D权重 | 4个最终checkpoint新鲜SHA256匹配，读取期间未变；未反序列化 |
| 历史预测归档及sidecars | 本机新鲜哈希匹配；80条对应历史评分记录存在 |
| 新安装根和新输出路径 | 均不存在，父目录存在，无路径链接 |

输入根目录必须沿用实际绑定：C开发病例位于`data/bcsp_geov1_foldd_8192_seed0_v1/points`；D开发病例位于`data/bcsp_geov1_foldc_8192_seed0_v1/points`。目录名表示历史点集生成／训练分组，不能根据后缀猜测并交换路径。

两份大型Mamba/CausalConv CUDA二进制本轮只做存在性和精确大小核对，哈希继承原冻结记录，没有新鲜重哈希或导入。最终执行仍须复用原精确加载校验；本轮不扩大依赖库存。PointNet2 provider及其二进制已包括在18个新鲜文件核验中。

磁盘满足6GiB启动、4GiB运行余量和本次1GiB产物预算；这不是对后续训练矩阵容量或未来GPU空闲的保证。每次真正执行前仍按request重验。

## 真实接口结论

母版PCTransformer在encoder之后取得`coor`、`x`，经increase_dim与max得到global_feature；唯一首次coarse赋值是`self.coarse_pred(global_feature).reshape(bs,-1,3)`。SPCG factory只将该赋值替换为`spcg_head(xyz,coor,x,global_feature)`，后续mlp_query、LQI decoder和dense路径保持。

因此D0中的S=coor、F=x、z=global_feature均可在真实head入口得到，无需改encoder或decoder。已有`head.capture`保存S/F/z/A/mu/rho/tau/index和Q，但缺少实际x、f和原生距离矩阵。

最小补齐方法：沿用现有capture；给H首层添加只读pre-hook取得实际x，f取x的[1024:1408]；仅为G2对传入argsort的原生FP32分数增加一次返回同一张量的观察包装。该包装只存在于隔离实例，不能改冻结生产源码或排序公式。不得将FP64重算的近邻次序替代实际索引。G1实际使用ALL256，不伪造8邻域。

这仍是待实施的接口设计，尚未以CPU或CUDA证明观察等价性。没有必要重复原模型GPU preflight，但须完成一次针对性CPU验证/P3，之后才能创建绑定最终实现哈希的request。

## 调用链记录

最初合并查询6755字节，85秒无回传；保留原源码、命令绑定、stdout/stderr和超时记录，不声称当时资产核验通过。随后进程快照未发现残留Python核验进程，未重发该长查询。将同一范围分为四个已静态核对的短查询（811/1115/1171/951字节），均成功返回，再补核两个原定新路径。

该现象与长命令传输问题相符，但本轮未做专门传输因果实验，不能认定唯一原因。没有模型调用失败、重训或GPU重试，不新增通用传输框架。

## D0已准备的固定范围

- G1_C→G2_C→G1_D→G2_D，各20例，总80次完整forward；8192输入／8192输出、batch1。
- loss/backward/optimizer step/warmup/BNCal/retry均为0。
- 固定40例不替换，5个既有案例单列；主要关联C=17、D=18来源。
- 全部80条保存D/S/F/z/A/x/f/mu/rho/tau/Q/P，G2另存原生FP32分数和实际KNN索引。
- 新输出`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/TRACE_D0_memory_evidence_20261117_v1`；新安装根`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_trace_D0_20261117_v1`；本轮未创建它们。
- GPU阶段不读GT；历史预测重放、E/J核验及关联分析在后续本机CPU评分副本中完成。
- 资源与新TRACE重放限值见`TRACE_D0_preparation_scope_v1.json`；资源阈值不放宽。

## 剩余实施边界

建议下一次仅授权四个隔离文件：观察适配、D0短入口、CPU分析入口和人工测试文件。完成一批CPU验证及正式冻结/P3后，再生成最终待授权D0 request。本轮没有写观察实现、runtime config、launcher或execution request；没有服务器写入、模型加载、forward或训练。
