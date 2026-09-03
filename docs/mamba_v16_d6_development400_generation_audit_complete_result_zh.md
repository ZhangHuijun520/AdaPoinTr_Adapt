# Mamba v1.6 D6 development400 生成、独立审计与归档完整结果

> 本文档冻结 D6 development100 到 development400 的数据里程碑。本阶段完成来源与协议绑定、400 例确定性生成、独立完整性审计和跨平台恢复验证；不执行梯度校准、不训练 R0/R1、不开放 seed-1 或 D6-B，也不访问 proposal-confirmation25 与 official test。

## 1. 研究目的与实验边界

D6 的本阶段用于为后续 slot-32 机制实验建立独立、可审计的数据基础。需要同时证明：

1. 100 个 development 来源均通过模型无关 QC，且不与 D3/D4/D5 来源重叠；
2. 每个来源确定性生成四种缺损族，共 400 个病例；
3. 四个病例保持来源级同折，四折各 25 个 dev 来源和 75 个 train 来源；
4. 来源、派生文件、NPZ、几何门控和清单可独立复核；
5. proposal-confirmation25 不提取、不生成、不参与当前任何统计；
6. 归档可在 Windows 本地恢复并重放完整哈希链，但不携带新的实验授权。

## 2. 上游机制与数据谱系

D6-A 在访问 D6 病例之前已冻结 R0/R1 slot-32 机制和人工 CUDA zero-step。R1 参数量为 94,529，zero-step 使用 4 个人工病例完成 8 次 forward、8 次 backward，optimizer step 和模型更新均为 0。

| 谱系项目 | 冻结身份 |
|---|---|
| D6-A zero-step commit | `26b255f1d71291c6ad40b9c50c2119a0eb88ff6c` |
| D6-A zero-step tag | `mamba-adapter-v16-d6a-slot32-zero-step-v1` |
| Zero-step 完整结果 SHA256 | `7f093b50e660e4828bec85b5c0f75ce2f6dc487198c648516b933969ff267b85` |
| Source125 acquisition lock manifest | `d8509c44dd36575d46784972f70ec8f808754d3ffa84f390655ef3e5467c0fc1` |
| Development100 QC lock manifest | `ba62bbe839e044d98a1f73be2fa2d0f2973ca771ab9e0911548dd77e81376ed2` |
| Development100 assets CSV | `a1f06fba94158074a116033d62b37c267479c7f630a10bee94c0383980083d0c` |
| Generation/fourfold lock manifest | `6a130df708ba006a286388cd38fb8bdd0d3fac7a028d67063357fa18bbd04036` |
| Source-fold assignment | `35d7b981395e4f630b1c2b071a42af38594380daa0ee92e60bb54653a6d0b5d1` |
| Generation protocol commit | `a48caa2b0ce2b792d8c4ee978a62054fa400a054` |
| Generation protocol tag | `mamba-adapter-v16-d6-development100-generation-protocol-v1` |
| Audit protocol commit | `eb93642a9ca5798ff3ae67752ae27b2a1f7fe93c` |
| Audit protocol tag | `mamba-adapter-v16-d6-development-generation-audit-protocol-v1` |

## 3. 冻结数据组成与四折

| 项目 | 冻结结果 |
|---|---:|
| Development 来源颅骨 | 100 |
| 每来源病例数 | 4 |
| 派生病例总数 | 400 |
| Fold A/B/C/D 病例数 | 100 / 100 / 100 / 100 |
| 每折 dev/train 来源数 | 25 / 75 |
| 来源 STL 文件总字节数 | 19,914,032,900 |
| 来源 raw tree `du -sb` | 19,914,069,764 |
| D6 development400 tree `du -sb` | 109,951,107 |
| Proposal-confirmation 几何访问数 | 0 |

四种缺损族为 `ellipsoid_large`、`ellipsoid_medium`、`ellipsoid_small` 和 `irregular_medium`，每族各 100 例。同一来源的四例始终位于同一折，不存在来源级 train/dev 泄漏。

## 4. 冻结生成结果

生成从 100 个冻结来源产生 400 个 NPZ，并在独立审计前保持 `pending_D6_generation_audit` 状态。

| 生成工件 | SHA256 |
|---|---|
| Generator bundle | `793306c4b0ec9ed0079c891f4f4c1b82590fb4b77dce5f9cd7a8a8885fe99a84` |
| Dataset `files.sha256` | `7c5967d6600aa2017e9c28aa3414594010b2033acf94c69f161f12889f243041` |
| Generation manifest | `37fca6b9436233053ce142d1fcb9504d0fb17c79123e1d78a1514f87b2528bdb` |
| Generation receipt | `eddc4758c434313e4edac1b6b50a8124f2d0d68744636133d57b239c69fdf676` |

生成器没有构造校准器、训练优化器或 checkpoint，没有访问 proposal-confirmation25，输出工作目录在验证后原子移动到最终目录。

## 5. 独立 generation audit

生成协议在运行前已经冻结审计硬门控；审计执行器在生成完成后、读取详细审计统计前单独冻结。该时间关系被明确写入 audit protocol，不将事后实现误述为生成前预注册。

| 审计工件 | SHA256 |
|---|---|
| Audit protocol | `5e8f09d9b5be5ea1271e4804c516701e72b69bf71f22cd96559a017e5ef901fc` |
| Audit implementation | `8d04091f68bd3d59ea30985845dea2717814ad1bb7920dfcc94e60e282eb8530` |
| Audit tests | `93b62a8db7a73b957fd75dd408dbc639eeab5f3a223c5e27480a7799ae6b7687` |
| Audit `files.sha256` | `fa14e67677aa64e1f0e2cdf96aa9d37062471ea3f774ca831d05bea1c95e7e7a` |
| Audit summary | `f8942d6421a524ff648639e464394bd64bfa32781f7d65a6ec8c62aa7485c390` |
| Portable manifest | `f39e44d0836545980840db2dad8969899be00b631f070fe535b8f09bbba9c682` |
| Derived-case audit CSV | `0a54040a299303dd574a87332dc2240400598b32f0c9fbb36c1a10f4e81dc9cf` |
| Source-fold audit CSV | `91ff3b1eb9b7803d95268080f14864f8af3950ecdc1b60b784bf23908001876f` |

审计逐例重新散列 100 个来源和 400 个派生文件，并确认：

- 400 个派生 SHA256 全部通过且两两唯一；
- manifest 与病例目录严格双射；
- 每来源四种缺损族完整且同折；
- `partial`、`implant`、`gt`、`centroid`、`scale`、reference-rim 的 shape、dtype、finite 和归一化契约全部通过；
- 几何硬门控、相对路径和来源绑定全部通过；
- proposal-confirmation25 与 official test 均未访问。

## 6. 几何审计统计

| 指标 | 最小值 | 均值 | 最大值 |
|---|---:|---:|---:|
| Reference rim 点数 | 8 | 23.615 | 64 |
| 移除表面积比例 | 0.0036789621 | 0.0376160036 | 0.1398270550 |

所有数值均位于预注册硬门控内。Reference rim 最小值正好达到下限 8，移除表面积比例最小值接近下限 0.003；这些是后续校准报告应保留的预注册分层变量，不能用于修改当前数据或阈值。

## 7. 部署与传输修复事件

服务器部署中发生两类非实验性修复：补齐已冻结的 D6-A zero-step 父报告，以及将 Windows CRLF 运输文本恢复为 Git 中的 canonical LF 字节。修复后重新生成的 protocol lock 与冻结 lock 字节一致，generation preflight 再次通过。

这些修复没有改变来源成员、fold salt、生成参数、几何门控或权限边界；对应凭据被纳入归档：

- `development_protocol_zero_step_parent_hotfix1_v1`；
- `development_protocol_lf_hotfix2_v1`。

## 8. 归档与跨平台恢复验证

里程碑归档不重复保存来源 STL，而是绑定本地 development100 资产包：

| 来源资产绑定 | 值 |
|---|---|
| Source archive stream bytes | 11,007,297,410 |
| Source archive stream SHA256 | `183ac5d7a1e6b3c2006ef0f933f1c78280da839dde492341c2c76ff6269e07c4` |
| Source STL count | 100 |
| Source STL file bytes | 19,914,032,900 |

最终 D6 development400 归档已在服务器和 Windows 本地分别恢复验证：

| 归档验证项 | 结果 |
|---|---|
| Archive bytes | 109,698,701 |
| Archive SHA256 | `45b913c3da57430f090f19fab9a2eb5dcbbbad09e73ea7d300e70d31368efc94` |
| Tar members | 560 |
| Payload manifest entries | 534 |
| Payload manifest SHA256 | `206f7c3e74d2dac46c87153686c8e8f356ea210b287fd71aca35ea5aebde951f` |
| Derived case hashes | 400 / 400 通过 |
| 三个数据锁、mechanism、zero-step、audit | 通过 |
| 环境和实现 bundle | 通过 |
| Source STL、confirmation geometry、checkpoint | 0 |

首次 Windows 验证使用的恢复路径恰好令一个文件达到传统 `MAX_PATH=260`，Python 3.10 `pathlib` 因而将该文件误判为不存在。归档及恢复后文件的实际 SHA256 均与 payload manifest 一致；改用较短恢复路径后，534 个 payload 文件和全部冻结语义完整通过。因此该事件属于本地路径长度兼容问题，不是归档损坏或结果漂移。

服务器环境记录为 Python 3.10.20、PyTorch 2.4.1+cu118、SciPy 1.15.3、NumPy 2.2.6 和 NVIDIA GeForce RTX 4090 D。

## 9. 权限与科学结论

本里程碑证明 D6 development400 数据完整、来源级互斥、可重复审计且可跨平台恢复。它不证明 R0/R1 有效，也不自动开启任何后续实验权限：

- `D6_gradient_calibration_authorized = false`；
- `D6A_training_authorized = false`；
- `D6_seed1_authorized = false`；
- `D6B_training_authorized = false`；
- `D6_candidate_selection_authorized = false`；
- `proposal_confirmation_accessed = false`；
- `official_test_accessed = false`。

## 10. 下一阶段建议

下一步只能单独预注册 D6 training-only gradient-ratio calibration。建议冻结：

1. R0 与 R1 分别按 fold A-D 使用训练分区，不读取 dev；
2. 固定每折批次数、batch size、case-slot 数和随机种子；
3. 固定主任务梯度与 slot-objective 梯度的参数集合、范数定义、聚合统计和目标比例；
4. 校准阶段 optimizer step、checkpoint load/write、dev 访问均为 0；
5. 校准权重按候选和同折绑定，禁止跨折合并后再调参；
6. 校准完成只授权生成 receipt-bound runtime configs，不自动训练；
7. seed-1、D6-B、candidate selection 和 proposal-confirmation25 继续锁定。

只有在独立校准协议、实现测试、CUDA zero-step 和校准完成凭据全部冻结后，才能另行签发 D6-A seed-0 训练执行授权。
