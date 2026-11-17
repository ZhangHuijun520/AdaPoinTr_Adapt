# SPCG G0_C启动失败：正式只读冻结审计与完整导入／回溯生命周期核查

日期2026-11-16。request：`0f5a8aca25b1acd43c3bd258ae8ddf7ea3d06f81d020f2c38bde1ea7a944ef08`。

## 审计结论

FORMAL_READONLY_TRAINING_FAILURE_FREEZE_PASS。9个安装文件集合、大小和SHA一致，request／授权／runtime单向绑定和单次claim一致。退出码1，worker及固定tmux均不存在。输出仅worker.pid、launch.log、startup_failure.json、exit_code.txt和空tmp目录，没有模型构造、初始化、metrics、resources、checkpoint或completion产物。

失败在导入observe时，早于训练runtime导入、模型构造、Budget构造和dispatch。因此forward/loss/backward/optimizer step均为0；此处依据源码顺序、失败调用栈及产物缺席，不伪造未生成的运行计数文件。本request已消耗，不能复用。

本轮哈希213,068bytes，仅读取固定源码及失败文本，不读取NPZ、加载checkpoint、运行模型或SMI。服务器无写入。

## 一、完整观测导入链

| 环节 | 依赖与状态 |
|---|---|
| training entry | 先加载metadata contract，再安装文件策略、加载torch及项目模型类，随后显式加载encoder/factory/LQI四模块 |
| training bridge | 顶层仅stdlib；dispatch内torch，未引入其它SPCG模型模块 |
| observe：bcsp_spcg_runtime_v1 | 顶层hashlib、pathlib、torch，以及`from bcsp_spcg_head_v1 import need` |
| 间接head | 顶层torch与nn；仅提供need被observe使用，但Python仍需执行整个head模块定义 |
| frozen training runtime（尚未进入） | torch Dataset/DataLoader、tools.bcsp_adapter、bcsp_training_contract_v1；原18文件项目绑定包含tools/bcsp_adapter.py，contract已由authorize显式加载 |

观测工具所需head实际存在：

`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_cuda_20261116_v1/bcsp_spcg_head_v1.py`

大小4209bytes，SHA256 `687c123ae7d0769c9ee89e2067367ff7fc2762f66bf47a814bf077ac68c59d3b`，与既有CUDA冻结一致。

训练request implementation没有head记录，入口也未把它显式载入sys.modules；sys.path只包含新训练entryroot、provider和site-packages，不含旧head所在目录。文件存在不等于该模块可导入。只把旧目录追加sys.path还会弱化精确身份控制，不是首选修法。

已核查该本轮新增链的项目直接／间接导入，发现的缺口是这一项；原模型／provider可沿用冻结证据。静态核查不保证未来所有运行分支无其它错误，不据此承诺下一次必然成功。

## 二、回溯守卫生命周期

entry except写startup_failure.json后重新raise；finally执行guard.close()和utc.close()。guard.close清空fds，但sys.addaudithook注册的Policy仍存在，并在解释器sys.excepthook／linecache读取源码时调用guard.allow→verify→fds[path]。

此次需要回溯的observe路径已经在records内，却在fds关闭后查找，故抛KeyError。该问题不同于前期“路径未绑定”，也不同于Windows CRLF兼容；它是Linux生产入口的异常收尾顺序遗漏。正常进程结束前不应在仍有活跃审计hook可能读源码时关闭其依赖而继续打印未处理异常。

## 三、CPU证据为何未拦截

先前16项测试在新进程中直接导入入口／bridge，observe由人工SimpleNamespace替身代替；没有真实source()加载observe，更没有覆盖它的间接head依赖。已有独立policy回归在描述符仍开启时测试traceback，未覆盖生产entry的except→finally→sys.excepthook顺序。人工3900次调度通过不能等价为真实生产启动链通过。

## 四、建议下一步一次限定修订（本轮未实施）

1. request增加上述head精确路径／大小／SHA；启动时在observe之前显式source加载head，并纳入同一精确只读守卫。保持head源码和所有科研模型、loss、数据不变，不扩大sys.path目录白名单。
2. 在守卫仍开启时将完整格式化异常、阶段及链式异常写入限定日志，然后以明确SystemExit(1)结束，finally再关闭guard／UTC，避免未处理原异常离开main后触发已失效审计hook。不吞掉错误、不将失败变为0退出、不增加重试。
3. 一批CPU子进程回归实际source()依次加载bridge→head→observe→继承runtime的合同；以人工依赖替身隔离CUDA，但不替换正在验证的observe/head源码。真实文件策略下覆盖读取／写入拒绝和生产异常退出路径，断言exit=1、原始错误落盘、无KeyError／sys.excepthook二次错误。
4. 新P3后创建全新run/control/output及request；原request维持已消耗。新模块不重复GPU准入，不改变3900步或1GiB／3600秒等阈值。

本轮只完成审计与限定方案，没有修改代码、生成request或运行实验。
