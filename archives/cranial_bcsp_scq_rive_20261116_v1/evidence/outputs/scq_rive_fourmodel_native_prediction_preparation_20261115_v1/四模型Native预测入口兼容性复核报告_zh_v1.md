# RIVE四模型420次Native预测入口兼容性复核 v1

## 结论

模型接口、RF factory、冻结初始化、checkpoint载入格式及现有Native预测核心可复用；旧六模型短入口不能原样执行本轮RIVE。需要一次限定的RIVE四模型入口适配及人工CPU回归／P3，之后才能生成绑定最终实现哈希的待授权execution request。本轮未修改任何生产源码，也没有生成最终执行request。

## 已核清的科学范围

29项本机静态一致性核对通过。模型顺序固定Static_C、Requery_C、Static_D、Requery_D，每模型105例，共420次forward；210个唯一开发输入、42个来源，每来源5种既定缺损。每折两臂输入路径、哈希、归一化、病例顺序一致，且训练／开发来源互斥。所有四组训练均为共同原始初始化、8192→8192、3900更新；C/D各自使用原冻结批次顺序。

本轮两折Static/Requery均在相同冻结GPU及驱动上训练，不能沿用旧RF的D折跨设备混杂标签；但也不能因此抹去旧RF阶段的历史限制。Mamba有限梯度非确定性披露仍保留，单seed结果不能作多seed结论。

四个新checkpoint及正式审计绑定如下：

|模型|checkpoint SHA256|正式审计SHA256|
|---|---|---|
|Static_C|`80c59d40fe3d0a415e41c67f1b036f619e2e862fde829f42a66ecb73e950eb97`|`37c4c51ba73b28fbc43de7b37aeb00d898d63792655f1de81b29e9bc083990b5`|
|Requery_C|`5fc095755fa22fec79230394f3d3cd5dc461fd18e4ff1e366e52e5ae033dc87e`|`fd463d344e62978c79fa8bc1c077b04b3366b38ea945fe49544f81528a02775d`|
|Static_D|`f196f5b1bf406e4018baf11ae5d977dc445f515ea4b72aff431a061e64740b45`|`d1637699a9e1e6813920c5feeae014db72500ef71b15e21d447c2d2e479a86ea`|
|Requery_D|`e2528ee8a65f3c8a1a44798a89af1d47a94c3a02aa2c0de2a48ed6bf1a880533`|`5c0ef50e3b3a9f0a0a602d3e703d96cea605c86370ababc084c350fabe291346`|

## 最小适配范围

1. 用新RIVE四模型schema、固定index／protocol／audit哈希替换旧sixmodel及六个历史权重pin；严格保持四模型105例与420预算。
2. 将authorize、validate_index、validate_evidence、实际循环上限、完成事件和打包计数同时适配，不能只改request中的630。
3. 读取绑定覆盖实际factory／encoder／RF源码、当前四份正式审计及新入口，不新增通用库存框架。
4. 保持batch1、eval/inference_mode、partial-only、FP32数值合同、state/RNG前后指纹、失败即停；零warmup/TTA/loss/backward/optimizer/BNCal。
5. 保留现有prediction、coarse、Qraw及RF分阶段数组，不采集完整context/decoder trace，不增加模型调用。
6. 用人工fixture覆盖完整authorize及四模型计数、两折配对、实际加载读取路径、错误历史pin拒绝、state/RNG及失败边界；通过新P3后生成最终request。无需重复已通过的GPU准入。

## 路径与资源限制

复用此前已更正的实际开发点集路径：逻辑Fold C开发病例位于foldd目录，逻辑Fold D开发病例位于foldc目录。这反映既有数据布置，不能按目录名猜测分折；必须用fold_binding、病例／来源清单及哈希约束。当前只核对本机冻结索引，没有重新确认服务器文件存在或读取真实NPZ。

候选预算沿用已验证预测入口的7200秒、RSS8GiB、Torch20GiB、SMI22528MiB、输出1GiB和最低4GiB余量，最终request需明确绑定。当前空间未重查；新路径、输出和归档并存的空间准入在后续就绪阶段检查，不以旧观察认证。

## 当前边界与下一步

已保存420行范围草案；其状态明确为非执行request。未连接服务器、导入模型、加载checkpoint、运行测试或forward，没有部署、执行控制材料化或训练。当前授权是兼容性复核与request准备，尚不包含新增预测实现和测试。

下一步可单独授权“新增RIVE四模型预测入口＋针对性人工CPU验证＋P3；通过后创建绑定最终实现哈希的待授权request，不重复GPU preflight”。
