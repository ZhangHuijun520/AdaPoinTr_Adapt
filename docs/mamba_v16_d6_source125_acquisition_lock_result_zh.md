# Mamba v1.6 D6 source125 metadata-only acquisition lock 结果

> 本结果只冻结官方元数据、来源集合、完整 ZIP 边界和下载计划。没有读取、提取或部署任何 D6 geometry。

## 结果

- 官方健康 A-series：500 个来源。
- D3/D4/D5 排除：125/100/150，pairwise overlap=0。
- Prior union：375。
- D6 remaining：125 个来源、25 个完整 ZIP。
- Partial archive overlap：0。
- Development：100 来源、20 ZIP。
- Proposal confirmation：25 来源、5 ZIP。
- D6 后未分配健康来源：0。

总下载量为 61,898,113,721 bytes，即 57.65 GiB：

| Partition | ZIP | Sources | Bytes | GiB |
|---|---:|---:|---:|---:|
| Development | 20 | 100 | 50,812,421,339 | 47.32 |
| Proposal confirmation | 5 | 25 | 11,085,692,382 | 10.32 |

Development 下载批次：

| Batch | ZIP | Sources | Bytes | GiB |
|---|---:|---:|---:|---:|
| 001 | 8 | 40 | 13,244,133,257 | 12.33 |
| 002 | 8 | 40 | 23,078,626,299 | 21.49 |
| 003 | 4 | 20 | 14,489,661,783 | 13.49 |

## Confirmation blind partition

五个预定义 macro strata 各确定性选择一个完整 ZIP：

| Stratum | Archive | Bytes | MD5 |
|---|---|---:|---|
| S1 | A0081-A0085.zip | 1,250,631,135 | `069bb81da4f0387095af782f7e91e631` |
| S2 | A0161-A0165.zip | 1,276,988,561 | `17a8adad8e4c53d41f8f19f0591ebccb` |
| S3 | A0346-A0350.zip | 2,802,874,665 | `143f3e93aef5806056060b11d5357605` |
| S4 | A0366-A0370.zip | 2,257,538,190 | `05c89da4f65e35baac69ad99379b4488` |
| S5 | A0456-A0460.zip | 3,497,659,831 | `b98e2cd62bbdecff4bf74b34a09b42f7` |

该分区只使用固定 salt、archive name、官方 MD5 和 size。未使用 geometry、QC、模型预测或人工重分配。

## 冻结哈希

| Artifact | SHA256 |
|---|---|
| `files.sha256` | `d8509c44dd36575d46784972f70ec8f808754d3ffa84f390655ef3e5467c0fc1` |
| Acquisition receipt | `865b9fb30ef52c532ae5dd4c5ff18405833dee0570144ee94957cf5c460dab71` |
| Protocol copy | `10234e1c631cae80aca3ff4ce422107bc89bc3fb94b50b163f3157148ad6fd53` |
| D6 source125 IDs | `f84e13b0f260beefe9308bd5bd56d18fc5d95055c24033eaad0f2d1a74c3d658` |
| Development100 IDs | `833595b000732cb56a3d729fcb1121a0c70018bf030505aa9584020498a2cc68` |
| Confirmation25 IDs | `7adb4a0dcf6eb7897d66110f32f425fa36a5c5561f729bd173200bcd1386d632` |

正式数据锁：

```text
E:\ResearchBackups\AdaPoinTr\MUG500plus\data_locks\
mug500plus_d6_source125_acquisition_lock_v1
```

## 权限状态

当前只授权 development 与 confirmation ZIP 的离线下载和 checksum。

继续锁定：

- development extraction=false；
- development QC=false；
- synthetic generation=false；
- R0/R1 implementation=false；
- training=false；
- seed1=false；
- confirmation geometry=false；
- D6-B=false；
- protected/official test=false。

下一步必须先冻结 assignment-consistent R0/R1 mechanism protocol、toy-case tests 和 zero-step preflight。

