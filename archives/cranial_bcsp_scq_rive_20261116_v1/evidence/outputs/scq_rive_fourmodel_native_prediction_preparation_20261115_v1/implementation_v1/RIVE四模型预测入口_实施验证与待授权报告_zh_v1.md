# RIVE四模型Native预测入口实施、CPU验证与P3报告 v1

## 交付结论

隔离入口及人工CPU验证完成。唯一一批CPU检查53项通过，退出0、无stderr、无超时；完成420次轻量合成生命周期forward和2次人工母版路径forward（RF-Static／RF-Requery各一次）。P3 24项检查通过。没有真实点集读取、真实checkpoint加载、GPU或服务器调用。

最终待授权request：`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\scq_rive_fourmodel_native_prediction_preparation_20261115_v1\implementation_v1\pending_request_v1\payload\RIVE_fourmodel_native_prediction_execution_request_v1.json`。

大小17683字节，完整SHA256 `ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774`。

状态AWAITING_EXPLICIT_USER_AUTHORIZATION，execution_authorized=false。未材料化生产授权回执、runtime、launcher或claim；没有冻结运输包、安装或执行。

## 唯一科研范围

Static_C、Requery_C、Static_D、Requery_D依序各105例，共420次Native forward。每次batch1，8192输入／8192 dense输出；保存256 coarse及Qraw/Q0/Q1/Q2/delta/delta0/delta1。210个唯一输入，42来源，使用原开发病例及原D-only归一化，不筛病例或调参。

零loss/backward/optimizer、零warmup/TTA、零BNCal；不接入GT配准、过滤或条件。state/RNG逐模型前后指纹检查、失败即停及单次claim保留。现有预测预算7200秒、RSS8GiB、Torch20GiB、SMI22528MiB、输出1GiB、最低空闲4GiB均未扩大；后续空间准入需覆盖输出和归档并存。

## 实现差量与验证

仅隔离新增入口及测试等本机候选；原RF入口、模型、provider和训练源码不改。更改7个入口函数用于RIVE schema、四模型pin、两臂索引与证据验证、RF-only分派、420计数和完成事件；14个数据读取／模型输出／精确源码读取／资源／权重加载／launcher等核心函数AST保持一致。

人工验证覆盖完整authorize单向绑定、旧630预算与历史权重拒绝、四份真实审计元数据、实际factory/encoder/RF加载路径及异常回溯、写入和相邻路径拒绝、两种人工母版状态/RNG稳定、合成checkpoint严格加载、partial-only读取、420预测及424成员合成归档、首次失败停止、无context/trace、POSIX启动渲染。测试环境为本机既有PyTorch CPU环境，CUDA_VISIBLE_DEVICES为空。

## 配对证据与限制

四份RIVE正式训练冻结证据已绑定，两折均按本轮同设备配对条件记录；旧RF阶段跨设备限制不被追溯更改。Mamba有限梯度非确定性及单seed局限继续披露。

CPU验证不证明CUDA路径或补全效果。当前服务器资产及空间尚未重新核对。历史纠正后的开发路径按fold_binding／病例／来源／哈希约束，不能按foldc/foldd目录名猜测；最终执行前必须重验210个输入和四个checkpoint，不复用旧运行权重。

## 下一步

可单独开展一次必要的服务器只读就绪核对：确认当前设备、实际相关冻结资产与历史准入凭据、210输入、四个checkpoint、新安装目标及资源；通过后冻结最小运输包与不覆盖安装映射。无需重复已通过的GPU preflight。部署和420次预测仍需单独明确授权最终request完整SHA256。
