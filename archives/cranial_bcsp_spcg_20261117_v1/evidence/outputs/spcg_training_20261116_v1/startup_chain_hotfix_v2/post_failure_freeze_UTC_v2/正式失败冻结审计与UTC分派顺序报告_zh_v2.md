# G0_C v2失败冻结与UTC精确守卫分派顺序审阅

2026-11-16。状态FORMAL_READONLY_G0C_V2_UTC_FAILURE_FREEZE_PASS。

request完整SHA：`6a1ff266ff9eae8db51b5809b7db3aa87b72900625d267a4ee3b0a5a9a489f42`。

## 正式冻结核验

10个已安装文件集合、大小与SHA匹配；request、授权、runtime单向绑定和单次claim一致。退出码1，worker／tmux不存在。输出仅worker.pid、exit_code.txt、launch.log、startup_failure.json、training_error_traceback.json及空tmp。失败在factory构造Mamba时的依赖导入，尚未完成模型构造，也未创建Budget或进入dispatch；无forward、loss、backward、optimizer step。

本次完整异常成功在GUARD_ACTIVE_BEFORE_CLEANUP阶段落盘，无guard关闭后KeyError或sys.excepthook二次错误。上次head导入与异常收尾修订已经越过原阻断，不能将此次失败归回该旧问题。当前request已消耗，不复用。

## UTC资源本身正常

当前只读重新核验：/usr/share/zoneinfo/UTC是符号链接，link text为Etc/UTC，精确解析到/usr/share/zoneinfo/Etc/UTC；目标为无链接祖先的普通文件，118bytes，SHA256为：

`ab1ddb33c7187e56408033a8165ea3b1432e024710e7ab2aafec036a8bd7f09a`

与已经冻结并在CUDA入口使用的ExactUTCReader合同完全一致。没有发现需要重装pandas、transformers或时区文件的证据。

## 根因：训练入口适配层分派顺序遗漏

正确且已在通过CUDA入口使用的顺序为：整数FD快捷返回→utc.allow精确例外→source_guard→其余payload／目录规则。

当前训练入口顺序为：整数FD快捷返回→guard.allow→super().check。虽然super所属的原training policy有utc.allow，但guard.allow先调用clean，看到UTC是链接后直接抛错，根本没有机会到达既有UTC精确验证器。

因此，资源有精确绑定、UTCReader也已初始化，并不表示该精确例外实际可达。当前失败由训练入口适配层把通用源码清理放在精确UTC例外之前造成，是实现遗漏；不是科研模型、数值loss或依赖缺失。

原始调用链为Mamba包→transformers generation→sklearn→pandas→dateutil→UTC。最内层为symlink拒绝，外层GenerateDecoderOnlyOutput ModuleNotFoundError是包装异常，不能根据外层文字安装／升级包。

## 建议下一步最小修订（本轮未实施）

仅在训练Policy.check整数FD判断后、guard.allow之前加入已有utc.allow(filename,write)分派，与通过CUDA路径一致。保持ExactUTCReader的精确链接文本、目标、大小、SHA及只读验证不变，不泛化放行其它符号链接。

一批CPU回归需覆盖UTC读取先被精确验证器处理、UTC写入拒绝、精确例外校验失败传播、其它链接仍拒绝、源码正常读／写拒绝、数据守卫不变以及异常落盘／退出顺序。CPU人工fixture应区分策略调用顺序验证与真实Linux链接目标验证；真实资源身份已由本次只读审计补证，不需要重新GPU准入。

CPU和新P3通过后创建全新v3待授权request，保持所有模型、数据、loss、3900步、预算及provider不变。本轮不修订、不创建request、不导入依赖、不重跑模型。

机器证据formal_audit_result_v2.json；原始冻结server_evidence.json及stdout.bin/stderr.bin。
