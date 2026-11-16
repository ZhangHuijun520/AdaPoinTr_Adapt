# RIVE Static_D待授权request准备

**状态：AWAITING_EXPLICIT_USER_AUTHORIZATION。** 本轮仅本机准备与37项静态绑定核对，不新增模型实现、不重复CPU测试或GPU准入、不操作服务器。

request大小15491字节，SHA256：

```text
f2a9d28fae758c5e718c28bc463d9c90de8b07b752ec89d80441807827018fb2
```

沿用已冻结模式A矩阵的第三运行：RF-Static、Fold D、seed0、8192→8192、batch8、100 traversals、3900步、31200曝光/300drop、3600秒。绑定原D折315病例/63来源、固定D-order和共同原始初始化；不使用C折终态权重warmstart，Static不要求未来Requery_D已完成。

模型/entry/bridge/runtime/P3、loss、优化器、LR/BN、阈值和原始初始化均保持。D-order文本逐轮计数核对通过；同折train/dev来源无交叠。C两臂正式冻结记录作为本机矩阵进度依据，不引入C训练loss或结果派生的配置变化，也不扩大统计结论。

使用全新run、session、控制/claim和输出路径；当前服务器路径是否不存在及资源未在本轮现场检查。request的capacity字段明确当前空间未核验，需执行前重新确认至少6GiB可用空间；完整矩阵空间仍未认证。不将旧观察数字当当前资源。

下一步仅冻结**单个request的补充运输包与不覆盖安装映射**；其余入口、P3、D折元数据和点集复用，不重复运输，也无需把C终态权重上传到训练目录。上传核验、安装和完整SHA对应训练执行仍按既定边界分别授权；当前没有材料化授权回执、runtime、launcher或启动训练，不评价或BNCal。
