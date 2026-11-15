# SCQ-RF冻结字节加载合同修订、CPU验证与v3待授权说明

2026-11-14。本轮仅本机限定implementation-only；未操作服务器、部署、运行CUDA或训练，未生成／替换权威初始化。

## 1. 修订内容

新增版本化RF源码`bcsp_scq_rf_residual_v2.py`，仅`load_initialization()`函数AST改变。移除加载时调用`initialization_values()`及其逐位相等比较；seed保留为历史生成来源。其余descriptor、forward、两臂分支、网络层、参数名称及初始化生成函数均不改，原factory复用。

加载器继续严格检查文件大小924,684字节、预期SHA256、四个参数的固定名称／形状／顺序、little-endian主机、CPU FP32解码、完整消费字节、有限性及零输出层。没有放宽数值容差，没有引入fallback或重新采样随机值。

唯一权威初始化仍为原文件，SHA256：

`a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e`

新request直接复用服务器已有这份文件，不把新的随机值写回初始化。新源码通过既有模块别名`bcsp_scq_rf_residual_v1`精确加载，保持原factory导入接口与state_dict键不变。

## 2. 本次CPU与P3

唯一一次新人工CPU批次**36项全部通过**，未运行任何模型forward、loss、backward或optimizer step。主要证据：

- 用禁止调用的stub替换随机值生成函数，整个加载／构造／factory批次调用次数为0。
- 四个加载tensor的哈希与冻结清单逐项相同；重复加载独立存储，修改返回副本不改变原文件。
- 默认dtype改变仍按FP32解码；模拟版本标签改变不触发重生成。该测试不等同真实跨PyTorch版本复现验证。
- 错误SHA256、声明大小、单字节损坏、截断／额外元素／空文件／错误总布局、NaN／Inf、非零输出层、错误固定shape／顺序与不支持的主机字节序均被拒绝。
- 两臂真实RF head构造及原factory在人工容器上正确绑定新加载器，参数数目231,171不变，共有参数及CPU RNG不变；没有调用KNN或forward。

新本机P3通过。旧59项模型图与52项CUDA入口CPU证据按精确源码差量继承，**本轮没有重跑59或52项，也不把它们相加宣称本轮执行了147项测试**。原CUDA短入口字节不变，双调用hook修订及其原生S-ref冻结证据保留；RF两臂CUDA尚未通过。

为兼容未改动的CUDA入口，P3中的`CPU_checks=59`字段明确标记为继承的旧模型图证据；本次实际执行数量单列`loader_CPU_checks=36`。

证据：[36项CPU结果](cpu_loader_batch_v2/result_v2.json)、[新实现P3](implementation_P3_v3.json)、[未改动入口的接入P3](entry_P3_v3.json)、[静态差量审查](static_review_v2.json)。

## 3. v3待授权request

[SCQ_RF_artificial_cuda_execution_request_v3.json](pending_transport_v3/payload/SCQ_RF_artificial_cuda_execution_request_v3.json)

完整SHA256：

```text
8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac
```

状态保持`AWAITING_EXPLICIT_USER_AUTHORIZATION`，执行未授权。v2 request `09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf`记录为已尝试、失败、已消耗、不得复用；其失败和历史文件不改变。

新安装根：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3`。

新输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v3`。

新tmux：`bcsp_scq_rf_cuda_20261114_v3`。

8个新文件不覆盖安装。原v2 CUDA入口、RF factory、冻结初始化与其余模型／provider／配置均为精确只读复用。身份仍绑定最近审计的`zbpgzu-0`，执行前必须重新核验；不能把本次本机准备当作容器在线或资产未漂移证明。

## 4. 科研与资源合同保持

仍为**5 forward／4 full loss／4 backward／0 optimizer step**：S-ref eval(batch1)仅参考forward；Static／Requery各eval(batch1)、train模式(batch8)各一次完整forward／原loss／backward。没有warmup、真实病例、checkpoint、BNCal或训练。

模型公式、初始化字节、原loss、FP32／TF32关闭、同进程初态比较容差、固定fixture、原生调用计数、状态恢复和全部资源阈值不改。失败即停，不自动修复重跑。本次不修订已记录的退出期次级日志守卫问题，原始首错保留规则和失败记录仍沿用。

## 5. 上传文件与执行边界

本机目录：`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\scq_rf_initialization_loader_20261114_v2\pending_transport_v3`。

请将以下四个文件上传至`/home/jovyan/`：

1. `bcsp_scq_rf_artificial_cuda_pending_20261114_v3.tar.gz`
2. `bcsp_scq_rf_artificial_cuda_pending_20261114_v3.tar.gz.sha256`
3. `bcsp_scq_rf_artificial_cuda_pending_20261114_v3.tar.gz.bytes`
4. `bcsp_scq_rf_artificial_cuda_pending_20261114_v3.tar.gz.contents.sha256`

压缩包20,995字节，SHA256为`c970baebb2ba2956bb80b8f703d8975a789ff122b8da2119d467ef68c13d3e62`，9个归档成员含8个payload与1个安装映射。

上传后须单独授权v3完整哈希，才可重验身份与资产、不覆盖安装、材料化授权回执／单向runtime／launcher并启动唯一一次新CUDA尝试。本轮未创建这些执行控制文件，CPU及P3通过不代表CUDA或科研效果通过。
