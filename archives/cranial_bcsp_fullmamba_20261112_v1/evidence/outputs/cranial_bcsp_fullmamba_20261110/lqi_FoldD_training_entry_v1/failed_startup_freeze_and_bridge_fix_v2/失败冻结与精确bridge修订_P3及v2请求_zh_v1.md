# Fold D失败冻结、精确bridge读取修订与v2待授权请求

本轮完成正式只读失败冻结、单路径实施、实际文件策略CPU回归、新P3和最终完整authorize复核。未部署新版、未运行GPU或训练。

失败冻结：现有输出只有launch.log、worker.pid、exit_code.txt、startup_failure.json四文件及tmp目录；连同23个安装/控制文件共27个文件，前后哈希及内容指纹一致。退出码1，worker/tmux结束，无metrics、checkpoint或optimizer step。绑定源码在bridge导入阶段停止，尚未构造/运行训练模型；CUDA上下文可能已经初始化，不能声称此前完全没有CUDA API。审计辅助首轮将tmp目录误计为文件，保留失败记录，修正精确文件数后完成核验，未修改服务器。

生产修改仅为新增`Path(q['implementation']['bridge']['path'])`到read_roots。不放行其父目录、不改bridge内容或hash、模型、loss、数据、初始化、顺序及3900步合同；原v1源码/request及已尝试记录保留。

8项CPU检查通过，采用真实继承文件策略和最终入口source_module：复现旧策略拒绝，在新策略下真正导入精确bridge，且仍拒绝写源码和相邻未绑定文件。测试不运行模型或训练。原29项CPU及正式CUDA准入继续作为继承证据；本轮未重跑它们。

新版request状态：AWAITING_EXPLICIT_USER_AUTHORIZATION。

完整SHA256：`317870937023da177930437f39b3179956e72e3773f53f4010eb86f25ed21da9`。

本机`pending_transport_v2`内四文件需上传至`/home/jovyan/`：`bcsp_lqi_FoldD_training_pending_20261111_v2.tar.gz`及`.sha256`、`.bytes`、`.contents.sha256`。压缩包20,065bytes，内含4个新安装文件；模型、数据、bridge及C折证据复用既有服务器资产，执行前仍须重验。

新安装根`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v2`，新输出根`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldD_seed0_train_20261111_v2`。全新tmux、回执/runtime/launcher/claim路径。只读确认时新根不存在；正式执行前须再次核验。

模型及科研绑定逐项与v1完全一致；只改变entry、P3/readiness与运行路径。最终request的完整authorize使用实际冻结元数据和证据在本机镜像复核通过，授权对象仅存在于审查内存，未生成真实执行回执。

上传后须单独授权本v2完整哈希，才可不覆盖安装并启动唯一一次新训练。旧v1授权已消耗；不得复用。失败即停，不自动重试或resume，不进入BNCal或评价，不重复GPU preflight。
