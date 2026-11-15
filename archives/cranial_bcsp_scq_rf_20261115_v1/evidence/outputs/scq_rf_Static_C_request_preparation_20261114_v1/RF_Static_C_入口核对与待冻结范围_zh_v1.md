# RF-Static Fold C 入口核对与待冻结范围

日期：2026-11-14。仅完成本机只读证据及源码核对，没有部署、测试或训练。

S-ref_C正式审计26项通过，3900更新、100遍历、31,200曝光、300丢弃事件。已绑定其审计、构造、初始化和曝光记录。既定矩阵下一臂确为Static_C。

现有入口不能直接执行RF-Static：它只授权S-ref/S，禁止安装RF，校验40,596,676参数，调用三参数SCQ factory，并按旧SCQ evidence层级读取。真实RF factory需要原SCQ初始化与RF初始化两份冻结记录，返回parent/rf层级，模型为40,827,847参数。原SCQ日志也没有分开记录Q1、delta0与delta1。

因此没有生成一个明知不能执行的最终execution request。机器可读范围保存在request_readiness_review_v1.json的scope字段；该scope不是执行请求，不能授权训练。

建议下一步单独授权最小implementation-only接入：Static_C专用入口、必要bridge适配、针对性人工CPU回归及P3。复用现有RF模型和原3900-step runtime；不修改科研公式、loss、数据、初始化或资源阈值，不重复GPU准入。

该次接入应集中覆盖：RF factory参数与evidence层级；总参数和四个RF新增参数分组；排除仅RF后的共有初始化与S-ref一致；全部冻结源码和两份初始化的精确只读绑定；正常加载顺序、runtime再哈希和异常回溯；RF几何阶段日志；最终authorize与launcher合同。人工验证不使用真实点集或训练checkpoint。

Static_C仍从头初始化，S-ref最终checkpoint仅作冻结证据，不warm-start。保持同一Fold C、seed0、8k→8k、315训练病例/63来源、同批次顺序、3900步。只复用N0，第二头相对几何在Q1重新计算，不增加gate、clamp、额外loss或参数扫描。

实施和P3通过后，才创建绑定最终实现哈希的新request，保持AWAITING_EXPLICIT_USER_AUTHORIZATION；本次未创建runtime、launcher或授权回执。
