# N0-B七例LQI实际Memory追踪：执行停止及失败冻结

2026-11-13。状态：**本次尝试已消耗，未完成七例Memory追踪，不自动重试。**

## 本次授权及准备

授权为七个固定开发病例、最多7次LQI Native eval forward、0 backward、0 optimizer step。病例为C/012/parietotemporal、C/013/frontoorbital、C/038/random_1、C/041/frontoorbital、D/060/bilateral、D/008/frontoorbital、D/052/frontoorbital。

当前容器t6ibfm-0。53项已有源码、配置、provider和七例输入的大小/SHA256通过。真实GPU为4090D、driver570.190，与冻结LQI预测时575.51.03不同，事前披露并保留normalized max-abs≤1e−6且world max-abs≤1e−3mm双容差。

完成12项人工CPU检查及本机P3，没有修改原模型/factory/decoder源码，也没有重编译或重装provider。CPU检查未覆盖实际母版的全关键字decoder调用，这是本次观察工具的验证缺口，不能将其解释为Mamba科研假设失败。

## 权重恢复与运输历史

七份冻结对照输出直接上传并核验。两次完整权重上传失败，一次发生在重新登录后；客户端的“token可能过期”为通用异常提示，未证实根因。失败残留未覆盖或删除，且当时模型未启动。

随后只为本次任务采用固定16MiB分块传输，在全新weights_restored_v3目录无覆盖拼接。两份完整权重SHA256均匹配原始正式训练审计：

- C：`d8d819ffb9ed1f931c60f0ee96e9ae9c4093d61c73c2152a52f13b8cd95a0ddf`
- D：`2afd1b4540b856d4c829786729d8c2df80943edd65a0f01af412940fd973e5ed`

现有恢复资产可供未来新请求精确复用，无须重新上传/安装整套工具或重跑旧GPU preflight。任务运行根为`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1`，仅作为已执行事实记录，不是继续执行授权。

## 实际执行与故障

|项目|实测|
|---|---:|
|单次tmux启动|1|
|forward尝试/已返回模型输出|1 / 1|
|通过冻结输出等价检查|1|
|可用Memory trace|0|
|backward / optimizer step / loss调用|0 / 0 / 0|
|worker退出码|1|
|worker是否仍存活|否|

第一例为C/012/parietotemporal。其Q/P与冻结预测逐元素一致，normalized和world max-abs四项误差均为0。该病例已证明本次恢复在这一次运行中的输出身份；不能推广为其余六例已验证。

随后导出观察缓存时触发`KeyError('Q')`。母版实际调用为`self.decoder(q=q, v=mem, q_pos=coarse, v_pos=coor)`，四个参数均按keyword传递。新增decoder pre-hook只读取位置args，因而没有收集Q/S/F/X。首层block hook能捕获索引，但不能补齐缺失的坐标/特征。人工fixture使用全位置参数，未覆盖这一真实调用方式。

没有生成NPZ轨迹，不据此计算d1/d8或判断局部Memory语义，也没有继续其余六例。`completed=0`指完整追踪产物为0，不表示没有发生forward；forward计数必须保留为1。

## 只读冻结结果

失败后下载并按独立服务器哈希核对6份输出文件；两份恢复checkpoint重新计算SHA256仍匹配；确认worker已退出且轨迹文件数0。详见`failed_attempt_freeze_v1/failure_freeze_result_v1.json`。

未完成模型运行后state/RNG指纹，且未取得forward后的完整峰值样本，因此不声称本次通过完整状态/资源冻结审计。没有训练、重试、resume、评价或SCQ实现。

## 下一步限定建议（未实施）

优先将S/F/Q/X改为从既有首层LQIBlock真实位置参数采集，decoder hook只计数；该首层接收的仍是未经该层变换的真实query/memory输入。补全与母版一致的全keyword、混合及位置调用fixture，验证只读采集和原输出保持，再完成CPU/P3。

保持模型、权重、病例、双容差与资源阈值不变。通过后创建新版本待授权请求，复用已完整恢复的两权重和对照输出。不得复用本次已消耗启动标记；若另行批准重新执行完整七例，应明确历史累计会成为8次forward，而不是抹除原1次。

本说明不授权上述修订或新forward。N0-B与整个N0的实际Memory证据门仍为未完成，不能进入SCQ训练准入。
