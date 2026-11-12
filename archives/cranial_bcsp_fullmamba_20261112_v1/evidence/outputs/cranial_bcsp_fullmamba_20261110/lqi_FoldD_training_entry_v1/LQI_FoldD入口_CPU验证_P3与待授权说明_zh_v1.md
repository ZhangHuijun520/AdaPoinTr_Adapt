# LQI Fold D最小入口、P3与待授权request

状态：已完成最小入口适配、CPU验证、本机P3和最终真实元数据完整authorize复核；未部署或训练。

唯一新增生产入口为`bcsp_lqi_foldD_training_entry_v1.py`。沿用LQI decoder/factory及已安装C折bridge，不复制修改bridge；仅增加D分派及绑定冻结C折训练证据和既有D参考合同。保持8k→8k、seed0、315病例/63来源、batch8、100次遍历、3900步、31200曝光和300丢弃。不依据C折训练loss调参、筛病例或warmstart。

CPU首批因fixture路径混用在元数据读取处停止，记录保留；生产入口不变，仅修正测试引用并使用新目录。修正后29项通过，覆盖真实准入/C折证据/D参考/顺序的完整authorize及错误拒绝，人工8k batch8 surrogate模型forward/backward、几何日志和3900计数守卫。CPU不代表实际训练成功，没有重复GPU preflight。

只读核验九个元数据/复用工具哈希、315个D折点集存在性/大小及资源/新目录；未打开真实数组。315份payload原始SHA256必须在获得执行授权后、安装和启动前重验。

最终request状态：AWAITING_EXPLICIT_USER_AUTHORIZATION。

完整SHA256：`41e53b39f099e502e3a1abebab952b9ea98acd58d1616e128312a0685a6bb517`。

上传本目录`bcsp_lqi_FoldD_training_pending_20261111_v1.tar.gz`及`.sha256`、`.bytes`、`.contents.sha256`四文件至`/home/jovyan/`。包内17文件，不含数据或权重；沿用11个C折型文件并增加6份C折证据和1份D参考，但bridge复用服务器既有版本而不重复安装。

安装根：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v1`。

输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldD_seed0_train_20261111_v1`。

单独明确授权完整request哈希后，才可重验、不覆盖安装和单次tmux训练。失败即停，不自动重试/resume，不进入BNCal或评价。生产参数/优化器/LR/BN及原资源阈值均不变。
