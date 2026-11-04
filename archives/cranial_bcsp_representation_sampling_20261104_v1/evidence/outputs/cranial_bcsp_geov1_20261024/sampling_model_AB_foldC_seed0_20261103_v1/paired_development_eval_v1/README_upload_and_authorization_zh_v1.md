# Fold C V1／Morton配对开发评价：上传与授权说明

**本机准备完成，状态 AWAITING_EXPLICIT_USER_AUTHORIZATION。未操作服务器、部署、预测或评分。**

request：`development_execution_request_v1.json`

完整SHA256：`76673ba94626253161dc70f0a33006d21c8094bced8148496c68c6c3490f0f4c`

固定105例／21来源，每臂一次，共210次native预测，8192输入与输出。两个final checkpoint已由正式训练后审计冻结；本次不重训、不BNCal、不更改采样参数。开发输入保持两臂共同GT、归一化与逐病例点序。

主指标：A1未知表面E面积加权P95(mm)；关键次指标：切壁J P95／Cover@2mm、E Cover@2mm及共同GT8192 CD-L1。按来源五缺损平均后等权比较Morton−V1，仅作单折单seed描述性结论。评价协议及后续单独评分边界见 `paired_evaluation_protocol_zh_v1.md`。

## 手动上传

将本目录以下五个文件上传到服务器 `/home/jovyan`。运输包共213成员（210点集＋3个工具／元数据文件），不含checkpoint或原始NRRD。不要上传CPU人工fixture或本机参考库。

| 文件名 | bytes | SHA256 |
|---|---:|---|
| bcsp_sampling_pair_foldc_development_v1.tar.gz | 33005392 | `5e333dec21488fa2faaf29458f660be4d883e022bfb52b5d8aaa5341026ae3cf` |
| bcsp_sampling_pair_foldc_development_v1.tar.gz.sha256 | 113 | `fad358e8445130a34ca7fa49f36b811852efdaa4715807edaa75e7441778ffa6` |
| bcsp_sampling_pair_foldc_development_v1.tar.gz.bytes | 9 | `f3828034ae6b3673e3da98b844930e30bcb867ed191ff8b8a0098c0ca8e94101` |
| bcsp_sampling_pair_foldc_development_v1.tar.gz.contents.sha256 | 26469 | `6825da18a3460c9df897bbf4aa4400fafdb7e0b5622c492470b6ab9bb28dacd0` |
| bcsp_sampling_pair_foldc_development_v1.tar.gz.contents.sha256.sha256 | 129 | `e51fd906c2aa195ce2a5af68b44b31fd78911e1bdcf3f7f1db946753f5d79e2c` |

## 后续顺序

上传后，对上述完整request SHA256单独授权。执行前仍须实时重验容器／GPU、两个checkpoint及精确复用资产、上传包、所有新目标不存在和资源；只按冻结映射不覆盖安装、材料化单向授权链，再启动唯一一次210预测。失败即停，不自动重试。当前容器预期为 `shu-common-25721452-notebook-v2iwsa-0`，若身份已变则不能直接复用。

预测结束后，另行授权正式只读冻结审计；下载并核验归档后，单独授权统一CPU评分。当前request不授权评分或正式gate。现有旧四模型评分工具不能直接运行两臂数据，评分时只做必要的两臂读取适配，保持当前冻结的指标与参考不变。

## 验证证据

20项CPU合同全部通过，人工Tiny模型及权重只在CPU使用；完整213成员运输包哈希回读通过，缺成员／重复目标均拒绝。P3记录最终实现、数据与父审计哈希。CPU测试不是CUDA通过证明；本轮未发出WSL或服务器调用。
