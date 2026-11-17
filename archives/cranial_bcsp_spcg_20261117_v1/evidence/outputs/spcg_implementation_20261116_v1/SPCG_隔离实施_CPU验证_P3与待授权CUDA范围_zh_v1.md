# BCSP-SPCG隔离实施、CPU验证与待授权CUDA范围

日期：2026-11-16。依据：正式计划审阅修订v2及S0有限差量核对。

**结论：限定implementation-only已完成，唯一一批32项人工CPU检查全部通过，post-test只读内容冻结及本机P3通过。真实Mamba、完整生产cdist loss、CUDA梯度与显存尚未验证，不构成训练准入。**

## 实现及不变项

四个隔离生产文件：

- `bcsp_spcg_head_v1.py`：固定256探针；G1全局256与G2局部8聚合；无affine LN；1416→1024→384→3，共1,845,763参数。Q直接生成，不加A残差、不限制bbox、不引入GT或额外loss。
- `bcsp_spcg_factory_v1.py`：保留LQI构造链；只将真实PCTransformer.forward的一处`coarse_pred(z)`表达式替换为显式D/S/F/z调用。G0保留旧头，G1/G2删除旧头。原始query／LQI／FC／返回值与loss消费者不改写。
- `bcsp_spcg_runtime_v1.py`：D-only partial数组读取、同次几何及总loss Q梯度记录、no-decay分组、输出估算和调用预算。3900步训练入口本轮未创建；未来训练日志接入仍须绑定此模块，不能把LOG_STEPS常量视为已完成实际训练集成。
- `bcsp_spcg_cuda_entry_v1.py`：待授权11 forward／3 loss／3 backward／0 step入口，复用既有provider、有限项目导入、精确源文件守卫、UTC和资源监测。无安装、下载、编译或依赖升级。

原始母版、训练runtime、数据、loss和provider文件未修改。G1/G2新增参数相对原头为8,963；目标原生模型参数预期G0=39,903,169、G1/G2=39,912,132，须在实际CUDA构造时再确认。

## CPU验证与证据边界

冻结清单：`CPU_batch_scope_v1.json`；唯一输出：`artificial_cpu_batch_v1/result.json`。32项通过，批次报告耗时约3.31秒，不作为速度结果。

覆盖数学独立参考、G1恒等式、G2稳定并列索引、无并列Memory置换、D bbox不变、批次隔离、H/F/z与人工S梯度、无梯度S合法、raw初始化一致、真实母版forward的单表达式接入、训练／eval消费路径、原FC与get_loss路由、总loss Q梯度、D-only读取、no-decay、完整authorize/materialization/launcher，以及11／3／3／0循环的状态／RNG恢复和首次失败即停。

这里的encoder／decoder是人工替身，CD是便宜标量替身；真实母版forward、FC和loss路由从冻结源码提取。不能宣称完整生产loss已通过CPU，更不能据此宣称Mamba／CUDA通过。

CPU环境PyTorch2.5.1；服务器继承PyTorch2.4.1+cu118。U和H在CPU环境生成后冻结为原始FP32字节；目标环境加载这些权威字节，不要求按seed重生成逐字节相等，不升级服务器软件。H独立流seed2026111600。相关SHA见CPU结果、P3与request。

新候选每run的静态估算约0.61GiB：FP32参数及Adam双矩、2MiB buffer预算、96MiB日志／控制和64MiB序列化／临时余量。仍须实际1GiB上限监测，估算不证明未来完整训练磁盘已准入。

## 唯一待授权CUDA范围

人工解析双球面＋共享圆锥切壁：G0/G1/G2各一次eval B1、一次train B8，共6 forward；只有三个train调用执行完整loss及backward。另有G2五次真实训练D-only eval，零loss／backward。合计11／3／3／0，无warmup、复演或decoder-only。

按预登记SHA排序从两折共同train来源选出的固定五例：

1. train__063__bilateral
2. train__023__frontoorbital
3. train__073__parietotemporal
4. train__056__random_1
5. train__006__random_2

本轮仅依据既有manifest及S0属性清单冻结五例路径、大小和SHA，未读取真实NPZ。未来进程可校验容器文件原始字节，但只提取partial数组；不声称OS已经隔离同NPZ内GT。五例同次保存S/F/z、A、索引、描述子和coarse/dense，距离／邻面支持统计可据这些输出离线计算，不新增forward。

当前拟绑定lwwgl9-0，4090D，UUID GPU-c25d6be2-173c-031a-89c6-b96e0f5f8190，driver570.190。安装及启动前必须重新核验身份、资源、复用文件与全部新目标；本轮没有核查新安装目录是否已存在。任何差异停止，不能套用旧设备信息。

## 最终请求与运输包

request：`pending_transport_v2/payload/SPCG_CUDA_execution_request_v1.json`。

完整SHA256：`00a69c5cc3d42e04f4caa3c21650dd58db5d8c1b446741a1b42caf6730213d0f`。

状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`。没有材料化真实授权回执、runtime、launcher或单次claim。

最终运输目录：`pending_transport_v2`。上传四文件：

- `bcsp_spcg_cuda_pending_20261116_v2.tar.gz`
- `bcsp_spcg_cuda_pending_20261116_v2.tar.gz.sha256`
- `bcsp_spcg_cuda_pending_20261116_v2.tar.gz.bytes`
- `bcsp_spcg_cuda_pending_20261116_v2.tar.gz.contents.sha256`

归档6,744,099bytes，14个拟安装文件＋1份映射。内容清单采用UTF-8，支持其中的中文计划文件名。

v1打包时使用ASCII写中文成员名清单失败，已保留失败运输产物；v2仅补全运输清单编码，源码、CPU结果和request字节均未改变，没有重跑测试。该失败属于本机打包，不是SPCG或CPU验证失败。

后续需上传核验及单独完整哈希执行授权，才可按冻结映射不覆盖安装、重新确认启动条件并执行唯一一次准入。失败停止；成功后仍需正式只读post-CUDA冻结审计，才可准备训练请求。
