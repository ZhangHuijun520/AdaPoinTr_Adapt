# SCQ四模型预测后正式只读冻结审计

日期：2026-11-14（Asia/Shanghai）。状态：`FORMAL_SCQ_BS_CD_POST_PREDICTION_FREEZE_AUDIT_PASS`。35组检查全部通过。

## 结论及计数

任务退出码0，worker与固定tmux均已结束。B_C、S_C、B_D、S_D各105例，共420次Native forward、420份预测。每份均保存Qraw256、Qused/coarse256、delta256及dense8192；没有context或逐层trace文件。

434个输出文件、18个安装文件及4个控制文件的集合精确匹配。前后两次完整文件哈希及内容相关属性一致，不以atime变化作为失败依据。35份元数据回读后与独立远端哈希逐一匹配。

## 执行及科学输入合同

授权request SHA256：

`ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a`

单向授权回执→runtime哈希关系、唯一尝试claim、launcher原始UTF-8字节均核验通过。实际420条forward声明、预测manifest及几何日志的模型顺序、病例、source、输入及checkpoint哈希、归一化逐条匹配。

同折B／S输入、顺序和坐标框架相同；每模型21个开发来源、每来源五类缺损，105例齐全。210份输入及四权重重新流式核验哈希；未加载真实权重，未读取GT数组。

历史训练身份保留为t6ibfm-0；实际预测身份绑定zbpgzu-0。四份历史训练freeze不改写，新GPU／驱动通过已冻结重绑定补充协议披露。不能声称当前与历史设备预测位级等价。

## 状态、RNG及几何

四模型记录的参数及持久BN状态指纹前后一致，CPU／CUDA RNG哈希及Python／NumPy状态前后一致，格式核验通过。实际构造记录匹配LQI父骨干及SCQ B／S变体，B总参数39903169，S总参数40596676，S新增693507参数，无注册attention模块。

420份保存输出均为有限FP32，Qraw、Qused及delta满足已冻结的一致性条件；B的delta为零。独立从保存点集重算coarse、dense和Qraw的质心、包围盒、回转半径、协方差谱，以及dense相对coarse偏移和delta范数，均与日志一致。这仅证明输出与日志一致，不证明解剖或接口精度改善。

## 资源

845条资源记录的阶段、forward计数和全部停止条件逐条重算通过。采样峰值RSS为1981640704字节、torch allocated为243860992字节、reserved为281018368字节、SMI显存717MiB。最后完成记录墙钟175.895秒，只是运行记录，不作为正式效率benchmark。

资源监测为采样观测，不声称独占硬隔离或PID命名空间所有权。

## 归档及下载

服务器目录：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2/`

需要下载的四个文件：

1. `development_predictions_v1.tar.gz`
2. `development_predictions_v1.tar.gz.sha256`
3. `development_predictions_v1.tar.gz.bytes`
4. `development_predictions_v1.tar.gz.contents.sha256`

压缩包大小40571136字节；SHA256：

`57e7c761510bd8fb0f4758a49eb38354231ba8b0893eab16513f1b478350838d`

426个归档成员的大小、哈希和字节内容与当前输出逐一一致，未在服务器解压落盘。三个sidecar与压缩包、成员清单精确匹配。精确四文件路径／大小／哈希记录见同目录`download_four_files_manifest_v1.json`。

建议本机长期保存目录：

`E:\ResearchBackups\AdaPoinTr\BCSP_FULLMAMBA_SCQ\2026-11-14_native_development_eval`

尚未将预测压缩包下载或核验为本机长期备份。下载后先做本机四文件核验，再另行准备统一CPU评分；本次未创建或执行评分request。

## 审计边界及本机保存问题

服务器写入、新forward、backward、checkpoint反序列化、GPU调用、GT数组读取、评分及BNCal均为0。仅使用NumPy读取已完成预测的输出数组进行一致性检查，没有模型恢复或重新推理。

初次本机元数据保存遇到Windows路径过长；原始回传与失败凭据保留。随后在项目内短路径保存已有回传的同一份字节，继续剩余只读审计，没有重复预测或覆盖原证据。短目录保存最终机器可读结果、清单、原始输出和元数据副本。

状态／BN及RNG结论基于冻结实现与已保存前后指纹，未通过重建模型张量独立验证。不从本次一致性审计推断SCQ科研效果。
