# 四模型、两固定病例实际取点轨迹执行报告

日期：2026-11-02。request SHA256：`752bc7b45dab96f9cee90057e1180526126121da9ee1fb7d5b7b8365588c44bf`。

## 执行结果

在当前容器 `shu-common-25721452-notebook-v2iwsa-0`、GPU `GPU-34a1b996-2bd7-88e6-9dca-164b718caea6` 上完成唯一一次 tmux 诊断。session：`bcsp_proxy_trace_20261102_v1`；worker PID：734；退出码 **0**。

| 模型 | 固定病例 | forward | 新旧预测数组完全相同 |
|---|---|---:|---|
| C_8192 | train__001__bilateral | 1 | 是，最大绝对差0 |
| C_16384 | train__001__bilateral | 1 | 是，最大绝对差0 |
| D_8192 | train__004__bilateral | 1 | 是，最大绝对差0 |
| D_16384 | train__004__bilateral | 1 | 是，最大绝对差0 |

没有 cross-fold 见过来源的额外推理。没有第二次对照 forward；与此前已保存的同模型同病例预测做逐元素比较。模型参数及 BN 状态哈希前后相同，CPU RNG 前后相同，训练更新、BNCal、loss、backward 均为0。GPU RNG 未记录，不能宣称完整 CUDA RNG 不变认证。

## 已记录与核验的实际轨迹

每份 trace NPZ 含18数组：

- FPS512、FPS256 各自的实际输入坐标、实际索引、实际输出坐标，共6数组。
- 四次 graph 调用的 query/key 坐标及实际 KNN 索引，共12数组。

四份轨迹都通过：512/256 索引形状和范围检查；使用实际索引 gather 的坐标与记录的输出坐标精确相等；四个 KNN 数组的 query 数量、k=16 和 key 索引范围检查。

记录器调用原 FPS/KNN 后返回原结果，仅复制轨迹至 CPU；结束或异常后恢复函数。13项本机人工合同检查支持其接口合同，实际 CUDA 的轨迹完整性及历史输出精确相同进一步支持本次观察未改变所核查的最终预测。仍不能由此证明实际特征因果关系。

## 安装及资源核验

运输包 SHA256 匹配，安装目录原先不存在；在新目录不覆盖写入4文件，安装哈希匹配。四 checkpoint、四 input 以及原执行依赖哈希匹配冻结记录。Python3.10.20、torch2.4.1+cu118、numpy2.2.6、timm1.0.27 与预期一致。900秒外部 timeout，原显存/RSS阈值保留；全部已记录资源条件通过。

资源记录实测：device memory 采样峰值734 MiB；torch peak allocated 247,680,000 bytes；RSS采样峰值1,492,156,416 bytes。RSS和SMI数据是采样峰值，不是连续峰值证明。

首次本机查询漏解码、一次长批量只读查询超时，均未启动模型；修正并拆为短查询后通过。正式GPU运行只启动一次，没有失败重试。

## 只读运行后核验

重新确认退出码0、四次forward、四模型状态/CPU RNG、完整清单，重新计算归档及11个成员哈希，均通过。资源日志所有 checks 为true。

## 归档及下一步

服务器目录：
`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/actual_proxy_trace_20261102_v1/`

手动下载四文件：

1. `development_predictions_v1.tar.gz`
2. `development_predictions_v1.tar.gz.sha256`
3. `development_predictions_v1.tar.gz.bytes`
4. `development_predictions_v1.tar.gz.contents.sha256`

归档 bytes：**4,271,350**。

归档 SHA256：`637cc82bb5ce20f3ef2f115df5147accf5792e300b095f6d792e07c4840d3181`。

建议本机位置：`E:\ResearchBackups\AdaPoinTr\BCSP_INPUT_DENSITY_V1\2026-11-02_actual_proxy_trace`，避免与原420预测归档混放。按用户既定边界，由用户完成下载；本次未将服务器归档自动视为已有本机备份，也未删除服务器产物。

当前完成的是实际轨迹获取与完整性核验，**尚未完成实际 proxy 对真实 J 的覆盖及邻域传播分析**。待本机取得四文件并验证后，可与已存在的两例 reference bank 配对，逐阶段比较输入→512坐标→256坐标及真实邻域并集的 J 覆盖与支持保留；无需再次GPU执行。分析仍须区分坐标/邻域保留与学习特征因果，不直接据此决定重训。
