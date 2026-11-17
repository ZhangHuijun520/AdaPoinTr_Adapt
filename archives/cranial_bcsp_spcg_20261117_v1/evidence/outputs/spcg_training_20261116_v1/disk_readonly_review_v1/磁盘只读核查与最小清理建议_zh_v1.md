# SPCG G2_C 启动前磁盘只读核查

2026-11-16，当前容器 `lwwgl9-0`。本次仅查询元数据及对候选重复分片做字节核验；服务器写入和删除均为零，未重试安装或训练。未加载模型或反序列化checkpoint。

## 实测余量

项目所在文件系统可用8.392578125 GiB；保留原准入阈值8.5 GiB，缺口0.107421875 GiB，即110 MiB。阈值未修改。当前没有tmux会话；此项不是所有后台进程均不存在的证明。

项目分配空间约5.66 GiB，其中logs约3.93 GiB。旧N0目录约2.53 GiB，DAC诊断工具目录约0.91 GiB。du仅覆盖项目，未检查整个文件系统，不能据此推断其他目录的总占用。home顶层上传文件约6.58 MiB，单独清理不足以补足缺口；当前G2运输包应继续保留。

## 首选最小清理候选

仅建议清理以下两个目录中各29个 `part_000.bin` 至 `part_028.bin`，共58个分片：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/parts_restore_v3_C`

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/parts_restore_v3_D`

合计957,620,838 bytes，约913.26 MiB。每个分片均与仍保留的对应完整权重的同偏移字节完全相同；全部分片串接至文件末尾，无遗漏或额外字节。检查前后大小、mtime和inode稳定，无符号链接或多重硬链接。精确路径、大小、SHA256和保留对应关系见 `candidate_duplicate_parts_scope_v1.json`。

保留 `weights_restored_v3` 下两份完整LQI权重：

| 文件 | bytes | 实测SHA256 |
| --- | ---: | --- |
| LQI_C_epoch99_step3900.pth | 478810419 | d8d819ffb9ed1f931c60f0ee96e9ae9c4093d61c73c2152a52f13b8cd95a0ddf |
| LQI_D_epoch99_step3900.pth | 478810419 | 2afd1b4540b856d4c829786729d8c2df80943edd65a0f01af412940fd973e5ed |

若单独授权删除这58个重复分片，按本次余量估算可恢复到约9.28 GiB，足以超过原启动阈值。实际回收和后续余量须删除后重新实测；不保证共享文件系统上的后续变化。

保留分片目录中的manifest、合并脚本、所有完整权重、诊断结果，以及当前SPCG G0/G1 checkpoint、U/H、代码、训练数据、provider和环境。不因本机可能有归档而推断服务器其他文件可删。本轮未认证其他大文件已有可用本机备份，因此不建议现在扩大删除范围。

## 后续授权边界

本报告和候选清单不构成删除授权。下一步可仅授权按精确清单删除58个重复分片；删除前重新核验其哈希及保留权重。完成后再核验磁盘余量。

G2先前调用已在安装前停止，不能自动恢复或再次调用。清理完成也不构成新训练启动授权；若继续，需要单独授权新的尝试，保持原request、科研合同和失败即停规则。
