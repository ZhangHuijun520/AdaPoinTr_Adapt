# SCQ四模型 Native 预测入口、CPU验证及P3

日期：2026-11-14。已完成本轮授权的implementation-only范围，尚未连接服务器、安装文件或执行真实预测。

## 实现及差量

新增专用入口 `bcsp_scq_fourmodel_native_predict_v1.py` 及人工验证文件 `test_scq_native_prediction_cpu_v1.py`。原LQI入口、SCQ模型源码、训练runtime及权重均保持不变。

入口复用原有partial读取、Native输出检查、四源码精确读取基类、模块加载、文件策略、资源预算、归档、RNG快照、几何摘要、严格checkpoint加载及POSIX launcher。这11项函数／类的AST与旧入口一致。

限定差量为：四模型身份及420预算；本轮freeze证据字段；SCQ factory分派；复用已准入ExactSCQReads绑定SCQ源码与初始化二进制；Qraw／Qused／delta读取与保存；对应main接入。没有新建通用框架，没有修改模型或数值合同。

## 人工CPU结果

单批42项检查通过，保存完整测试结果与产物，没有失败后修复重跑。

- 四模型、两折420条元数据核验，同折B／S输入及归一化配对；缺病例、错误权重、错误fold／variant、额外cache、缺Qraw及路径漂移均拒绝。
- 实际完整authorize路径及单向授权链验证；拒绝缺授权、runtime哈希不一致、超额forward、backward及BNCal。
- 在子进程真实文件audit hook下，加载六个实际源码模块并读取精确初始化二进制；拒绝写入及无关相邻源码读取。
- 使用实际母版计算类和SCQ factory，人工grouper／因果mixer下分别运行B／S完整forward。S使用固定非零人工残差检查Qraw＋delta等于实际返回coarse；没有优化器更新或拟合。
- 测试实际生产factory调用签名及variant分派。严格加载人工3900步checkpoint；错误更新数、缺键、多键均拒绝。
- 420次轻量人工外层forward（每模型105次）及420份输出齐全，逐份保存prediction／coarse／Qraw／delta，424个归档成员核验通过，四模型状态及Python／NumPy／CPU RNG保持一致。
- 第一例人为失败后停止，保存尝试数，不进入下一模型；launcher父目录先于日志重定向创建，POSIX参数和超时保持原合同。

CPU测试环境为既有PyTorch 2.5.1+cpu环境。真实母版人工forward为2次，420次循环为轻量接口fixture，不是420次科研预测。没有读取真实点集数组、加载真实checkpoint或调用CUDA。服务器环境二进制不在本机，未冒充已验证其实际内容；执行前必须重新核验。

## P3及待授权范围

P3状态：`LOCAL_SCQ_NATIVE_PREDICTION_P3_PASS`。最终源码与CPU记录、静态结果、实际读取策略结果及四次正式训练freeze绑定。

顺序固定B_C、S_C、B_D、S_D；每模型105例，合计420次Native forward，batch1、8k输入、Q256及8k输出。对应210个不同病例、42个开发来源。仅partial入模型；不使用GT条件、配准、去飞点、TTA、筛病例、BNCal、loss或backward。不追加Memory或逐层trace；保存Qraw等数据不增加forward。

使用当前冻结的t6ibfm-0身份、GPU UUID及驱动，执行前重新核验；不自动重绑定。资源合同沿用7200秒、RSS8GiB、torch20GiB、SMI22528MiB、输出1GiB、磁盘余量4GiB。四模型串行，失败即停，不自动重试或resume。

## 文件及授权边界

最终request：`pending_request_v1/payload/SCQ_BS_CD_native_prediction_execution_request_v1.json`。

SHA256：`760191aeb674533e341d7050db58039eab6ddc7421a773bf36b05e816dea02c4`。

运输包：`pending_request_v1/bcsp_scq_BS_CD_native_prediction_pending_20261114_v1.tar.gz`，73519字节。

SHA256：`62299acb5258e340ac2c2b2abc44fa3c1d112a87efe963abacf89f47c2951cf0`。

运输包含14个待不覆盖安装文件及安装映射。已验证归档成员字节及完整清单，同时生成`.sha256`、`.bytes`和`.contents.sha256`三个校验文件。

request保持 `AWAITING_EXPLICIT_USER_AUTHORIZATION`。没有材料化真实授权回执、runtime、launcher、启动claim或tmux。用户上传后，仍需对上述完整request哈希单独授权，才可执行身份／资源／资产核验、不覆盖安装及唯一一次420预测。首次失败停止，无自动重试；无需重复GPU preflight。

预测结束后仍须单独正式冻结审计，再下载核验并准备统一CPU评分。本轮CPU／P3通过不代表CUDA预测、补全精度或接口吻合已经改善。
