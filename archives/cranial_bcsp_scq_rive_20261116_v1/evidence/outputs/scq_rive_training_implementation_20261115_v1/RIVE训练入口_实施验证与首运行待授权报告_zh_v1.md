# SCQ-RIVE训练调用层实施、CPU验证与首运行request

日期：2026-11-15。状态：**implementation-only完成；73项人工CPU检查一次通过；P3完成；仅首个Static_C request待授权。**

## 1. 本次交付

新增三个隔离源码文件，未改动模型或旧工具：

- `bcsp_rive_training_entry_v1.py`：RIVE模式A的C/D、Static/Requery调用层。
- `bcsp_rive_training_bridge_v1.py`：双臂bridge，校验授权臂、设备类型和原runtime哈希后委托原训练生命周期。
- `test_rive_training_cpu_v1.py`：本轮针对性人工CPU验证。

原RF/SCQ公式、encoder、LQI、原训练runtime/contract/budget、数据和初始值均保持原哈希。未新增通用库存、传输或审计框架；没有连接服务器、部署、创建生产执行控制或启动实验。

## 2. 最小接口收敛

### 2.1 新RIVE授权域与配对

入口不再依赖旧六运行顺序、旧S-ref终态日志或已消耗的RF授权。新stage为`CRANIAL_BCSP_SCQ_RIVE`，mode A、seed0、8192→8192，范围为Static_C→Requery_C→Static_D→Requery_D。该顺序是科研矩阵，不是一次性执行授权。

新Static开始scratch配对，不要求另一臂已运行；后续Requery须绑定同折、同设备、同pair contract、同初态/顺序和完整计数的RIVE Static正式冻结凭据。测试中使用的配对凭据均明确为人工fixture，不是实际训练证据。当前只创建Static_C正式待授权request。

授权回执绑定request SHA；runtime单向绑定授权回执SHA，不引入反向哈希循环。生产授权回执、runtime、launcher和attempt claim均未材料化。测试目录中的`ARTIFICIAL_*`文件仅验证接口，不赋予生产权限。

### 2.2 原训练循环与初态

继续调用原runtime SHA256 `939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee`，不另写optimizer或训练循环。原100 traversals×39 batch、batch8、3900 updates、31200 exposures、300 drops、固定epoch99/update3900最终checkpoint保持。

原AdamW、LR/BN、梯度裁剪、SSM no-decay标记、FP32/TF32=false和coarse+dense loss保持。loss后端继续是已有PyTorch cdist；PointNet2与Mamba沿用已绑定provider，不安装、编译或fallback。

SCQ和RF初始化bin精确复用，原factory私有随机流不变；生产更新前校验完整初态参数与持久状态指纹。CPU只构造tiny人工模型，不声称重算了完整40827847参数模型的初态。

### 2.3 3600秒与资源口径

旧静态配置保留86400秒作为历史配置身份，新request绑定**实际3600秒**：launcher外层timeout及传入原TrainingBudget的effective limits均使用3600。没有覆盖旧配置或放宽原合同。原2GiB单run输出、8GiB RSS、20GiB Torch、22528MiB SMI及4GiB余量保持。

首运行启动检查要求可用空间至少2GiB输出+4GiB余量，即6GiB；每步保留原监测。继承的RSS监测读取worker自身RSS，不是进程树总量或硬隔离；GPU/RSS监测为采样。没有将未实现的进程树/cgroup保证写成已通过能力。

最近只读观察剩余8.485GiB，满足单run预算；完整四运行矩阵容量仍未认证。最终执行前需再次核对身份、provider、315训练payload哈希、目标不存在和可用空间，不能把本轮CPU通过当作现场资源准入。

### 2.4 读取与日志

复用已通过的精确源码读取、UTC先后顺序和启动SMI错误落盘逻辑；实际读取链覆盖encoder→factory→LQI→SCQ→RF→bridge→runtime，以及异常回溯读取。启动命令采用POSIX路径，目录先于日志重定向，单行长度限制保留。

记录Q0/Q1/Q2、残差、邻居集合重合、coarse/dense几何、两项loss、实际病例顺序与计数。Static继续验证N0复用；Requery允许实际重选邻居。记录不参与训练计算图。

完整M/F/z及实际邻居的420次Native同次保存属于后续预测入口范围，本轮未实现或执行该阶段。

## 3. 验证结果

先完成8项静态检查，随后在现有本机PyTorch CPU环境执行一批人工验证：Python3.9.21、Torch2.5.1，GPU不可见，线程2。

**结果：退出码0，73项命名检查全部通过，stderr为空；没有失败后修补或自动重跑。**

覆盖包括：

1. 四个fold/arm组合的完整`authorize()`，读取实际冻结文本元数据；拒绝旧stage、seed1、16k、资源/设备/初态漂移和缺失的新Static配对凭据。
2. 单独完整哈希授权和单向runtime合同；固定POSIX控制路径及3600秒launcher。
3. 实际SCQ/RF残差实现与RF安装，在tiny人工模型中走Static及Requery分派；验证零初始化、非零第二头梯度探针、Q1相对几何、固定邻居改变fixture及原no-decay分组。
4. 人工日志两项loss、Q2/coarse身份、同一个batch顺序、3900终止计数守卫。
5. 真正双臂bridge的runtime重哈希与委托；CPU生产调用、错误臂与错误runtime被拒绝。
6. 子进程启用实际读取策略，按真实顺序加载全部源码和原runtime；读取初始bin；验证源码写入、无绑定邻近文件、dev/其他checkpoint被拒绝，异常回溯保留原始错误。

人工完整forward3次、backward3次，optimizer step0；原runtime只导入，没有执行真实训练。没有真实NPZ数组读取、checkpoint加载、native Mamba/CUDA、GPU测试或服务器操作。原GPU证据继承，不重复preflight。

主要证据：`static_review_v1.json`、`cpu_invocation_v1.json`、`cpu_exit_v1.json`、`cpu_contract_batch_v1/result_v1.json`、`CPU_policy_stdout_v1.bin`、`training_entry_P3_v1.json`、`P3_difference_review_v1.json`。fixture全部保留在项目内新目录。

P3状态：`RIVE_TRAINING_ENTRY_LOCAL_P3_PASS`。P3证明调用层人工合同通过，不证明新的CUDA运行或科研效果，也不授权训练。

## 4. 首个待授权request

本机文件：

`pending_request_v1/SCQ_RIVE_Static_foldC_seed0_train_20261115_v1_execution_request_v1.json`

状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`，`execution_authorized=false`。

完整SHA256：

```text
fdcb6cacef71bfae9395baf7b3bd05506b34b4053b75bfb03f54bff6bbe82bda
```

大小：15288字节。范围仅Static_C、seed0、8k→8k、3900步、100 traversals、31200曝光/300drop、3600秒、唯一一次scratch训练；失败即停，不自动重试/resume，不运行评价、BNCal或后续臂。

计划中的服务器安装根：

`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1`

计划中的唯一结果目录：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Static_foldC_seed0_train_20261115_v1`

以上服务器路径只是冻结计划，本轮未连接或验证其当前存在性，未创建目录。不能因旧路径曾不存在而直接写入。

## 5. 当前边界与下一步

本轮已完成用户授权的入口/bridge、人工CPU验证、P3和首个待授权request。运输包与不覆盖安装映射**尚未冻结**，没有要求上传文件，也没有部署或使用本request执行授权。

下一步应仅冻结最小运输包与不覆盖安装映射；之后按既定边界上传核验，并在当前条件重新核验后，对本request完整SHA单独执行授权。不要只上传request而遗漏新入口与P3依赖，不复用旧RF request或旧launcher。

首运行空间就绪不能扩展成四run容量保证；后续在各自request前明确剩余空间安排，本轮不清理任何服务器文件。另三运行、预测、评分、统计和seed1均未获本轮执行授权。
