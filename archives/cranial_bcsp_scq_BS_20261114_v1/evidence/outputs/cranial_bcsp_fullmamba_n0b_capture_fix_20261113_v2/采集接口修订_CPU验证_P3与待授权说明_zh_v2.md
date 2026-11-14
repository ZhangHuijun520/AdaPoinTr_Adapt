# N0-B采集接口限定修订、CPU验证与P3

2026-11-13。当前状态：**implementation-only完成；新版request待单独执行授权。** 本轮服务器操作0、真实模型forward0、GPU调用0；未部署入口，未生成授权回执、runtime scope、launcher或启动标记。

## 1. 唯一修订

保留旧入口v1及失败证据。新增`n0b_trace_worker_v2.py`，仅修改Capture类：decoder hook只计数；S/F/Q/X从首层LQIBlock的真实位置参数0/1/2/3读取，排序、逆序、self/cross邻域索引仍从既有位置参数采集；复制使用`detach().clone()`，hook不返回替代参数或输出。

源码核对了冻结母版的实际全keyword调用`self.decoder(q=q,v=mem,q_pos=coarse,v_pos=coor)`，以及冻结LQIDecoder调用首层block时前四参数确为`q,v,q_pos,v_pos`。first-block pre-hook在该层实际变换之前采集，读取的是已传入原decoder的相同Query/Memory张量，不用近似FPS、原8192输入邻域或F0替代。

其余入口正文保持一致：权重加载、模型构造、eval/inference_mode、输入allowlist、参数/RNG检查、单次计数、七次上限、完整输出等价检查、资源预算及失败即停均未改变。原模型/factory/decoder和环境不变。

## 2. 人工CPU回归

**41项全部通过**，使用本机CPU PyTorch2.5.1，仅人工Decoder/Block和合成点集，不加载真实模型。

- 覆盖与母版一致的全关键字调用，以及混合、全位置调用。
- X/F与Q/S使用不同数值，逐字段验证来源与索引，避免相同测试张量掩盖错配。
- 验证输出身份、输入/state/RNG不变、独立克隆、hook移除、短参数拒绝与重复调用拒绝。
- 用旧v1 hook在真实调用风格下复现缺Q/S，说明回归覆盖旧失败。
- 保留normalized≤1e−6和world≤1e−3mm两种独立容差；超限失败，不放宽。

CPU结果不代表真实CUDA接口、资源及七病例等价性已经通过。版本/硬件差异仍在未来执行时核对。

## 3. 本机P3

`P3_capture_fix_v2.json`记录CPU报告、worker、实际母版及decoder源码的SHA256，验证Capture以外源码未变、原v1字节未变、没有新增backward/optimizer step调用、旧失败尝试完整保留。新worker SHA256：

`82fd2a2582ff045564485e4aea3a0b98fb18cb5d76dc1235dbd06c4bc9835615`

## 4. 新版待授权request

文件：`N0B_seven_LQI_capturefix_execution_request_v2.json`。

完整SHA256：

`4a554bc7bd23eaebf62982cda6cecc99948f47c9511cedcd9fbfa28e69630baf`

状态：`AWAITING_EXPLICIT_USER_AUTHORIZATION`。七病例、原权重哈希、模型、输入、输出等价容差、资源阈值均不变。未来需新输出目录和tmux；旧请求/claim不得复用。

复用原任务目录中`weights_restored_v3`的两份完整LQI权重，以及七份已核验对照输出，不重新安装环境、上传整权重或重复旧GPU preflight。本轮未连接服务器，故不宣称这些路径当前仍存在；执行前必须重新核验身份、哈希、资源和全部新目标不存在，异常即停。

旧尝试已消耗1次forward、0可用trace。新版拟新增最多7次，0 backward/更新；若全部执行，历史累计为8次forward，不能抹除旧1次。只有对上述完整request哈希单独授权后，才可材料化新回执、runtime与单次launcher并执行。
