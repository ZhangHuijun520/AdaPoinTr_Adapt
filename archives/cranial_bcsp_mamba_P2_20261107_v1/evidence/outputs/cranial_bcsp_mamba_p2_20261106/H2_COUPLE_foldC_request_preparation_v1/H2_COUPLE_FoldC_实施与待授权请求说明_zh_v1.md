# H2-COUPLE Fold C：实施、CPU验证、P3与待授权request

日期：2026-11-07。

已新增一个隔离的COUPLE训练入口及一个针对性人工CPU测试文件；原AUX入口、H2范围头、adapter和训练runtime的字节与哈希均保持不变。未连接服务器、部署、训练或重复GPU preflight。

## 配对与科研范围

与冻结AUX使用同一原始M0 scratch初始化、同一1025参数零初始化头、315个训练病例、63来源、原完整顺序、batch8、8k输入/8k输出、100次遍历、3900步、31200次曝光、300次丢弃。H1、BNCal、评价、resume和自动重试关闭，不依据AUX训练loss调参。不能载入AUX最终checkpoint作为初始化。

唯一科学变化是启用原已验证的COUPLE软尺度变换；标签、辅助项权重0.1、beta0.1、最大尺度1.25、梯度detach合同均不改变。新入口在实际训练分派中核对全量参数指纹及持久state指纹，必须等于冻结AUX的初始记录；发现差异即停止。已有COUPLE人工CUDA准入证据直接复用，不重复GPU验证。

## 验证与问题记录

首批CPU检查在第22项停止，原因是测试沿用AUX入口的旧sys.path字面断言；没有发现生产入口失败。失败记录与原测试源码已保留。只修正该断言并使用全新batch_v2目录，生产入口不变。新版32项检查全部通过，覆盖完整authorize、COUPLE分派、同全量初始state、初始指纹偏差拒绝、五个坐标消费路径、单次辅助加权及原资源/数据边界。CPU测试的native边界为明确人工facade，不声称加载真实Mamba或验证CUDA训练。

本机P3通过；准备阶段生成的静态COUPLE配置与AUX仅有H2.mode不同。请求进一步绑定已完成的AUX正式冻结审计、原始AUX request和初始指纹证据。

## 运输与授权

最终request SHA256：

```text
477522d9f7c5e7fc4e282a231f44ad5641588d5b34e303d7e433c3ba57ed6ce3
```

状态为AWAITING_EXPLICIT_USER_AUTHORIZATION。运输包含7个不覆盖安装目标；三个H2实现、原数据及既有依赖直接复用。

请上传final_pending_request_v1目录下的tar.gz、.sha256、.bytes、.contents.sha256四文件到/home/jovyan。压缩包SHA256：`6db3f93995f7356eb9ddff4b9fdbe54d5816282f54963d47edffd51291d9e20a`。

本轮没有当前服务器资源核对。request明确将旧就绪回执标为历史快照，不声称新COUPLE目标已不存在。执行授权后、写入前须重新核验当前身份/GPU/资源、上传包、全部新目标与安全父目录、原资产及315个点集哈希。数值非确定性、采样式监测和PID诊断口径限制继续披露。

没有材料化正式授权回执、runtime config、已授权launcher、attempt claim或训练目录。运输包内只有待授权launcher模板。下一步需对最终request完整SHA256单独授权不覆盖安装及唯一一次训练。
