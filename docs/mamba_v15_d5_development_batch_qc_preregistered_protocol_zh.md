# Mamba v1.5 D5 Development 批次提取与 QC 预注册协议

> 本协议仅处理已冻结的 development ZIP，不允许读取两个 sealed 分区。

## 范围

- development 共 100 个来源，固定分为 40/40/20 三批。
- 每批必须完整核验官方 ZIP 的字节数与 MD5。
- 每个冻结来源只流式提取一个规范命名的 `A????_clear.stl`。
- NRRD、PNG、非 clear STL、B-series 和任何未冻结成员均不得提取。

## 模型无关 QC

- 使用冻结的 clear-STL QC 引擎检查文件规模、三角面、有限坐标、退化率、包围盒与表面指纹。
- 每批执行批内重复表面门控；100 个 development 来源全部完成后再执行跨批重复门控。
- QC 失败必须原样冻结，未经正式修订不得替换来源。

## 访问边界

- `proposal_confirmation` 和 `completion_holdout` 在执行前后都必须为零文件。
- 不运行模型、不生成合成缺损、不训练、不选择候选。
- 只有当前批全部通过，下一 development 批次才可继续。
