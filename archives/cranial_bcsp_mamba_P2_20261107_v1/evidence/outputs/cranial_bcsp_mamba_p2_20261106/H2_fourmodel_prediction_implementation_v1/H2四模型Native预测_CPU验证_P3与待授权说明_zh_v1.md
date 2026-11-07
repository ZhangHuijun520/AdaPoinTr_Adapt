# H2四模型Native预测入口：CPU验证、P3与待授权request

2026-11-07。新增一个隔离预测入口与一个针对性CPU测试文件，复用H2模型和已有provider，不改训练源码或三个H2实现。本机P3完成；未连接服务器、部署或运行真实预测，也没有重复GPU preflight。

## 固定执行范围

C_AUX→C_COUPLE→D_AUX→D_COUPLE，四个正式冻结的epoch99/update3900 checkpoint，每模型105例，总420次Native forward，实际为210个共享开发病例/42来源。每折两臂输入、D-only归一化和顺序相同。batch1，8192输入/8192输出，256 coarse；无warmup、TTA、loss、backward、optimizer或BNCal。不重跑既有M0。模型逐一处理，先用原factory创建M0再附加同模式H2，检查checkpoint内H2版本/常量/mode和legacy阶段/epoch/update，然后strict加载，不允许缺头键、额外键或模式不匹配。

推理只访问partial数组，不访问GT/target。日志从当前forward的H2上下文记录D-only delta、scale和raw/used coarse矩，不调用get_loss、不额外forward，也不设置condition override。各105病例前后参数/持久BN及Python、NumPy、CPU/CUDA RNG必须不变。已有秘密/payload/链接/资源守卫保留；精确源码读取扩展至factory、encoder、H2 range、H2 adapter四文件，并通过直接编译固定.py字节避开相邻.pyc。

同一forward保存dense及事前固定代表病例coarse张量、Native几何/H2摘要，完整attempt journal、manifest、状态/RNG证据与预测归档四文件。未来COUPLE条件干预20次不在本request内，固定病例已事前登记但不执行、不混入Native主表。补全质量与接口结果仍须后续正式冻结、下载及统一CPU评分判断。

## CPU与P3

新版34项CPU检查通过。执行四模型合计420次人工预测，检查105/模型、420个输出、420条预声明attempt、845条资源采样调用、同模式人工checkpoint严格加载、错误模式/常量/keys拒绝、parameters/BN和CPU/Python/NumPy RNG不变、partial-only读取、无条件override及首错停止。实际原forward AST结合人工本地算子，native factory为明确人工facade；CPU不验证真实Mamba/PointNet2/CUDA或CUDA RNG。

源码策略回归在独立子进程启用实际audit hook，通过四个固定人工源码的真实load_h2_builder读取、range→adapter与encoder→factory导入，并拒绝写入和相邻源码访问。首批测试已完成420人工预测后，在Windows CRLF人工源码fixture与继承Linux os.read文本FD的哈希比较处停止。仅改人工fixture为原始LF字节，再执行新batch_v2；生产入口与读取守卫不变，失败回执和测试快照保留。

本机P3确认原load_partial/predict_once/source_module/file policy/resource/RNG/geometry/pack核心AST不变，H2实现哈希与既有CUDA版本一致，四份训练审计和checkpoint指纹绑定完整。资源预算继承7200秒、RSS8GiB、Torch20GiB、设备22528MiB、输出1GiB、空闲磁盘最低4GiB；是采样监测，不保证硬隔离，PID仅诊断。有限Mamba数值非确定性继续披露。

## 待授权文件

完整request SHA256：

```text
b95b866a6b3a0eaeb1e840e003ecd426847ed47b07675b6c1f7644b5aee97170
```

状态AWAITING_EXPLICIT_USER_AUTHORIZATION。运输包包含11个不覆盖安装文件；真实权重、数据、依赖及H2模块直接复用，不在包内。

压缩包bcsp_p2_H2_fourmodel_native_prediction_pending_20261107_v1.tar.gz：74716字节，SHA256：`69f9c1863250d7425471b4294726d0a278406d26565f496839207b0fcf9fbbcd`。

请将pending_request_v1中的tar.gz及.sha256、.bytes、.contents.sha256四文件上传到/home/jovyan。上传后须针对完整request哈希单独授权不覆盖安装与唯一一次420次Native预测。执行前重新核验当前身份/GPU/空间、新目标不存在、四checkpoint、210个实际输入文件和复用源码/provider/元数据。

没有材料化正式授权回执、runtime、launcher或attempt claim；包内仅为无授权值模板。没有运行真实GPU预测、训练、评分或正式gate。
