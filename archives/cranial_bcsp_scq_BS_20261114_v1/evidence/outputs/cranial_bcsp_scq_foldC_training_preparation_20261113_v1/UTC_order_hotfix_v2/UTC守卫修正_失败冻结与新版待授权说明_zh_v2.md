# B_C启动失败冻结、UTC守卫顺序修正与新版待授权范围

日期：2026-11-13。状态：**失败证据正式冻结；限定修正及本机P3通过；v2 request待授权**。

## 1. 已完成的正式只读失败审计

`failed_startup_freeze_v2/freeze_verification_v1.json`记录正式审计通过，指的是失败证据完整可信，不是训练成功。服务器退出码为1，固定tmux及worker已结束；原24个安装文件、控制文件与5份输出共33文件的名称及内容哈希符合预期。回读授权单向绑定和唯一claim均正确。

失败发生在factory导入Mamba的依赖链中，尚未进入`train_lifecycle`，没有initialization、metrics、model_construction、SCQ_geometry或checkpoint，resources日志为空；结合绑定源码可确认**已提交训练更新为0**。模型、provider关联工具、初始化字节及UTC精确链接目标均按原大小/哈希核验未变化。

根因是新训练Policy先调用SCQ通用守卫，其路径检查在已有精确UTC读者介入前拒绝了`/usr/share/zoneinfo/UTC`。外层`GenerateDecoderOnlyOutput`导入异常是其传播结果，不据此重装Transformers/Mamba或修改科研模型。

日志还保留了异常退出后traceback读取已关闭守卫fd导致的次级KeyError。本次不把次级报错误当模型失败，不扩展修复范围；后续异常仍可能产生该诊断局限。

审计最初在本机静态长度检查发现一条命令为2621 bytes，未发送服务器；随后将同范围的模型哈希检查拆为短批次完成审计，未扩大范围或预算。

旧request `132ea92fde3fb871f4bad6d78d18d625fc83c85e9e2719d52ef7cd2b9c3b9396`已消耗、不可复用，旧文件/日志未修改或删除。

## 2. 唯一生产修正

新增`bcsp_scq_training_entry_v2.py`，只在原训练Policy的整数fd处理之后、SCQ守卫之前加入：

```python
if utc.allow(filename, write):
    return
```

先由原`ExactUTCReader`检查精确路径、链接文本、目标inode/大小/哈希及只读属性，再交原SCQ/general policy。没有放开其他链接、整个zoneinfo目录或通用文本文件。

移除此单一条件后，新旧生产入口AST完全一致。SCQ、LQI、runtime、bridge、初始化、数据、loss、优化器、3900步及资源阈值均不变；没有部署或GPU验证。

## 3. CPU回归与P3

最终**22项针对性CPU回归通过**。测试使用实际UTC读者的verify/allow方法和实际旧/新Policy类，fd及metadata由人工fixture模拟，不创建Windows系统链接或改系统配置。

覆盖旧顺序冲突复现、新顺序精确核验、link/target及bytes路径、UTC写入拒绝、坏hash/链接文本/目标fd变化拒绝、整数fd、非UTC源码/写入/链接守卫、train-only NPZ和final-only checkpoint，以及原runtime/contract/budget字节身份。

首版人工OS fixture遗漏`SEEK_SET`常量而停止；只补该fixture常量，保留失败回执，未因此改生产代码。最终结果在`cpu_UTC_batch_v3/result_v3.json`。

`training_entry_P3_v2.json`通过，继承原34项训练入口CPU证据，另绑定本次22项UTC回归、静态差量、正式失败审计。它不代表真实服务器重新导入/训练成功，也不承诺此后没有其他阻断。无需重复已冻结GPU准入。

## 4. 新版request与精确部署范围

v2 request保持`AWAITING_EXPLICIT_USER_AUTHORIZATION`，`execution_authorized=false`。

完整SHA256：

`95d6dfdb07a0e64a8f80646c65f84da38ff7297344e74541000fe1dbcc899b84`

新版本只补5个文件：入口v2、P3 v2、正式失败审计副本、CPU结果副本及v2 request。其余已安装24个文件按原哈希复用；旧request仅保留，不再执行。

为保持已核验元数据路径和读根，5个新文件安装在现有根：

`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1`

这是**现有根内的全新版本文件**，不覆盖原文件；不误将现有根要求为“不存在”。真正必须不存在的是5个新目标、`control_v2`和新输出。新版控制目录、回执/runtime/launcher/claim路径均全新。

新tmux：`bcsp_scq_B_foldC_20261113_v2`。

新输出：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldC_seed0_train_20261113_v2`。

下一次授权后须重新核验当前容器/同GPU/driver、资源、旧24目标和复用模型/provider/初始化、315训练文件哈希及上传包，再不覆盖安装新文件。失败即停，不自动重试、resume或进入S_C、BNCal、evaluation。

## 5. 运输文件

`pending_transport_v2/`中四文件：

- `bcsp_scq_B_foldC_UTC_order_pending_20261113_v2.tar.gz`
- 同名`.sha256`
- 同名`.bytes`
- 同名`.contents.sha256`

压缩包**17,284 bytes**，SHA256：

`865d9f36185b348c9886a5d268c4fb197d859182e156dd44e4ee0a05e4cbfe98`

包内5文件加1份安装映射，共6个普通文件成员，无权重或点集。请手动上传四文件至`/home/jovyan/`，随后单独授权v2 request完整哈希。原包不用重复上传，原运行授权不得沿用。

最终已对v2实际`authorize()`进行全路径本机语义复核：使用精确文件镜像与内存中的人工控制字典，确认315训练病例、原3900步/资源/配对合同；没有材料化真实授权回执、runtime或launcher。

本轮唯一服务器操作为只读失败审计；没有服务器写入、新forward/backward、GPU准入或训练。当前交付不授权部署与执行。
