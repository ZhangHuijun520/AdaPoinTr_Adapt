# G1_D v2 身份与启动磁盘合同修订

2026-11-17。限定implementation-only完成，唯一一批28项CPU检查、P3及运输包独立核验通过。本轮未连接服务器、部署、使用GPU或启动训练。

## 冻结变更

- hostname：`shu-common-25721452-notebook-yxwd3w-0`。
- GPU UUID：`GPU-4b19574a-832d-b4fe-e655-a57462954d6a`，CUDA_VISIBLE_DEVICES同步绑定。
- 启动磁盘余量：8.5GiB改为6GiB。依据为既有每run约470MiB产物、1GiB输出上限及额外余量。运行期间4GiB下限、8GiB RSS、20GiB Torch、22528MiB SMI、3600秒等原合同不变。
- 全新工具根、run/control/output路径使用v2，不覆盖旧尝试。bridge字节不变，entry仅增加冻结身份／迁移合同与启动容量验证，并调用6GiB检查。

模型公式、U/H、数据、D折完整批次顺序、初态、loss、AdamW与调度、3900步／100轮／31200曝光／300drop合同不变。未依据训练loss调参。禁止自动重试、resume、评价和BNCal的边界不变。

## 设备迁移的科研限制

G0_D位于原GPU，不能继续声称其与G1_D严格同设备。接受并披露此限制，保留G0_D作为跨设备参照；后续G2_D需与G1_D保持当前设备，才能支持核心G2对G1的同设备比较。型号及驱动相同不能证明数值等价，有限梯度非确定性仍存在。若核心结论依赖G0比较，再另行决定是否补同设备基线，不自动重训。

## 验证

保留原22项CPU验证，新增6项：迁移与新身份固定；6GiB边界及8983150592 bytes（此前约8.37GiB）准入；旧hostname或GPU拒绝；运行期间4GiB／输出1GiB不变；科研配置与非entry科研源码不变；缺少迁移声明或擅改阈值拒绝。完整authorize元数据路径、G1 head/母版接口、精确U/H、单向授权及no-decay验证继续覆盖。

CPU使用人工骨干/loss及auth/P3 fixture；不代表实际CUDA或科研效果通过。既有导入链和G0_D人工3900观测生命周期证据继承，未重跑GPU准入。测试stdout旧短标签不作为计数，权威记录为CPU_batch_v1/result.json的count=28。

## 待授权交付

request完整SHA256：`d0e171d7ef70bef996cb1e4b1fb7006bd7173cc0aecf9b580d130b25fb2d998e`。

运输包：`bcsp_spcg_G1_D_training_pending_20261117_v2.tar.gz`，21206 bytes，SHA256：`65a0b9e0a9295e88eb76768e7dadf58476a582c0bac6365a0823093cebeb0ebb`。共10个安装文件与1份映射。上传压缩包及.sha256、.bytes、.contents.sha256四文件到/home/jovyan/。

旧request `3a19826c48c3d4f695c35eacb7e0238aa1c9c9479772fc97dc414c89421ed5a8`保留审计用途，不用于新设备执行。v2保持AWAITING_EXPLICIT_USER_AUTHORIZATION，未材料化真实授权回执、runtime、launcher或claim。

下一次需单独授权新request完整哈希；重新核验新容器、GPU／provider／源码、D315输入与order、上传文件、6GiB容量和全新目标后，才可不覆盖安装并启动一次训练。共享磁盘余量仍可能变化，6GiB不是训练必然完成的保证。
