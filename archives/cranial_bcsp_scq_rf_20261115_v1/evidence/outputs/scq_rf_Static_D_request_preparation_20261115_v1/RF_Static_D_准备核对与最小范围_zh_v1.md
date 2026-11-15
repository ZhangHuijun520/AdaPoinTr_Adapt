# RF-Static Fold D 准备核对与最小范围

2026-11-15。已绑定S-ref_D（30项通过）和Requery_D（43项通过）的正式冻结证据。D折315病例、63来源、完整顺序及3900步合同沿用不变；不依据训练loss调参。

当前Static入口仍限定C折，需要新增D入口；Static bridge功能与fold无关，可以复用。模型公式、RF头、两份初始化、优化器、loss和runtime均保持不变。最终模型40,827,847参数；从头初始化，不加载已有checkpoint。

最后一组必须绑定同折Requery_D的完整初始参数/持久状态及顺序证据，并保留Static复用N0、在Q1重算相对几何的唯一机制合同。下一次集中实施只需D入口、必要的身份接口适配、一批人工CPU验证及P3，不重复GPU准入。

容器现已变为qx2k0r-0；先前五组的训练身份仍为zbpgzu-0。此次仅一次有界只读资源查询：不加载CUDA模型、不修改环境、不部署、不训练。实际GPU/驱动/解释器版本及磁盘记录在current_resource_identity_v1.json；是否与历史物理GPU及驱动一致见Static_D_scope_and_compatibility_v1.json。新容器不能自动当作原训练设备，旧审计身份不回写。

GPU UUID or driver differs from trained D pair; disclose device confounding and obtain a scientific continuation decision before accepting migration.

完整软件/provider资产尚未做本轮执行前核验；任何最终request仍保持待授权，不代表已经具备训练准入。本次未修改生产实现或创建执行内容。
