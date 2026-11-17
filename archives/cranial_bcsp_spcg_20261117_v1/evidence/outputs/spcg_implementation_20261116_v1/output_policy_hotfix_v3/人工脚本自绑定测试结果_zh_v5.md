# 人工脚本精确自绑定：CPU v5结果

2026-11-16。仅测试fixture新增policy_child.py的大小／SHA记录，添加到现有精确只读FD守卫，保留Windows二进制读取兼容。生产模型、守卫源码、候选v3入口字节均未改变，未扩展生产权限。

唯一一次新版CPU_batch_v5失败，保留failure.json与子进程stdout/stderr，未修复或重跑。没有服务器、SMI或模型调用。

子进程已完成五条精确输出写入及邻近NPZ拒绝、输入写入拒绝、源码只读、脚本自身只读与四份源码traceback检查。它尚未成功返回整批机器可读结果，父测试仍只记录第一项通过，不能将上述执行轨迹标记为12项全通过。

失败发生于测试末尾：先执行g.close()清空fds，后续坏SHA负例调用exact读取源码，仍安装的audit hook回调原守卫，verify访问已清空fds，抛出KeyError。不是预期的哈希拒绝RuntimeError，故测试失败。人工脚本自绑定及CRLF读取的原问题未再出现。

下一步应仅修订fixture生命周期：把坏SHA负例放在guard关闭之前，守卫关闭只在所有检查完成后的finally进行，不捕获KeyError来伪造通过、不放宽任何生产守卫。需要明确授权新的单次CPU批次，旧批次不复用。

新P3及execution request未创建。
