# Mamba v1.5 D5 development400 生成、独立审计与归档完整结果

> 本文档冻结 D5 development100 来源数据到 development400 派生病例的完整数据里程碑。该阶段只完成数据生成、来源级四折绑定、独立完整性审计和可恢复归档，不实现模型、不训练候选、不启动选择，也不访问任何 sealed 分区。

## 1. 研究目的与边界

D5 的本阶段目标是建立一套独立于 D4 的 development 数据基础，用于后续可证伪的候选与训练协议。核心问题不是比较模型性能，而是确认以下前提同时成立：

1. 100 个 development 来源颅骨经过冻结 QC 后可确定性生成 400 个合成病例；
2. 每个来源的四种缺损族完整、同折且来源级互斥；
3. 所有派生文件、几何约束、路径和清单均可独立复核；
4. proposal confirmation、completion holdout 和 official test 始终保持 sealed；
5. 归档能够在本地恢复并重放完整哈希链，但不携带新的实验授权。

## 2. 数据组成与冻结划分

| 项目 | 冻结结果 |
|---|---:|
| Development 来源颅骨 | 100 |
| 每来源病例数 | 4 |
| 派生病例总数 | 400 |
| Fold A/B/C/D 病例数 | 100 / 100 / 100 / 100 |
| 每折 dev/train 来源数 | 25 / 75 |
| Development 来源 STL 总字节数 | 16,820,263,850 |
| Sealed 几何文件数 | 0 |

四种预注册缺损族为 `ellipsoid_large`、`ellipsoid_medium`、`ellipsoid_small` 和 `irregular_medium`。同一来源的四个病例始终属于同一折，不存在来源颅骨跨 train/dev 泄漏。三个 development 下载批次被统一绑定到最终 QC lock；跨批重复、成员重复、非 canonical clear STL、大小或哈希不一致均为硬失败。

## 3. 冻结生成结果

生成器在冻结来源、冻结协议和确定性随机规则下完成 100 个来源、400 个病例的生成。最终状态为 `generated_training_locked_pending_D5_generation_audit`，随后才进入独立审计。

| 冻结身份 | SHA256 |
|---|---|
| D5 generator bundle | `ef0664bf17435d7aa7c5efbba076ef4dc1cc49701483bdd29f743af1e0ac27e8` |
| Generation/source manifest | `58b23c47be8da5dd801f2e5b527d7a978b6d7c97f0cec788d28681a8dc96f8ef` |

生成阶段确认：

- 100 个来源均产生四种预注册缺损族，共 400 个 NPZ；
- A、B、C、D 四折各 100 个病例；
- 生成输出在审计完成前保持 `pending_audit`；
- 未构造模型、优化器或 checkpoint；
- 未访问任何 sealed geometry。

## 4. 独立 generation audit

独立审计逐例读取全部 400 个 NPZ，并重新核验来源绑定、派生哈希、几何约束、数组契约、四折关系和目录双射。审计最终状态为 `generation_integrity_passed_model_training_selection_and_sealed_still_locked`。

| 审计身份 | SHA256 |
|---|---|
| Audit protocol | `7cb4ceb37b47191a6102468194fe793f530e8a7107b82c8b86fd9d288a64171e` |
| Audit implementation | `d2984c6e1a82157dca688578e826ee44999a78ea1c00269695f365bd4a783f91` |
| Audit tests | `b310c317e42dffa24ca570ddd78c4f61a6fd5b39226b1954f9c11925be2b1ed8` |
| Source manifest | `58b23c47be8da5dd801f2e5b527d7a978b6d7c97f0cec788d28681a8dc96f8ef` |
| Portable manifest | `f653a82ac29c98909d987ad0b6bb618841d006ddf3144ba732d4911cff32bf8d` |
| Audit `files.sha256` | `6232d046f87ee8548d29580a635c41e3ab316d96920fcc6a9fd8ab27a78e55ed` |

审计确认：

- 400 个派生文件哈希全部通过且两两唯一；
- manifest 与病例目录严格双射，无缺失或额外 NPZ；
- 每来源四种缺损族完整，来源与折绑定全部正确；
- `partial`、`implant`、`gt`、`centroid`、`scale` 和 reference-rim 等数组契约全部通过；
- 所有预注册几何硬门控通过；
- portable manifest 中的相对路径可在服务器与本地恢复环境解析；
- 所有模型、训练、选择和 sealed 权限仍为关闭状态。

## 5. 几何审计统计

| 指标 | 最小值 | 均值 | 最大值 |
|---|---:|---:|---:|
| Reference rim 点数 | 8 | 25.4525 | 81 |
| 移除表面积比例 | 0.00835789 | 0.04044113 | 0.14427638 |

Reference rim 最小值达到协议允许下限 8。该事实不构成生成失败，但后续候选协议应预注册按 rim 稀疏程度和缺损族分层的报告，避免总体均值掩盖低支持病例。该观察不能用于回改本次冻结数据或调整既有几何门控。

## 6. 运输规范化事件

服务器部署期间发现 Windows CRLF 运输会改变冻结文本文件的字节哈希。处理方式是从已冻结 Git 对象恢复 canonical 字节并重新执行精确 lock replay，而不是修改协议内容或替换数据锁。

| 项目 | 结果 |
|---|---|
| Transport status | `canonical_git_overlay_installed_lock_exact_preflight_passed` |
| Canonical overlay SHA256 | `a8b4899ccff528bd1cd1de4992e95932f0b3a87ebec192e4dfbe28a03e9aad4c` |
| Canonical overlay contents SHA256 | `b51bb023cd4c8cef933a32196b66b51642e9adf644d84a3fdb85753d97868933` |
| Fourfold lock manifest SHA256 | `eade1467f7864f041c2c9e2065936f5aa8fbd84e0999d335f1d1b0b247da18fb` |
| Exact replay | `true` |
| Lock replacement | `false` |

因此，该事件属于传输层字节规范化，不是协议修订、阈值调整或结果后验修补。

## 7. 本地归档与恢复验证

最终里程碑归档不重复保存 16.8 GB 来源 STL，而是绑定已独立校验的本地 source100 资产归档：

| 来源资产绑定 | 值 |
|---|---|
| Source archive bytes | 9,288,781,774 |
| Source archive SHA256 | `9d3544766188369783d8adfa99a6592dc32ccea7715d9b43a97ab1f493091a21` |
| Source STL count | 100 |
| Source STL bytes | 16,820,263,850 |

D5 development400 里程碑归档已下载到本地并完成恢复验证：

| 归档验证项 | 结果 |
|---|---|
| Archive bytes | 109,677,064 |
| Archive SHA256 | `dda4c9334e3769996483498d50793bbe1f7fb96d9907297ee929c36eb0d44d0a` |
| Tar members / regular files | 530 / 509 |
| Payload manifest entries | 508 |
| Payload manifest SHA256 | `c65957ecc0043d175ed16676c0406c276802f2ee033b174fdbe399ba37206978` |
| Derived case hashes | 400 / 400 通过 |
| Generation receipt and three locks | 通过 |
| Independent audit and transport receipt | 通过 |
| Environment and implementation bundle | 通过 |
| Source STL or sealed geometry in archive | 0 |

本地恢复验证同时确认归档中不存在模型 checkpoint，且所有训练、选择和 protected-access 标志仍为 `false`。`verification_restore` 在 Git 推送和远端 tag 核验完成前暂时保留。

## 8. 安全与权限结论

本里程碑只证明 D5 development400 数据可复现、可审计、可恢复。以下权限没有因数据审计通过而自动开启：

- `D5A_model_implementation_authorized = false`；
- `D5A_training_authorized = false`；
- `D5B_training_authorized = false`；
- `D5_candidate_selection_authorized = false`；
- `proposal_confirmation_accessed = false`；
- `completion_holdout_accessed = false`；
- `official_test_accessed = false`。

## 9. 冻结结论与下一步

D5 development100 到 development400 的数据生成、来源级四折、独立完整性审计和本地恢复验证均已通过，可以作为后续 D5 实验的冻结数据基础。该结论不等价于候选有效，也不允许直接启动训练。

下一步应单独预注册 D5 候选与训练协议，至少冻结：

1. D5-A/D5-B 的可证伪机制假设与实现边界；
2. 训练预算、优化器、epoch、checkpoint 和随机种子；
3. 来源级四折执行及一次性 dev 访问规则；
4. contact-support、整体几何、灾难病例和效率门控；
5. 候选晋级、停止条件和禁止人工 tie-break 的规则；
6. zero-step implementation preflight 与单独的训练执行授权。

在上述协议形成新的不可变凭据并通过零步 preflight 之前，D5 模型实现、训练、候选选择和 sealed 数据访问继续锁定。
