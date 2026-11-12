# LQI人工CUDA零更新入口与待授权范围 v1

日期：2026-11-11。状态：**入口、针对性CPU验证、本机P3及最终待授权request已完成；尚未执行CUDA。**

## 1. 唯一执行合同

只构造一个F0-LQI-v1模型，按已冻结公式和原种子初始化，不加载训练checkpoint。

| 阶段 | batch | 完整forward | 完整原loss | backward | optimizer step |
|---|---:|---:|---:|---:|---:|
| eval模式 | 1 | 1 | 1 | 1 | 0 |
| 训练模式准入 | 8 | 1 | 1 | 1 | 0 |
| 合计 | — | 2 | 2 | 2 | 0 |

训练模式仅检查实际loss、梯度及BN临时行为，不构造optimizer，不开展训练。每阶段开始／结束及失败时恢复完整state_dict、BN缓冲与momentum、模块training标志，以及Python／NumPy／CPU／CUDA RNG；清空梯度。参数不得更新。

没有额外warmup、重复forward、decoder-only调用、旧prefix干预、真实数据读取、checkpoint读取、BNCal或开发集预测。两次完整forward应合计72次原生SSM forward钩子记录，覆盖22个原生Mamba模块；backward的内部kernel工作不被混称为额外模型forward。

人工输入及target分别使用NumPy default_rng种子20261110和20261112，均匀分布[-0.5,0.5]、FP32、形状8×8192×3；batch1取第一行。该输入仅验证执行与数值路径，不模拟真实骨组织，也不提供补全质量证据。

## 2. 后端与准入证据

- 使用现有Python3.10 native PointNet2 provider、真实Mamba2.3.1与已冻结CUDA扩展；禁止下载、编译、重装或升级。
- 完整loss明确沿用已授权的PyTorch `cdist` Chamfer分支，拒绝悄悄切换到compiled Chamfer。完整母版get_loss的原输出合同、原loss配置和人工target均保留。
- 保持FP32、TF32=false及原严格确定性设置；接受并披露既有有限梯度非确定性，不要求梯度逐位相等。本轮没有重复测量或新的梯度容差扫描。
- 全部已出现的参数梯度必须有限；35个模块组梯度范数必须非零，覆盖coarse、PE、reduce_map、6个encoder mixer、16个decoder mixer、8个norm_v、increase_dim和decode_head。
- 检查正式母版参数数量仍为39,903,169；检查候选版本、原生Mamba来源与调用数，不允许误加载旧F0 decoder。
- 保留原动态无注意力算子检查及模块清单边界：不能把未发现已知attention算子扩张为对不透明扩展内部语义的完整证明。

## 3. CPU与本机P3完成情况

一批针对性人工CPU合同验证共29项通过。覆盖实际authorize、范围漂移拒绝、单向runtime、2F/2loss/2B及batch1/8控制流、35组梯度检查、成功／失败后的状态恢复、首错停止、POSIX launcher、父目录先于重定向，以及候选四源码在精确文件策略下的真实加载分派。

CPU完整loss控制流使用便宜人工MSE fixture，**没有实际执行CUDA或生产Chamfer**。它与此前LQI公式的55项CPU断言互补，不重复前一批测试，不证明实际Mamba/CUDA或科研效果已经通过。

`entry_P3_v1.json`状态为`LQI_CUDA_ENTRY_LOCAL_P3_PASS`，绑定最终入口、decoder、factory、CPU结果及既有55项实施证据。最终request又用实际authorize路径和renderer作了本机合同复核；人工授权对象只存在于冻结脚本内存中，没有生成可执行授权回执、runtime或launcher。

## 4. 服务器只读就绪核对

当前核验容器：`shu-common-25721452-notebook-zv9bqd-0`，UID1000。

GPU：RTX4090D，UUID `GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed`；driver575.51.03，SMI总显存24564MiB。核对时显存占用0MiB，项目磁盘可用11,512,315,904bytes。

继承母版、provider、相关依赖与精确UTC资源共45个文件核对通过，哈希读取711,206,393bytes；没有导入ML、读取真实payload、写服务器文件或调用CUDA。新安装根与输出根不存在。执行前必须再次重验，当前就绪证据不替代启动前核对。

固定预算：1800秒、RSS8GiB、Torch allocated/reserved峰值20GiB、SMI22528MiB、输出1GiB、磁盘余量4GiB。沿用2秒监测和单次SMI查询10秒超时，PID仅记录诊断，不恢复宿主procfs归属硬断言。资源监测不是专属cgroup硬隔离保证。

## 5. 待授权request与运输包

request状态保持`AWAITING_EXPLICIT_USER_AUTHORIZATION`。

完整SHA256：

`d1324b1b754e2eea91e00ea5ede802c6bd506815b82db82f3c41a070811e9812`

本机目录：

`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\cranial_bcsp_fullmamba_20261110\lqi_gpu_admission_v1\pending_transport_v1`

上传以下四文件到`/home/jovyan/`：

1. `bcsp_lqi_artificial_cuda_pending_20261111_v1.tar.gz`
2. `bcsp_lqi_artificial_cuda_pending_20261111_v1.tar.gz.sha256`
3. `bcsp_lqi_artificial_cuda_pending_20261111_v1.tar.gz.bytes`
4. `bcsp_lqi_artificial_cuda_pending_20261111_v1.tar.gz.contents.sha256`

压缩包21,023bytes，SHA256：`d8dfde92d514cb158393e6d32da39afaf8aacc7e27169225e0d716f1bf4f3bcd`。共9个成员：8个拟安装文件与不覆盖安装映射，不携带数据、checkpoint或依赖二进制。

服务器拟安装根：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_cuda_20261111_v1`。

拟输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_artificial_cuda_20261111_v1`。

固定tmux：`bcsp_lqi_cuda_20261111_v1`。日志、PID及退出码分别为输出目录中的`launch.log`、`worker.pid`、`exit_code.txt`。

## 6. 下一步及权限边界

手工上传后，单独明确授权request完整SHA256，才可按冻结映射核验、不覆盖安装8文件，并依次材料化授权回执→计算回执SHA256→runtime→launcher→单次claim→唯一一次tmux启动。父目录须先创建／核验，再进行日志重定向；本机调用保留原始字节并显式返回退出码。失败即停，不自动修复、重试或resume。

CUDA执行后先进行独立正式只读冻结审计，核验清单、哈希、2F/2loss/2B计数、72个原生调用、完整梯度、BN／state／RNG恢复及显存记录。通过也仅说明该人工输入、该后端和预算的执行准入，不证明真实数据效果，不自动创建或启动训练。
