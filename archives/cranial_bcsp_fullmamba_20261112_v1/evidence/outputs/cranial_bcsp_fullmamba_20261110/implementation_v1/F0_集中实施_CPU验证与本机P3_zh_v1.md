# F0-P-v2集中实施、CPU验证与本机P3 v1

2026-11-10。**隔离实施和本批44项人工CPU契约验证通过，本机implementation P3完成；native CUDA准入尚未执行。**

## 四个隔离文件

- bcsp_f0_decoder_v1.py：八层self→conditional→FFN；双向query每层共享参数，prefix单向完整512；首层graph和concat merge保留；384维、PE1152参数、无跨病例cache。原调用签名保留，拒绝denoise，完整轨迹仅eval。
- bcsp_f0_factory_v1.py：调用原P1/M0构造后隔离安装16个decoder mixer及共享PE；新seed20261110，不改原公共RNG；原Norm/FFN/graph/merge按重映射state键精确核对，decoder外初始state保持。生产native入口与显式人工fixture入口分开。
- bcsp_f0_runtime_adapter_v1.py：8k输入/目标校验、GT仅送loss、轻量detached矩日志、生产CUDA准入守卫。正式生命周期委托已绑定的原P1 runtime，保留3900步/100遍/31200曝光/300 drop；本文件不是可直接启动训练的launcher。
- test_f0_cpu_v1.py：从冻结源码AST加载真实CrossAttnBlockApi、PointTransformerDecoder、Attention/CrossAttention、DynamicGraphAttention及Mlp，使用纯CPU cdist KNN和明确标记的因果mixer；不导入完整项目或native Mamba。

## 验证结果

仅运行一批44项，PASS，PyTorch2.5.1 CPU，0 optimizer step，无失败后自动修复重跑。

覆盖：共同初始化和RNG不变、decoder16 mixer/PE1152参数、保留首层两graph、八层结构及真实FFN/残差、256/512扫描长度、无已注册旧Attention模块、query排序/逆序/32点slot、成对memory重排、完全tie确定性、batch2独立性及batch8接口、NaN/FP64/shape/denoise拒绝、eval-only full trace、条件/PE/各mixer的有限非零人工梯度、早段prefix扰动对分支出口的影响、原优化器组无重复/no-decay旗标、8k调用与GT隔离及轻量日志detach。

这里的模型/生成头和scalar loss是人工fixture。真实母版block、graph、Norm、FFN得到实际CPU调用，但完整生产grouper/PointNet2、native SSM和8192点Chamfer未运行。不能把CPU的条件响应视为native SSM状态传播证据或科研收益。

## 源码与边界

静态审查和P3再次核对Stage A所绑定7个原文件哈希一致；原P1/P2、母版、数据和评分未改。本轮只新增四个隔离代码文件及测试/审阅证据，无服务器访问、CUDA、真实点集/checkpoint、部署、训练或execution request。

在未来真实短入口中，必须绑定本四文件及所有实际父依赖哈希、使用非fixture的native工厂。runtime的parent_sha256参数需要来自冻结执行合同；不能把调用者随意给出的字符串当作可信准入。本轮不伪造CUDA回执，不将状态字符串等同于完整执行授权。

## 下一步与剩余准入

下一步可单独准备专用人工CUDA短入口及待授权范围，沿用正式计划：4次完整F/B，加6次decoder-only F和1次decoder标量B，全部0 optimizer step；不重复通用环境库存。不立即运行GPU，也不创建训练request。

该步骤应覆盖实际native Mamba、完整冻结loss、batch8资源、无attention动态路径、短卷积边界与SSM条件区分及状态/RNG口径。CPU artificial结果不能代替这些证据。实际3900步、完整数据/批次、Native E/J及风险只能由后续分别授权的真实实验建立。

机器P3：implementation_P3_v1.json；测试：artificial_cpu_batch_v1/result_v1.json；源码与证据哈希：delivery_manifest_v1.json。
