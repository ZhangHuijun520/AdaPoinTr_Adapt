# RIVE四模型Native预测正式只读冻结审计 v1

结论：通过，35项汇总检查全部通过。11次有界只读调用均退出0，无本机超时。未修改服务器、加载checkpoint、读取GT或运行新forward／评分。

## 完整性

退出码0、tmux及worker退出；420条预测和420条预先claim逐项对应，四模型各105例。病例、来源、折、归一化、输入／checkpoint哈希及实际预测大小／SHA256匹配冻结index。420份NPZ的9数组、FP32、形状、有限值及Qraw+delta/coarse、Q0+delta0/Q1、Q1+delta1/Q2关系通过。无context或decoder trace。

完整输出434文件、19个安装／控制文件及目录集合精确匹配。审计前后全部内容哈希及内容相关属性相同，排除atime干扰。420条几何汇总及RF阶段质心重算一致。

四模型记录的参数／持久状态与CPU、CUDA、Python、NumPy RNG前后指纹一致，均为eval/inference_mode且无训练、loss、backward或BNCal。审计核验的是既有指纹记录，未重新加载模型；不是对所有随机性的额外保证。

845条资源记录重新核算通过。SMI峰值720MiB，Torch allocated峰值244786176字节；记录最大耗时107.68秒。

## 归档

426个安全常规归档成员与原文件及完成清单逐字节大小／哈希一致，未落盘解压。压缩包实测45697569字节，SHA256 `4be9df6d5a5bf5620a14a6242c3c145fb198ae050e4a8abbef75247eafbe8b07`，三个校验文件精确字节一致。

服务器目录：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_fourmodel_native_development_20261115_v1`。

建议将以下四文件下载至 `E:\ResearchBackups\AdaPoinTr\BCSP_FULLMAMBA_SCQ_RIVE\2026-11-16_native_development_eval`：

- `development_predictions_v1.tar.gz`：45697569字节，SHA256 `4be9df6d5a5bf5620a14a6242c3c145fb198ae050e4a8abbef75247eafbe8b07`。
- `development_predictions_v1.tar.gz.bytes`：9字节，SHA256 `5708feafeab95cff974c9165d1f23b66fe9c948a4be597831095f9c031d1a487`。
- `development_predictions_v1.tar.gz.sha256`：100字节，SHA256 `7f591d375f4950c8bbbc4a0092d6fef89a4ee0d6bb291ad4db02b74b9b9b6cbf`。
- `development_predictions_v1.tar.gz.contents.sha256`：49290字节，SHA256 `57257cb166bb5ad321f335193fd46488b356b04fab114d676040f5bddcaa9e0c`。

## 下一步

下载后进行本机大小／哈希／归档清单核验，再准备统一CPU评分。当前仅生成下载清单，没有执行预测归档下载、没有认证本机备份、没有启动评分或创建评分request。尚不能据本次完整性审计判断Static/Requery补全效果。
