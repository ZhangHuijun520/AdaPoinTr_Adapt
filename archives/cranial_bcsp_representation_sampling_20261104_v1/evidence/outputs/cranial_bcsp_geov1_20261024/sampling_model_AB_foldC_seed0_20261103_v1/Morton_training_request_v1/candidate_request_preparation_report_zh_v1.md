# 固定8k采样对照：Morton候选臂request准备记录 v1

日期：2026-11-03。状态：AWAITING_EXPLICIT_USER_AUTHORIZATION。本记录不是执行授权。本轮只生成本机元数据和小运输包，没有服务器写入或模型调用。

## 准入依据与固定范围

V1基线正式只读审计v2的38项检查全部通过，审计JSON SHA256：7a6c002e45160cfdf11cb53686639f61d945a1255460bfafa271c75af63e17b1。基线实测checkpoint SHA256为bef638c807de8ea41f79862311138f42d9993dcc6fb5a09d5321642a57acfa51。初始化、实际批次顺序、31200次曝光/300次丢弃已冻结；模型/运行时/provider及候选315文件匹配。

仅申请一次Morton_area_stratified8k候选训练：SkullBreak Fold C，63来源/315训练例，seed0，8k输入/8k输出，batch8，100遍/3900更新。复用与V1相同的B0 AdaPoinTr、全key chunk256 KNN、原生PointNet2、cdist loss、FP32 deterministic/TF32 off、优化与LR/BN时序、目标/归一化/共同点序及完整病例顺序。没有Mamba改动、Fold D、额外seed或其他数据集训练。

候选从scratch初始化，严禁加载V1 final权重。入口在第一步前检查候选的参数和持久状态指纹与已审计基线一致，且同identity/config/runtime/order；若不符停止，不自动重试。基线的最终checkpoint在这里仅作证据哈希引用。

## 当前唯一候选request

文件：candidate_training_execution_request_v1.json。

完整SHA256：`d4a44a990c0b3f0b91522c6f9803074a34e6c3803c243bf08e8a46ace42eeae3`。

状态保持AWAITING_EXPLICIT_USER_AUTHORIZATION。尚未材料化任何候选授权、runtime、launcher或启动标记。已有初始化凭据是审计证据，不是授权文件。

Run ID：bcsp_sampling_ab_foldC_Morton_in8192_out8192_seed0_train_v1。

未来control：/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_sampling_ab_foldc_seed0_v1/control_Morton_v1。

未来输出：/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_sampling_ab_v1/bcsp_sampling_ab_foldC_Morton_in8192_out8192_seed0_train_v1。

未来tmux：bcsp_sampling_ab_foldc_morton_seed0_train_v1。

同一GPU/软件/源码条件是配对要求。若容器、GPU、代码或数值条件变更，不得自动继承本次准入。执行时应刷新身份、空闲GPU、磁盘、复用文件hash及新路径缺省。仍使用原资源监测阈值，不添加procfs/cgroup框架或放松科学合同。

## 只需上传小型控制包

候选315点集和代码已在服务器，本次不重复运输或安装它们。小运输包只有三个元数据成员：paired_initialization_receipt_v1.json、qualified_training_receipt_v1.json、training_entry_request_v1.json。它们未来仅安装到全新control_Morton_v1目录，采用不覆盖写入；不改旧V1目录或结果。

请把以下五文件上传到服务器/home/jovyan；本机文件位于本目录transport_v1。

| 精确文件名 | bytes | SHA256 |
|---|---:|---|
| bcsp_sampling_ab_foldc_morton_control_v1.tar.gz | 3311 | `af4b57c7ab6e27b98c89e083fd80eb1f4af486ef9bf0f64cf7352972406c71d0` |
| bcsp_sampling_ab_foldc_morton_control_v1.tar.gz.sha256 | 114 | `5b41ad1b990075319567979a47e95d8040d62fc4124997806e31f26f329f3efc` |
| bcsp_sampling_ab_foldc_morton_control_v1.bytes | 5 | `835897ac3a5015bd5134d02adb899004daba0cf7312a764e019dbf0d2e36b54f` |
| bcsp_sampling_ab_foldc_morton_control_v1.contents.sha256 | 302 | `e1cd6d03e5548dc1079f5214e882f9647bafbe12af42a32b9826fcca58780607` |
| bcsp_sampling_ab_foldc_morton_control_v1.contents.sha256.sha256 | 123 | `17f015660c7a7d12a6a148791d38508b4618d9ec962a0ed8d20fe00ae170a00c` |

用户另行明确批准上述完整request SHA后，才允许核验上传包、不覆盖安装三元数据、按授权→计算SHA→runtime→单次launcher顺序材料化并唯一一次tmux训练。未授权时不得执行。失败即停，不重训V1，不自动resume/retry，不进入BNCal或development evaluation。

## 本机接口核对与限制

实际新生成的qualified receipt、315例选择、顺序、资源绑定及配对初始化字段通过现有入口的本机读者合同检查。未来路径仅映射到本机同字节文件，授权fixture只在RAM中，未创建真实授权文件。没有重建模型，亦没有新CUDA/forward验证；候选真实初始化核对发生在未来获授权运行的第一步之前。

两臂训练冻结后才能单独授权同105病例的配对评价。几何覆盖改善及基线训练loss均不能预先证明候选模型效果更好。
