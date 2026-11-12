# F0 新容器最小重绑定与待授权说明 v2

日期：2026-11-11。用户确认当前容器已换为 `zv9bqd-0` 后完成只读证据核验与本机身份／路径重绑定。未在服务器写入文件、安装工具、加载模型、解码点集或运行 forward。

## 📋 核验结果

| 项目 | 结果 |
| --- | --- |
| hostname／UID | shu-common-25721452-notebook-zv9bqd-0／1000 |
| Python | /opt/conda/envs/adapointr-mamba/bin/python3.10，3.10.20 |
| GPU | NVIDIA GeForce RTX 4090 D |
| GPU UUID | GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed |
| 驱动 | 575.51.03；原绑定为570.190 |
| 物理显存／查询时占用 | 24564 MiB／0 MiB |
| 项目剩余磁盘 | 12758024192字节，约11.88 GiB |
| 原上传包及三个校验文件 | 匹配；原归档14成员、13个安装目标的内容绑定一致 |
| 原安装、控制、启动claim及结果路径 | 均不存在 |
| 新v2安装根及结果根 | 均不存在，父路径未发现符号链接 |
| 复用源码／provider／依赖 | 逐精确路径大小及SHA256匹配；包括Mamba二进制，无ML导入 |
| 两份checkpoint及210份输入 | 大小及SHA256均匹配；未反序列化或解码 |
| UTC | 原精确链接及目标绑定一致 |

四次有界只读调用均成功。实际命令858／1902／2034／1546字节，均不超过2048字节。源码／依赖阶段读取711911941字节，用时约2.76秒；checkpoint／输入阶段读取990623904字节，用时约8.25秒。所有过程未调用CUDA或执行实验。

证据见 `resource_rebind_audit_receipt_v2.json`、四个 `*_result_v1.json` 及原始 stdout／stderr 字节文件。哈希读取只证明对应时刻文件内容一致；实际执行前仍需重验身份、空闲状态及目标不存在。

## 🔧 重绑定范围

模型及生产预测入口字节不变，继续复用已通过的42项CPU检查与本机P3；本次不重跑CPU测试或GPU preflight。

只更新hostname、GPU UUID、驱动记录、CUDA_VISIBLE_DEVICES，以及版本化run ID、安装／输出／控制路径和tmux名称。新增只读核验回执与重绑定补充说明，供v2 request绑定。静态差量核验和最终序列化request的纯内存authorize检查均通过，未创建真实执行授权文件。

科研范围仍为Fold C／D各105例，共210次Native forward；8k输入／8k输出；全210例保存coarse；同次forward保存20例上下文、10例逐层轨迹。模型、权重、数据顺序、归一化、数值设置、所有资源阈值、失败即停和禁止自动重试合同均不变。

旧request SHA256 `8c2f849a1e3cb9cfbaac5e501f09647fa0de894491501e0d0bd48e09b9e9ee03` 在首次hostname核验处停止，未安装、未创建claim、未启动。旧授权不能用于新身份v2 request。

既有GPU准入来自原UUID／驱动。新容器文件哈希一致不等于当前CUDA已验证；按既定不重复preflight范围，实际新设备路径在单独授权后的首个Native forward中接受验证，异常立即停止。当前不能判断补全质量。

## 📦 v2 待授权材料

新request：`transport_payload/F0_CD_native_prediction_execution_request_v2.json`，15576字节，状态 `AWAITING_EXPLICIT_USER_AUTHORIZATION`。

完整SHA256：

`f1a222d9268adf33ffc32127bb62ad82c6b6cdf20748b0a68e8f2c1b97f13431`

请将本目录以下四文件上传至服务器 `/home/jovyan/`：

1. `bcsp_f0_CD_native_prediction_pending_20261111_v2.tar.gz`
2. `bcsp_f0_CD_native_prediction_pending_20261111_v2.tar.gz.sha256`
3. `bcsp_f0_CD_native_prediction_pending_20261111_v2.tar.gz.bytes`
4. `bcsp_f0_CD_native_prediction_pending_20261111_v2.tar.gz.contents.sha256`

归档68663字节，SHA256 `cb3c196c3620715dd068e23f4a002d032842fdde69da9dbfceb2e9df56d862a8`。包内15个精确不覆盖安装目标及映射，已本机回读校验。

新安装根：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_CD_native_prediction_20261111_v2`。

新结果根：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_native_development_20261111_v2`。

新tmux：`bcsp_f0_CD_native_eval_20261111_v2`。

上传后需对v2完整request哈希单独执行授权，才进行重验、不覆盖安装、回执→runtime→launcher单向材料化及唯一一次启动。本轮未自动继承旧执行授权，未运行训练、BNCal、评价或评分。
