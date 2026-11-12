# F0 两折 Native 预测正式只读冻结审计报告

日期：2026-11-11。正式结论：FORMAL_F0_CD_POST_PREDICTION_FREEZE_AUDIT_PASS，46项交叉检查全部通过。

本报告对应唯一获授权的v2 request SHA256：

    f1a222d9268adf33ffc32127bb62ad82c6b6cdf20748b0a68e8f2c1b97f13431

本次审计独立于此前完成状态观察。服务器操作全部只读，没有追加forward、加载模型、训练、BNCal或评分。

## 📋 完整性与调用计数

| 核验项 | 正式结果 |
| --- | --- |
| 容器／用户 | shu-common-25721452-notebook-zv9bqd-0／UID1000 |
| 退出／进程 | 退出码0；worker与固定tmux均不存在 |
| 模型与顺序 | C_F0、D_F0，各105次，匹配原开发顺序 |
| 调用日志 | 210条唯一预先claim、210条预测清单、210条几何记录 |
| 预测 | 210份；均含FP32有限值dense 8192×3和coarse 256×3 |
| 上下文 | 固定20份；F／S／z／Q／X字段、形状及有限值通过 |
| 轨迹 | 固定10份，共80层；每份40个FP32有限张量 |
| 资源日志 | 恰好423条，阶段及forward计数顺序匹配 |
| 结果目录 | 精确254个常规文件、5个目录，无额外或失败产物 |
| 安装／控制 | 15个安装文件匹配冻结映射；控制目录精确6文件 |
| 归档 | 246个成员；大小／SHA256与现存文件逐一匹配 |
| 冻结资产 | 新核验265文件，覆盖两权重、210原输入及所需源码／provider／依赖／配置 |

审计前后库存、inode／mode／size／mtime／ctime指纹和254个结果SHA256均一致，排除atime干扰。复制到本机项目内的34份受限元数据与新测哈希匹配，总计1370171字节。

## 🔗 授权链与病例绑定

核验了request哈希、独立明确授权回执、runtime对回执SHA256的单向绑定、唯一claim，以及startup中的launcher／runtime／authorization哈希。在本机用冻结入口重新渲染launcher，结果与实际launcher逐字节一致；没有执行新launcher。

全部预测与固定run、fold、source、case、输入哈希、checkpoint哈希及D-only归一化元数据一致。每折21来源×5缺损类型，未改变病例或顺序。

| Fold | 重新实测checkpoint SHA256；各478810419字节 |
| --- | --- |
| C | 4fd73dd8c265781225ba63a712a5589b175c94f0ea0878a69ebf466265ebebe9 |
| D | c4f29a8df3e36af2c87a20dc4888eb4b6a344bb448baa6403fb6c9c86023edaa |

checkpoint仅作字节哈希核验，未反序列化。原输入NPZ仅作身份核验，未读取GT数组。

## 🧪 缓存、轨迹与几何日志

20份context的Q与已保存预测coarse逐元素相等；10份trace首层input与对应X相等，且每层output与下一层input逐元素衔接。30条缓存文件记录与正确病例、同一次forward索引、输入／权重哈希和归一化一致。

z仍定义为query前的backbone.global_feature，区别于decoder后rebuild_global_feature。审计核验绑定实现、字段声明及数组合同，不重建模型计算z。

从已保存Q／P复算全部210例的质心、包围盒、回转半径、协方差特征值和dense相对coarse位移统计，匹配几何日志，最大绝对统计差为0。这是预测内部一致性核验，不是GT精度评分或Oracle配准。

## ⚖️ 状态、RNG与资源

两模型均为eval／inference_mode，各105次；BNCal、optimizer和backward均0。每模型前后完整state_dict指纹一致，覆盖参数及持久BN状态。

CPU／CUDA RNG为合法SHA256且前后一致。Python随机状态和NumPy MT19937序列化状态按实际格式核验，前后相同，未错误要求其为64字符哈希。状态／RNG结论来自冻结代码及运行保存的指纹，本次未重建模型张量独立求指纹。

构造证据匹配真实F0版本、M0 encoder六处分支、decoder十六个新mixer、共享坐标PE1152参数及decoder seed20261110；artificial_fixture为false，注册清单无禁止attention模块。不宣称已审计所有opaque底层内核。

全部423条资源子条件已独立复算并通过，失败列表为空。

| 资源 | 采样峰值／实际值 | 合同 |
| --- | --- | --- |
| RSS采样峰值 | 1931440128字节，约1.80 GiB | 8 GiB |
| Torch allocated峰值 | 241075712字节 | 20 GiB |
| Torch reserved峰值 | 289406976字节 | 20 GiB |
| SMI显存采样峰值 | 725 MiB | 22528 MiB |
| 监测累计时间 | 115.403秒 | 7200秒及外部timeout |
| 记录最小磁盘余量 | 12576620544字节 | 至少4 GiB |
| 归档后全结果大小 | 362016527字节，约345.25 MiB | 1 GiB |

RSS／SMI为采样值；Torch为记录的累计峰值。沿用监测与超限停止合同，不宣称专属硬隔离。PID只作诊断，不能证明命名空间所有权。

## 📦 冻结归档及下载

服务器结果目录：

    /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_native_development_20261111_v2

从此目录下载四文件：

1. development_predictions_v1.tar.gz
2. development_predictions_v1.tar.gz.sha256
3. development_predictions_v1.tar.gz.bytes
4. development_predictions_v1.tar.gz.contents.sha256

压缩包大小180647685字节，约172.28 MiB。完整SHA256：

    32b80af60b4e3819e98c6bc096282e2bb71e3fe3b253e11c2a1623ec5e4aaac6

四文件的精确大小、SHA256及服务器绝对路径见download_four_files_manifest_v1.json。建议本机长期保存目录：

    E:\ResearchBackups\AdaPoinTr\BCSP_FULLMAMBA_F0\2026-11-11_native_development_eval

本次只把审计元数据复制到本机项目内，未下载预测压缩包，不能视为已有本机长期归档。

## 📚 后续与证据

机器可读结果为post_prediction_freeze_audit_result_v1.json。audit_scope_v1.json、各阶段result、原始stdout／stderr及downloads保存回读证据。本次仅在本机保存审计代码和结论，没有写入服务器审计文件。

下一步下载四文件，本机核验后，再准备与冻结T0／M0基线的统一CPU评分。当前证明产物与执行证据完整、一致，尚不能判断完整骨块、接口吻合或退化风险是否改善。未执行未来30次decoder机制干预。

精确代表ID的预测前登记偏差继续披露；同折五类代表缺损来自同一来源，不能当作五个独立患者。既有GPU准入位于旧UUID／驱动，本次Native任务已在当前绑定设备成功完成，但不外推通用内核确定性。
