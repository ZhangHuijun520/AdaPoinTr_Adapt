# SPCG六模型Native预测入口：fixture修订、CPU验证、P3及待授权交付

2026-11-17。限定fixture修订完成，新版唯一一批24项CPU检查通过。P3与最终request、运输包独立核验通过。本轮未连接服务器、部署、加载真实权重或运行GPU。

## 修订边界

仅在人工build fixture的q副本中，将mother_source换为大小及SHA256相同的本机精确record；保存到新CPU_batch_v2，不复用失败批次。生产入口SHA256仍为 `223777e0dd409b58b04ab6fbcf53b71e76418fd9ff77b48a0a6e421517eaeb07`，与首次失败冻结记录一致；模型及科研源码未修改。

首批CPU在第8项因Windows读取服务器源码路径失败，证据保留。本次未放宽生产文件守卫或改变服务器源码路径；测试替身解决本机路径映射问题。

## 实现与验证

SPCG入口使用G0原coarse head、G1全局聚合head和G2局部k8 head，经冻结factory构建后按最终epoch99/update3900严格加载checkpoint。正式执行限定六模型各105例、总630次Native forward；batch1、eval/inference_mode、FP32及既有TF32/确定性合同。零loss/backward/optimizer/BNCal/warmup/TTA；失败即停，无自动重试。

本次权威计数为24项检查（CPU_batch_v2/result.json）。覆盖六模型冻结证据、630病例索引与210输入分折、原始manifest坐标绑定、错误索引拒绝、显式授权链、错误身份/预算拒绝、实际G0/G1/G2 factory与母版接口、人工checkpoint严格加载、k8路径、状态/RNG、计数、归档、精确源码与U/H读取守卫、POSIX launcher和UTC/异常收尾。

成功路径运行630次人工Native循环并生成630份人工预测；另有模型构建接口检查及故意失败/状态突变/RNG突变负例。负例不属于正式630次预测预算，也没有运行真实模型。骨干和loss为人工替身；真实Mamba/CUDA、checkpoint及NPZ均未访问。人工auth/runtime不构成执行权限。

P3状态LOCAL_SPCG_NATIVE_PREDICTION_P3_PASS，记录通过结果、源码冻结、首次失败及fixture修订，保留真实服务器就绪未核验限制。原有有限梯度非确定性和G0_D跨训练设备限制不变。

## 最终冻结范围

六个最终权重及训练request/正式冻结凭据逐一绑定。C/D每折21开发来源105病例，每模型仅其对应折；630条索引共210份唯一输入。逐病例路径使用既有已核验映射：C开发输入在foldd点集目录，D开发输入在foldc目录，不能按折名猜目录。当前存在性/大小/哈希仍须执行前重新核验。

每份输出仅prediction[8192,3]、coarse[256,3]，保留D-only center/scale于manifest供后续统一CPU评分；不在推理中读取GT、做Oracle配准或后处理。无RF数组、context cache或完整decoder trace。

资源合同7200秒、8GiB RSS、20GiB Torch峰值、22528MiB SMI、1GiB输出，启动6GiB、运行期间4GiB。串行加载六模型，逐模型核验参数/BN状态及RNG前后相等。统一推理设备不能消除历史训练设备差异，G0_D仍为跨设备参照。

## 交付

最终request完整SHA256：`c63ebdfc7e4315e36bb0c65b445925d5496352720fd78db80ff7ed0e5b155dcc`。

运输包：`bcsp_spcg_sixmodel_native_pending_20261117_v1.tar.gz`，81869 bytes，SHA256：`90182af9e43ee2053831f6bc9d52dcf8bf5bc978ac7b4231fc01e26a86fed5a4`。16个拟安装文件及1份映射，不含checkpoint、点集或人工测试大文件。

上传压缩包及.sha256、.bytes、.contents.sha256四文件到/home/jovyan/，再单独授权上述request完整哈希。状态AWAITING_EXPLICIT_USER_AUTHORIZATION；真实授权回执、runtime、launcher和claim均未材料化。

执行前需重新核验当前身份/GPU、6GiB余量、provider/源码/依赖、六checkpoint哈希、210输入哈希及元数据、全部新目标和父目录；满足后才可不覆盖安装及单次启动。无需重复GPU准入。预测完成后须正式只读冻结审计，再下载核验和统一CPU评分；本次没有预测或效果结论。
