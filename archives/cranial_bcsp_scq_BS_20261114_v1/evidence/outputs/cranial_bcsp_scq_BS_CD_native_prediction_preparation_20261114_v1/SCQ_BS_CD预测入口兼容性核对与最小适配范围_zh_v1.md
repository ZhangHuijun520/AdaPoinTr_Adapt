# SCQ B／S两臂、C／D两折 Native 预测入口兼容性核对

日期：2026-11-14。范围为本机既有源码及冻结JSON元数据核对；没有连接服务器、导入模型、读取真实NPZ数组、加载权重或执行测试。

## 结论

四次训练均已正式冻结，病例和归一化元数据满足本轮预测范围。但现有LQI预测入口不直接兼容SCQ，尚不能创建绑定最终实现哈希的execution request。当前已保存范围草案和420条输入元数据候选，明确标记不可执行；未材料化授权回执、runtime或launcher。

这次工作是入口核对，不是新的GPU准入。后续只需限定的预测入口适配、针对性人工CPU验证及P3，不重复已通过的GPU preflight，不开发新框架。

## 已确认的科学范围

| 顺序 | 模型 | 开发病例 | checkpoint SHA256 |
|---|---|---:|---|
| 1 | B_C | 105 | `9c4352355d001404e6e43a461244b6a2134884974cf8fba616ec0065c1001418` |
| 2 | S_C | 105 | `00f1ce94d219a42294c6c5a7874710edbd58431deac44c9522a9ab4f120d2f0b` |
| 3 | B_D | 105 | `f4bdd386c78eb3ebd7e764e9166761d18c3381acf0b0dc2ac91472533f5faf82` |
| 4 | S_D | 105 | `bd8fe23f1a276019b776b5d2cadce7aad62bd31eea440975ffd1222331f636fa` |

420次模型预测对应210个不同病例、42个开发来源。同折两臂使用完全相同的105例、点集文件哈希、顺序和D-only归一化；五类缺损齐全。病例保持冻结fold，不依据训练loss或已知病例表现重选。

输入8192点，coarse输出256点，dense输出8192点，batch1。每病例每模型只做一次eval／inference_mode Native forward。backward、optimizer step、loss调用、warmup、TTA、BNCal均为0。不做配准、去飞点、按病例选臂或GT条件输入。仅从输入NPZ取partial；GT字段不参与推理。

元数据表明旧LQI开发集输入与本轮来源的文件哈希、归一化一致；旧入口C／D目录命名与当前训练合同的根目录相反，因此不得直接复制旧DATA_ROOTS常量。应以本轮各fold训练合同和manifest构造精确路径。服务器210份实际输入的存在性和哈希仍需执行前核验；本轮没有声称已核验服务器数据。

## 必须集中完成的最小接口适配

1. **四模型和授权合同。** 旧入口硬编码两个旧LQI模型、旧权重及210预算，旧audit字段也不同。新入口应绑定四份本轮正式freeze、权重与factory版本，保持strict checkpoint load，拒绝缺失或多余键；完整路径覆盖authorize，不能仅把210替换为420。
2. **真实SCQ构造及精确读取。** 复用已准入encoder、LQI及SCQ factory，按B／S分派，并绑定SCQ residual、factory和初始化二进制。复用既有ExactSCQReads，不扩展后缀放行；保留UTC优先读取顺序。B为39903169参数，S为40596676参数；旧入口单一LQI构造证据及参数断言不适用于S。
3. **输入身份。** 从冻结fold和manifest绑定210份不同输入、420条预测记录；不凭目录名重选fold。逐臂核验21个开发来源、105例及与训练来源不相交。
4. **单次forward内的几何证据。** 保存Qraw、Qused/coarse、P及统一坐标信息。S复用已有_detached_诊断记录，B令Qraw=Qused；不追加forward、不导出完整Memory或逐层trace。应核对模型可能存在的点序变化，不能未经核验就把Qused与最终coarse逐元素比较，或直接假定dense到coarse的索引对应。
5. **针对性人工CPU验证及P3。** 覆盖完整授权路径、真实builder分派、人工state_dict严格加载、精确源码／初始化读取策略、420调用预算、失败即停、参数／BN／Python／NumPy／CPU及CUDA RNG前后指纹合同。用人工fixture验证合同，不读真实预测或checkpoint，不以CPU通过代替CUDA或科研效果结论。

限定新增内容建议为专用预测入口及对应人工测试文件；P3、scope/index/request为冻结证据文件，不修改模型、训练runtime或通用框架。通过后再创建绑定最终实现哈希的待授权request及运输包；安装与唯一一次420预测仍需单独执行授权。

## 建议沿用的预测资源合同

沿用已有Native入口：总墙钟7200秒、RSS8GiB、torch allocated／reserved各20GiB、SMI22528MiB、输出1GiB、最低可用磁盘4GiB，超时TERM后5秒KILL。四个模型串行构造、加载、预测和释放，失败停止，不自动重试或resume。该范围是草案，最终应在入口CPU验证与P3中绑定，不是资源准入证明。

## 本轮证据

- `entry_compatibility_review_v1.json`：源码身份、兼容性缺口和操作边界。
- `SCQ_BS_CD_input_index_metadata_candidate_v1.json`：四模型和420条候选输入记录，明确尚未核验服务器文件。
- `pending_scope_NOT_execution_request_v1.json`：限定范围草案，不是execution request。

本轮未修改生产源码、未运行CPU测试、未部署、未使用GPU、未创建可执行request。下一步需要单独授权上述限定implementation-only范围，完成后才能交付最终待授权预测request。
