# S_D 正式只读训练后冻结审计及 B_D／S_D 配对核验报告

审计日期：2026-11-14（Asia/Shanghai）。

## 结论

正式审计通过，32组检查全部通过。S_D 正常退出，完成3900次更新、100次遍历、31200次病例曝光及300次丢弃。未运行BNCal、评价或resume。该结论确认训练合同与证据完整性，不代表补全精度或接口吻合改善。

## 权重及完整性

checkpoint：`ckpt-last.pth`，487148386字节。两次远端流式读取计算SHA256一致，且与completion及产物清单一致：

`bd8fe23f1a276019b776b5d2cadce7aad62bd31eea440975ffd1222331f636fa`

核验16个输出文件、59个安装及控制文件的精确集合，前后共75个文件大小与哈希稳定。回读15个非checkpoint输出及4个授权控制文件后，逐一核验哈希。未下载或反序列化checkpoint。

## 配对核验

- B_D正式冻结证据及模型构造记录与request中的绑定匹配。
- 两臂共有母版初始化指纹一致；S_D与S_C完整参数和持久状态初始化指纹相同。B与S结构不同，不要求完整参数指纹跨臂相同。
- 冻结数据来源、训练点集绑定、配置、环境、同设备身份及准入证据一致。
- 3900步实际病例及source顺序、学习率、BN调度、梯度裁剪设置逐步一致。
- 完整order、exposure及optimizer defaults文件逐字节一致；S新增4个参数张量外，共有优化器分组完全一致。
- 独立重算31200次曝光与300次丢弃；每例曝光加丢弃均为100次。
- D折数据、QC及顺序匹配C折训练前已冻结的两折合同。

## 几何与资源记录

逐条检查3900条metrics和3900条SCQ几何记录：索引和病例对应、数值有限、coarse／dense范围有效、Q0及delta维度正确、coarse质心与Q0＋delta质心一致，coarse与dense CD之和与实际重建loss一致。

3902条资源记录全部重新核验通过。峰值RSS为1669595136字节，torch allocated为13927097856字节，reserved为14810087424字节，SMI显存14612MiB。

以下delta仅为训练日志描述，单位为D-only归一化坐标，不是误差或临床毫米，不构成效果结论：

```json
{
  "max_query_delta_norm": 0.5235843062400818,
  "mean_batch_delta_norm": 0.21517971313860004,
  "nonzero_delta_steps": 3899,
  "units": "D-only normalized, descriptive logging only; no accuracy conclusion"
}
```

## 边界与局限

服务器仅执行只读核验与文件回传，没有新增forward、backward、训练、测试或评价，没有服务器写入。初始化核验依据已绑定factory记录的指纹，未重新构建模型或恢复权重验证；资源为采样记录，不声称PID命名空间所有权或逐条磁盘遥测。保留既定有限梯度非位级确定性披露。

下一步建议核对B／S四模型两折Native开发集预测入口，随后准备待授权预测request；本轮不创建或执行该request，不依据训练loss调参。

## 机器可读证据

`freeze_verification_v1.json` SHA256：`0e65d9b88fd26350b6a444f8fc225be805c390459f4312ff10dd57e1b02aa89b`。同目录保存前后清单、原始回传、非权重产物及授权链。
