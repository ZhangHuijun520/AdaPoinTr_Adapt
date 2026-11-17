# TRACE D0：不覆盖安装完成报告

日期：2026-11-17。状态：**6文件安装及即时回读通过；待正式只读安装后冻结审计。**

## 实际执行结果

- 安装前容器为`shu-common-25721452-notebook-yxwd3w-0`，uid=1000，与冻结身份一致。
- GPU UUID为`GPU-4b19574a-832d-b4fe-e655-a57462954d6a`，驱动570.190；显存已用1MiB，利用率0%。
- 安装前磁盘可用7875854336 bytes，约7.33GiB，满足6GiB启动门槛。
- 四个上传文件及归档7个成员核验通过，77个复用文件全部完成新鲜大小／SHA256校验，涉及2623709897 bytes。
- 写入前复查上述77文件及4个上传文件的dev/ino/size/mtime/ctime签名未变；未将atime纳入内容变化判据。
- 核验全部6个目标、新安装根及预留执行路径不存在，父目录安全后，仅排他创建1个目录、以`xb`写入6个文件；没有覆盖、删除或自动重试。
- 安装后逐文件回读大小／SHA256及0644权限，全部匹配；安装根目录精确包含6个目标。

## 安装位置与清单

安装根：

`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_trace_D0_20261117_v1`

| 文件 | bytes | SHA256 |
|---|---:|---|
| bcsp_trace_D0_entry_v1.py | 15282 | e654857da63ed3e871d3485e63a0fb2f8036d60870c933f467f505da85df754e |
| bcsp_trace_D0_observer_v1.py | 5170 | 08f4ec5b71fa91bf4fc7f09c26bb1b8b08c56251d486a2d66c6f159a24311ae7 |
| bcsp_trace_D0_analysis_v1.py | 11506 | babfdefc43c47f5af01a1e4c292cbed151924cd1ebaa903bd1167a83e1d738c8 |
| TRACE_D0_preparation_scope_v1.json | 69440 | 5271bdca720cb4e3ec8a260abddb8374006a4e9aa6ecfc494f9f5df5f001a95f |
| TRACE_D0_P3_v1.json | 3130 | b13810daa570c1032965fe74c8e1ae4baa3cea5f896f9e299851a60f17f07b3b |
| TRACE_D0_execution_request_v1.json | 73054 | 7ad5a27aee302b877af7903b00da107c47560250d18135566315609b12a01b0f |

映射自身仅在内存读取，没有安装映射文件、额外依赖、权重或测试fixture。

## 权限与证据边界

执行为一次只读前置核验和一次不覆盖安装调用，两次调用均成功；本机曾精简尚未提交的安装脚本以满足短命令长度，不属于远端安装失败或重试。

没有运行包内代码、测试、GPU、forward、loss、backward、optimizer step、训练或CPU科研分析。生产授权回执、runtime、launcher、单次执行claim和D0结果目录均未创建。request状态仍为`AWAITING_EXPLICIT_USER_AUTHORIZATION`。

机器可读回执：`installation_receipt_v1.json`。原始stdout/stderr、调用退出码及最终安装核验源码均在本目录保留。

安装时的即时回读不代替独立正式post-installation freeze audit，也不构成80次forward执行授权。下一步应单独授权正式只读安装后冻结审计，仅复核6个目标、冻结映射及执行路径边界，不运行工具或模型。
