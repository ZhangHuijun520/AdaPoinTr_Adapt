# TRACE D0：测试fixture限定修正、CPU验证、P3及待授权request

日期：2026-11-17。状态：**新版人工CPU 30项通过；本机P3通过；最终request保持待授权，未部署或执行。**

## 1. 本轮实际变更

保留v1测试文件及其失败产物，新增`test_bcsp_trace_D0_CPU_v2.py`。相对v1，仅进行以下修改：

1. 改用全新保留目录`CPU_batch_v2`。
2. 为人工模型构建创建独立的`buildq`副本，将其中`mother_source`绑定到本机已存在的同字节母版文件，并显式断言大小、SHA256与原服务器绑定相同。
3. 仅将此`buildq`传入人工模型构建；原授权、服务器配置和运行路径不变。

观察器`bcsp_trace_D0_observer_v1.py`、生产入口`bcsp_trace_D0_entry_v1.py`和CPU分析实现`bcsp_trace_D0_analysis_v1.py`均保持原字节。既有head、factory、encoder、decoder、母版和守卫没有修改。

## 2. 本次唯一一批CPU验证

使用本机既有PyTorch 2.5.1／NumPy 1.26.4环境，线程数2，CUDA_VISIBLE_DEVICES为空。新版单批30项全部通过，未自动修复或再次运行同一批次。

验证包括：

- 完整authorize路径、单向runtime绑定，以及计数、身份、输入和checkpoint漂移拒绝。
- 在人工encoder／decoder配合下，调用真实母版forward／FC及冻结G1/G2 head、factory，核验有无观察器时输出精确相等、状态／RNG不变。
- 实际head输入、描述子、FP32近邻分数与索引采集；G1不伪造KNN8。
- FP32排序并列与FP64几何重算次序不同的人工边界情况；零间距保持不可估，不添加epsilon补救。
- 重放界限与E/J／风险评分的人工几何验证。
- 使用生成点集和人工state_dict完成四模型、每模型20次、合计80次的入口循环，核验逐次claim、清单、哈希及归档。
- forward异常、状态改变及RNG改变均按精确计数停止，落盘失败证据。
- 在真实读取守卫激活的独立人工子进程中加载完整冻结模块链，并在关闭守卫前保存异常回溯。
- 900秒POSIX启动模板、日志父目录先于重定向及显式退出码；本轮没有生成生产launcher。

人工完整循环不等于80次真实D0诊断。测试读取的NPZ与checkpoint均由本批生成，没有读取真实病例数组或训练权重，没有实际Mamba／CUDA模型执行或optimizer step。

## 3. P3结论

`TRACE_D0_P3_v1.json`状态为`TRACE_D0_LOCAL_P3_PASS`，24项证据核对通过，包括：

- 30项CPU结果与冻结范围一致，四份受测源码哈希一致。
- 新测试差量仅限已授权fixture修改，三个实现模块保持不变。
- 原v1失败证据完整保留。
- 80条人工清单、逐次claim、文件哈希、82个归档成员回读及sidecar一致。
- 真实读取守卫子进程通过，负路径计数和权限边界完整。
- 待执行范围仍为80次完整forward，loss/backward/optimizer step/BNCal/warmup/retry均为0。

P3表示本机实施就绪，不代替真实CUDA诊断、正式post-diagnostic freeze audit或科研结果判断。实际执行前仍须核验容器、GPU、磁盘、冻结资产及全新路径。

## 4. 最终待授权request

文件：`TRACE_D0_execution_request_v1.json`

状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`

完整SHA256：

`7ad5a27aee302b877af7903b00da107c47560250d18135566315609b12a01b0f`

该request绑定最终观察器／入口哈希、通过的P3、P0准备范围及原Native父请求。P3不反向绑定最终request哈希，避免循环依赖。

固定执行顺序G1_C→G2_C→G1_D→G2_D，各20个预定病例；共40病例／40来源、80次完整forward、零更新。GPU阶段不读GT，不运行loss、backward、BNCal或训练。后续本机CPU重放／关联分析另行授权，不由GPU入口自动调用。

资源保持900秒、RSS 8GiB、torch峰值20GiB、SMI 22528MiB、产物总量1GiB、启动空闲6GiB／运行空闲4GiB的既定范围。监测不是内核硬隔离，也不保证执行时设备仍空闲。

绑定容器`shu-common-25721452-notebook-yxwd3w-0`，GPU UUID `GPU-4b19574a-832d-b4fe-e655-a57462954d6a`。这是P0已核对身份，本轮没有连接服务器重查；发生变化时不能直接执行。

## 5. 本轮未执行与紧接着一步

本轮未操作服务器、上传、部署、读取真实权重／病例数组或运行GPU；未材料化生产授权回执、runtime、launcher及单次claim。CPU目录中的ARTIFICIAL文件均为测试fixture，不是生产执行内容，不能运输并使用。

下一步仅需冻结最小运输包及不覆盖安装映射，再按既定边界上传核验、授权安装／执行。未取得对应完整哈希的执行授权前，不启动D0；本次P3与request也不授权G3或六次训练。
