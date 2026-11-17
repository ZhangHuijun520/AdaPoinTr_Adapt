# SPCG v2正式只读失败冻结审计与路径合同核查

2026-11-16。request SHA256：`a2b1961158b58199e212130654ddd274ce617c90e24448f22ba70a0062c2343e`。

**审计通过，实验执行失败；未取得完整CUDA准入。** 本轮无服务器写入、SMI重查、模型调用、真实NPZ读取或重试。

## 冻结核验

7个安装文件集合、大小与SHA匹配；授权、runtime单向绑定及单次claim一致。退出码1，tmux和worker均已不存在，无completion，无real_D_00.npz等半成品文件。全部原始stdout/stderr及server_evidence.json保存在本目录。

六个人工阶段均有成功阶段记录：G0/G1/G2分别eval B1与train B8；各训练阶段完成完整loss和backward，参数未更新。最后计数7forward／3loss／3backward／0step，其中第7次为首个真实D。计数在调用前记录；调用栈表明首个真实forward已返回至保存函数，但其REAL_D_ONLY成功记录尚未产生。不能将其计作完整真实诊断病例完成。

三臂均有state/RNG/modes恢复为true的记录；本轮只核验记录，未加载模型重演恢复。38条资源记录全部条件通过，采样最大allocated约12.81GiB、reserved约13.98GiB、RSS约1.92GiB，SMI14800MiB。这是失败前部分执行的观察，不能替代11次全流程或后续训练资源准入。

## 主失败：精确输出合同遗漏

入口调用继承make_policy时，inputs为五个真实输入文件，checkpoints为空，**predictions也传入空列表**。该policy对NPZ等payload先检查allowed_write，然后才可能走普通output-root规则。因此，即使文件位于合法输出目录，也不会自动获得NPZ写权限。

save_memory明确要写固定的real_D_00.npz至real_D_04.npz，但五条绝对路径未传给policy。第一次np.savez_compressed打开real_D_00.npz时即被拒绝，故五个观察结果全部未写出。这是入口与写入守卫合同不一致，不能据此判断SPCG模型或重查询信息无效。

## 次级失败：异常回溯读取合同遗漏

Python输出原始异常时，linecache尝试读取已绑定parent_helper源码：

`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_CD_native_prediction_20261111_v2/bcsp_f0_twofold_native_predict_v1.py`

大小31713bytes，SHA256：`b1318c0ab8441e56dfd7133c83b2ae07435932359f1843fd7c3616c835e6f72b`。

它在安装／启动前已有精确内容绑定，import发生于policy安装之前；但安装policy后，该路径不在八文件source_guard内，也不在允许读取根中。异常回溯再读源码因而被拒绝，产生sys.excepthook二次错误。不能通过泛化放开third_party或整个项目解决。

## 仅供下一步授权的最小修订

1. 明确构造新run内real_D_00.npz至real_D_04.npz五条精确输出路径并传入既有predictions允许清单；保留输入、GT、checkpoint、链接及越界拒绝，不放开任意NPZ。
2. 为已冻结parent_helper添加精确大小／SHA只读绑定，使正常异常回溯可读取；同一调用链只核对已绑定helper／UTC等真实回溯需求，不新增通用库存框架。
3. CPU回归必须调用实际make_policy审计路径，覆盖五个允许输出、邻近未授权NPZ、真实输入写入拒绝、源码写入拒绝及真实traceback.format_exception／linecache读取；不能再仅用空save_memory回调断言输出合同通过。
4. 保持模型、U/H、provider、loss、资源阈值及11／3／3／0不变；新P3后创建新版本request。本v2已消耗，不重试、不覆盖既有安装。

以上修订本轮均未实施。最小修订应同时覆盖真实输出和回溯读取，避免再次逐文件补丁试跑。
