# H1两折预测入口：实施、CPU验证、P3与待授权request

状态：**implementation-only完成；38项人工CPU检查通过；P3通过；最终request为AWAITING_EXPLICIT_USER_AUTHORIZATION。**

## 1. 本轮改变

新增隔离入口`bcsp_p2_h1_twofold_predict_v1.py`，以已审计P1 Fold C预测入口为母版。旧P1入口、模型、Mamba encoder、factory、provider均未修改。

必要差量：

- 两个模型固定为`C_M_H1`与`D_M_H1`，各105例，总预算210次；没有基线额外forward。
- 每折独立校验train/dev来源、病例顺序、实际输入路径及原始目标/归一化溯源；manifest写实际fold。
- 模型属性和基线YAML只允许增加唯一H1配置，其他目标仍关闭。
- 绑定两折正式H1训练后冻结审计、最终checkpoint bytes/SHA256及P3。
- 代表病例按fold取固定清单，保存C7例、D5例coarse数组；全量利用同次forward保存coarse/dense摘要，不增加instrumentation调用。
- checkpoint加载、partial-only读取、精确源码读取、文件策略、资源Budget、state/RNG、归档等安全关键函数与原入口AST一致。

H1仅在训练loss使用；预测不调用loss。保留H1配置是准确记录模型身份，不是推理时使用GT或额外约束点云。

## 2. 验证及P3

本机既有PyTorch CPU环境执行唯一一批人工验证，**38/38通过**。新目录`artificial_cpu_batch_v1`保留全部fixture、人工预测、失败场景及记录，不清理或覆盖旧验证。

重点覆盖：

1. 原冻结两折输入索引/manifest/source index的完整105×2元数据验证；训练来源注入、重复/缺病例、错误fold、checkpoint哈希、H1参数和实际存放路径漂移均拒绝。
2. 完整`authorize()`单向绑定，无授权、runtime哈希错误及超过210预算拒绝。
3. 两份真实正式训练冻结审计的元数据验证；错折审计拒绝。
4. 微型人工模型按eval/inference_mode完成105＋105，210份manifest的fold、forward index正确；每折参数/BN及Python、NumPy、CPU RNG保持。
5. 人工checkpoint使用生产原始weights_only/strict loader，最终epoch/update正确接受，非最终epoch拒绝；人工NPZ的GT故意为object数组，partial-only读取正常，证明没有读取它来生成输入。
6. 非有限输出、forward异常、RNG改变、BN状态改变均停止，不进入第二模型；C7/D5 coarse保存数正确，210个同次几何摘要和归档清单完整。
7. 11个继承的安全关键函数/类与母版AST一致，实际factory/encoder精确只读绑定通过，写入和哈希漂移拒绝。原P1的完整source-policy行为证据继续作为继承依据，本轮没有重新开发文件守卫。

P3确认原模型及其参数/shape不变，两fold配置/审计/权重身份严格绑定。CPU使用微型模型、人工权重及人工NPZ；真实模型forward=0、真实checkpoint加载=0、真实点集payload读取=0、GPU调用=0。人工失败场景属于契约检查，不是科研失败。

最终封装过程中，本机launcher argv的静态索引断言误将`-B`位置当成entry位置；仅修正为entry的正确位置，并核对已产生的本机准备文件字节一致后完成封装。入口和测试均未改，未重跑CPU验证。没有执行任何launcher。

## 3. 最终待授权request

文件：`pending_request_v1/transport_payload/H1_C_D_development_execution_request_v1.json`。

完整SHA256：

```text
90df035abba6cb6651f323ce65f5477f2a9bd0b3a7a505a5ebcc376b7436c147
```

合同：batch1、输入/输出8192、coarse256、C105＋D105＝210次forward；warmup/TTA/loss/backward/optimizer/BNCal均为0。C后D，任意失败停止，不自动retry/resume或继续下一模型。只用冻结epoch99/update3900权重，不按训练loss选轮次。

权重：

- C：`6839d694cdd8068085dceea1426aa9d55e71faeaff39a9032bf21af6b1e8b5b4`。
- D：`6a76aa7dc156c0e2eeef29d4e03b253f624373ced8a48abebe1af4c99d7e789d`。

M0基线复用已冻结的P1预测，不恢复旧权重重新推理。后续CPU评分前须验证本机基线预测归档及相同case/input/target/frame；本轮没有打开大归档，也没有计算指标或H1 gate。

wall7200秒、RSS8GiB、torch峰值20GiB、SMI22528MiB、产物1GiB、空闲磁盘4GiB，沿用既有预测资源合同。state/RNG按每模型105例前后核验，仍披露训练阶段已接受的有限梯度非确定性；不把CPU通过或历史CUDA准入视为当前预测成功。

## 4. 运输与未来路径

手动上传四个文件，位于：

`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\cranial_bcsp_mamba_p2_20261106\H1_prediction_implementation_v1\pending_request_v1`

1. `bcsp_p2_H1_twofold_prediction_pending_20261106_v1.tar.gz`
2. `bcsp_p2_H1_twofold_prediction_pending_20261106_v1.tar.gz.sha256`
3. `bcsp_p2_H1_twofold_prediction_pending_20261106_v1.tar.gz.bytes`
4. `bcsp_p2_H1_twofold_prediction_pending_20261106_v1.tar.gz.contents.sha256`

压缩包48956 bytes；SHA256：`00eab49474bd23d4d0139dc1e74078e61b5c2a5b4678b081c0d4c53aa891fe9b`。

包内8个拟新安装文件：入口、输入索引、预测协议、P3、两折训练审计、CPU结果、request；另有不覆盖安装映射。不含checkpoint、真实点集或人工测试fixture。

未来安装根：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H1_twofold_prediction_20261106_v1`。

未来输出根：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2_h1/C_D_M_H1_development_20261106_v1`。

tmux：`bcsp_p2_H1_CD_eval_20261106_v1`。

本轮没有操作服务器，身份/当前资源与路径存在性尚未重验。执行前必须核验当前容器/GPU、上传包、两权重、210个输入与复用源码/配置/provider；全部新目标及控制/run路径必须不存在。异常立即停止，不自动重绑定、修复依赖或重复GPU preflight。

## 5. 当前边界

没有材料化真实授权回执、runtime、launcher或claim，没有安装或启动预测。人工测试目录中的合成授权记录只用于fixture，不是本request的执行授权。

用户对本request完整SHA256单独授权后，才可按冻结范围核验、不覆盖安装、依序材料化单向控制材料并唯一一次启动。预测完成后另做正式只读冻结审计，再下载并核验归档，之后准备统一CPU评分。此时才可能回答H1是否改善Native覆盖和接口风险。
