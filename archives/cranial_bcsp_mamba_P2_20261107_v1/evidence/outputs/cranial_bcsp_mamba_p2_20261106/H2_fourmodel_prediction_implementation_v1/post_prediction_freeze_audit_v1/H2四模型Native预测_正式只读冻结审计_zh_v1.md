# H2四模型Native预测正式只读冻结审计

2026-11-07。结论PASS，26项检查全部通过。训练/评价效果尚未解读。

## 完成与计数

预测退出码0，worker和tmux均已退出，无失败文件。四模型按C_AUX、C_COUPLE、D_AUX、D_COUPLE顺序各105次，总420次Native forward；420个预测文件，210个实际病例/42来源。清单和420条预声明attempt逐条匹配原输入、同折配对、case/source顺序、checkpoint哈希、归一化和输出哈希。无多余forward或重复病例身份。

433个现场正规文件的精确集合、大小/哈希通过核验，审计前后inode/权限/大小/mtime稳定，排除atime。所有冻结实现、provider、环境及四checkpoint共70个资产重新核验。

## 归档与数组

归档425个正规成员：420预测NPZ加inference manifest、attempt journal、geometry summary、inference complete及resources。成员名/大小/哈希与completion清单、现场文件、contents.sha256一致，无越界或链接成员，未在服务器提取文件。420个prediction数组均为有限FP32、8192x3；精确20个事前固定代表病例另有有限FP32、256x3 coarse数组。其余病例不额外保存coarse，计数和位置均匹配协议。

归档：

```text
/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_C_D_AUX_COUPLE_native_development_20261107_v1/development_predictions_v1.tar.gz
```

大小：38096299字节。实测SHA256：

```text
e2b28e7243531428ec7192c522bf87fe6855e01c4196be6d38d614bcc1511180
```

## 状态、RNG与Native边界

四模型各自105例前后的参数/持久BN state指纹完全相同，Python、NumPy、CPU、CUDA RNG记录前后完全相同。构建记录为实际M0、六个替换全局分支及对应H2模式，未使用人工fixture。严格checkpoint加载的模式/常量验证由冻结入口及CPU契约覆盖，审计不反序列化权重。

420条同forward几何/H2摘要均无condition override、GT读取标志或loss调用。AUX scale1且raw/used相同；COUPLE按固定有界公式、保持coarse中心、半径r_used=s*r_raw。最大舍入误差：

```json
{
  "no_override": true,
  "no_GT_read_or_loss": true,
  "AUX_raw_used_identity": true,
  "COUPLE_formula_bounds_and_moments": true,
  "max_scale_roundoff": 1.3907299467597056e-07,
  "max_radius_roundoff": 1.654628545288972e-09,
  "max_centroid_roundoff": 1.1641532182693481e-08
}
```

Native完成证据中training_updates、BNCal、loss、backward和模型optimizer计数均0，没有执行额外20次条件干预。矩和条件日志只能解释执行语义，不能替代形状/接口评分。

## 资源与限制

845条资源记录按4个model_start、420个before/after及1个all_complete严格排列，各项阈值通过。设备显存峰值692 MiB，RSS峰值1933758464字节，Torch allocated/reserved峰值214615552/253755392字节。最终含归档的输出总大小也在1GiB预算内。PID仅诊断，不证明跨命名空间所有权；资源监测不是硬隔离。

审计仅CPU只读检查既有文件/预测数组，没有新forward/backward、权重加载、模型更新、评分或GT读取。状态/RNG基于冻结源码及保存指纹核验，没有重建全模型张量。数组有限和形状正确不等于补全准确或具有临床制造精度。

## 下载与下一步

请从同一服务器输出目录下载以下四文件：

```text
development_predictions_v1.tar.gz
development_predictions_v1.tar.gz.sha256
development_predictions_v1.tar.gz.bytes
development_predictions_v1.tar.gz.contents.sha256
```

建议本机长期目录：`E:\ResearchBackups\AdaPoinTr\BCSP_MAMBA_P2_H2\2026-11-07_native_development_eval`。精确四文件大小及SHA256见download_four_files_manifest_v1.json。当前只下载审计文本证据，尚未下载归档至本机长期目录，不能认定已有可恢复本机备份；不删除服务器文件。

下载后先做本机压缩包、三个校验文件和425成员核验，再准备固定定义的统一CPU评分。评分需后续单独授权；本次未创建或执行评分request，不计算候选比较、bootstrap或gate。
