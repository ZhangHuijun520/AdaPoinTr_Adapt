# F0-P-v2 Fold C正式只读训练后冻结审计 v1

日期：2026-11-10。**结论：FORMAL_F0_FOLDC_POST_TRAINING_FREEZE_AUDIT_PASS，42项核验通过。**

## 运行身份与固定边界

Run：F0_foldC_seed0_train_20261110_v1；容器shu-common-25721452-notebook-n8xph5-0、UID1000。Request SHA256：`afd2750a3738f65d6fcfc308153c4358a4ded5e242a7e74796f9d8dec519d32d`。退出码0，固定tmux及worker PID均已结束；无failure或startup_failure产物。

输出目录：/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldC_seed0_train_20261110_v1。

## 完整产物与checkpoint

独立清点33个文件：16个运行输出、11个冻结安装文件和6个控制文件；目录仅有空tmp与control。采集前后逐文件SHA256、大小、inode、mode、mtime/ctime一致，读取造成的atime不参与指纹判断。原payload_manifest的12项全部匹配，原manifest未覆盖的launcher日志、PID、退出码及manifest本身由独立清单补齐。

最终checkpoint：`ckpt-last.pth`，478810419 bytes，服务器流式SHA256两次一致：

`4fd73dd8c265781225ba63a712a5589b175c94f0ea0878a69ebf466265ebebe9`

该实测值与completion及payload_manifest完全一致。没有torch.load、模型加载或checkpoint反序列化；内部模型/optimizer张量未逐项展开验证。本机仅下载了32个非checkpoint证据文件，不能将本审计视为checkpoint已经本机备份或可清理服务器权重的确认。

## 训练合同与实际顺序

独立核对3900条metrics：forward/backward/clip/optimizer step各3900，LR scheduler及BN scheduler各100；100 traversals；每批8、每遍39批，固定315病例、63来源，与21开发来源分离。每一批case/source顺序逐项匹配原M0同折冻结order，raw order SHA与原文件一致，canonical SHA在初始化、完成记录及曝光记录中一致。

从所有真实batch重算：病例及来源曝光各31200，drop300；每例训练曝光＋drop恰为100。实际训练前315个NPZ的原始字节哈希记录严格匹配固定训练allowlist，未混入开发或confirmation payload。本次审计只复用这些训练前哈希凭据，没有重新读取NPZ数组。

逐条核对loss有限、denoise为0、reconstruction/total标签一致，clip阈值10、已提交step标记、实际LR与BN momentum时序均符合原runtime。末步epoch99/batch38。completion生命周期耗时约25.62分钟，仅作该run记录，不与旧设备基线推导效率优势。

## 初始化、模型和优化器

实际factory完整构造证明与已冻结native GPU准入证明相等；原共同模块保持、encoder6个SSM和decoder16个SSM及共享PE按固定私有种子构造。完整初始persistent-state指纹与准入eval_1初始模型逐字节相同：

`beabbeb8c06c387d6ac54c3ec1825fbe7cd6bd529428c4f79299a5525cef301b`

初始parameter SHA256为`2c7d4e3094a98834ed7e2627c610b8015d183146e10270db1a2dccc56c751d8e`，seed0。没有checkpoint warmstart或resume。该相等性是初始化重放证据，不意味着训练梯度或最终权重应位级重复。

实际F0参数总数39,903,169，encoder9,929,472、decoder21,356,160、other8,617,537。从411条参数分组记录的shape独立重算一致、无重名；22个A_log及22个D保留no-decay。实际各组weight_decay为0或0.0005，AdamW lr/betas/eps等符合合同。optimizer.defaults中0.01是被每组显式覆盖的构造器默认值，不是本次参数组实际衰减率，不据此误判训练合同改变。

checkpoint内部stage沿用旧BCSP_INPUT_DENSITY_V1来源标签；run_identity明确标识CRANIAL_BCSP_FULLMAMBA/F0-P-v2/C/seed0，二者不混淆。实际模型、loss、runtime源码及70条非payload复用记录重新哈希匹配。已继承固定无attention模块/源码准入；本审计没有重新对3900步的opaque native kernel内部逐算子审查。

## F0几何日志

F0_geometry.jsonl恰有3900条，与metrics的step/epoch/batch及每批8个case完全对应。逐条检查coarse/dense质心、半径、min/max的字段、batch维度与三维坐标形状；所有数值有限、半径非负、min/max及质心范围关系一致。数据为D-only归一化坐标，不是world-mm或接口精度。日志来自同次forward的脱离计算图摘要，没有以这些训练日志代替Native开发评价。

## 资源与权限

3902条资源记录完整覆盖after_step1…3900、before_final及after_final。独立重算全部GPU阈值、RSS、输出大小和wall范围通过。采样RSS最高约1.551GiB，Torch allocated峰值约12.932GiB、reserved约13.785GiB，SMI最高14604MiB；冻结上限均未改变。资源监测起点含模型准备，与completion生命周期计时不同。

PID数值口径差异按既有DIAGNOSTIC_ONLY合同记录，不认定为外来进程证据，也不声称证明GPU专属。RSS/SMI是采样监测；最小磁盘空间由固定源码的local guard执行，资源行没有逐条free-disk数值，审计不虚构该项遥测。未使用专属硬cgroup保证。

本次服务器写入0、新forward/backward0、checkpoint加载/下载0；没有重训、BNCal、development evaluation或Fold D启动。BNCal/evaluation/resume完成标志均为false。

## 下一步

Fold C已正式冻结，可按既定计划推进Fold D配对训练准备；保持8k→8k、3900更新、相同初始化策略与对应M0同折顺序，不依据C折训练loss调参或筛病例。当前F0短入口只接受Fold C，因此需要限定的Fold D入口适配及针对性CPU/P3，再创建待授权request；不重复GPU preflight。

本次尚无F0开发集补全/接口评分，不能判断全Mamba是否优于M0/T0。原checkpoint及结果继续保留服务器，未经后续归档确认不得清理。

机器证据：post_training_freeze_audit_result_v1.json；原始前后清单、取回凭据、非checkpoint产物及源码复核结果保存在本目录。
