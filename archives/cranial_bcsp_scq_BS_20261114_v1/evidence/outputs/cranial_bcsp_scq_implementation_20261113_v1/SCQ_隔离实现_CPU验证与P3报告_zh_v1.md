# SCQ-v2 隔离实现、人工CPU验证与P3报告

日期：2026-11-13。状态：**LOCAL_SCQ_IMPLEMENTATION_P3_PASS**。

本次完成已授权的隔离实现、一批针对性人工CPU验证及本机P3。49项检查全部通过，无失败重跑。未连接服务器、部署、使用GPU、读取真实病例/原checkpoint、实例化optimizer或启动训练；没有创建执行request。

## 1. 实现内容与不变条件

| 文件 | 内容 |
|---|---|
| `bcsp_scq_residual_v1.py` | Q0→S的原生KNN8；逐F的无affine LN、mean/max；七维相对几何；F/S两臂；1802→384→3残差头 |
| `bcsp_scq_factory_v1.py` | 原LQI完整初始化后安装SCQ；隔离母版forward；共有状态/RNG核验；新增四参数的weight decay分组 |
| `test_scq_cpu_v1.py` | 单批人工CPU验证，使用实际冻结母版forward、LQI decoder、dense head及get_loss计算方法 |
| `initialization_v1.bin`及manifest | F/S相同的固定W1/W2/bias和Pfix字节，不在GPU重新随机生成 |
| `isolated_forward_diff_v1.patch` | 原base forward只增加一次SCQ调用的精确差量 |

原科研源码、LQI/Mamba模块及历史证据字节保持不变。隔离forward仅在query选择完成后、首次mlp_query之前插入：

```python
coarse, self._scq_last_info = self.scq(coor, mem, global_feature, coarse)
```

除隔离函数命名外，移除此语句后AST与原母版forward完全一致，原先未被选入learned query的FPS调用也保留。原对象、共有模块及state key未重建或改名；B臂保持原LQI。

```mermaid
flowchart LR
  accTitle: SCQ隔离接入与验证边界
  accDescr: 实际母版在第一次query构造前插入残差，CPU已验证下游接入，真实CUDA仍待单独授权。
  A[原LQI与Q0] --> B[隔离SCQ残差]
  B --> C[Q*统一进入原decoder与dense]
  C --> D[49项人工CPU检查通过]
  D --> E[本机P3通过]
  E --> F[待授权真实CUDA准入]
```

## 2. 固定公式的落实

- 实际KNN沿用`torch_knn(8,S,Q0,chunk=256)`及topk ties口径；不换近似算法，不给索引伪造梯度。
- LN沿F最后384维，eps=1e−5，无affine；先归一化，再取八邻居mean/max。
- 七维g严格为`[mean(S−Q0), sqrt(mean(centered_d²)+1e−6), mean(norm(S−Q0))]`；使用原D-only归一化坐标。
- S消费g；F消费`LN0(fa) @ Pfix.T`，并非无空间信息对照。F/S注册相同Pfix buffer。
- 残差MLP为1802→384→3、GELU、含bias；W2/b2全零。新增可训练参数**实测693,507**，buffer不计可训练参数。
- 不加GT条件、辅助监督、投影到残骨、半径过滤或幅度上限；保持8k→8k与原coarse/dense loss。
- Q*用于原query feature、decoder位置、PE、self/cross KNN、排序、dense特征拼接、相对中心及返回coarse。Q0→S索引不复用为decoder的Q*→S索引。
- 新权重decay=5e−4、新bias decay=0；原共有参数分组策略由既有runtime提供，适配器检查其完整且无重复，不重新定义Mamba no-decay规则。

## 3. 初始化冻结

在已存在的本机PyTorch **2.5.1 CPU** 环境生成一次，未安装/升级环境。W1使用独立CPU Generator种子20261114、Linear默认Kaiming uniform与bias规则；W2/b2为0。

Pfix使用独立CPU Generator种子20261113：randn(384,7)→reduced QR→Q.T连续FP32，无额外符号修正。生成流程和每个张量的shape/字节/哈希均保存；不要求另一PyTorch版本重新QR得到相同字节。

固定二进制大小：**2,784,780 bytes**；SHA256：

`e7858ee3ae4c0bf6d68e447727c36514f5bbab42b95e1935f1686620ec089416`

生产构造在临时独立CPU随机流内建立Linear，再严格载入固定字节；安装前后共有CPU RNG保持一致，不再次对整模型执行初始化。

## 4. 单批人工CPU验证

执行环境：`E:\RelocatedData\zhj\.conda\envs\adapointr\python.exe`，PyTorch2.5.1，CPU两线程。结果：**49/49通过**，测试主体约5.81秒。完整记录：`cpu_batch_v1/result_v1.json`。

| 验证主题 | 本次实际覆盖 |
|---|---|
| 公式与数值 | 独立float64 KNN参考；独立LN/mean/max及七维g参考；F七维投影活跃且不同于g |
| 几何与批次 | 同步S/F置换；ties继承；薄双层；远Query不被过滤；B8残差路径隔离；正确中心但紧缩的反例不被假称修复 |
| 守卫 | FP64/错误shape/非有限/坏初始化哈希拒绝；模型条件不接收GT关键字 |
| 初始化 | F/S完整参数buffer一致；B/F/S共有持久状态一致；新增参数量精确；CPU RNG不被推进 |
| 初始完整输出 | 实际母版forward→实际LQI→实际FC head；B/F/S的Q256和P8192完全一致 |
| 实际接入 | 手工指定非零W2/b2后，原mlp_query只调用一次；实际PE、KNN、排序、dense拼接及相对中心均消费Q*；P也发生变化 |
| 梯度 | 初始W2可导且W1为0符合链式法则；非零W2时W1、S/F/z/Q0连续路径梯度有限且非零 |
| 原loss/训练接口 | 原训练四元组、无denoise空张量；原get_loss对coarse和dense各调用一次；原完整8192点torch.cdist loss反传到Q*及新增四参数 |
| 状态 | eval共有状态及CPU RNG不变；backward后新增参数字节不变；train产生的临时BN buffer已恢复 |
| 兼容性 | 无注册的禁止attention模块；拒绝重复安装/重复optimizer分区；隔离forward只有一次AST插入 |

本次人工目标下原始完整loss数值为 **0.63383895**，只证明此人工输入下计算及梯度可运行，**不是任何真实病例补全分数**。未执行optimizer step。

## 5. 本机P3结论及证据限度

P3重新核验源码/静态审查/初始化/CPU结果哈希，确认原绑定文件未变化、唯一差量位置正确、49项结果完整且没有失败回执。结论为**限定实现及人工CPU合同通过**，不是完整N2或训练准入。

明确局限：

1. CPU使用冻结母版的真实计算方法，但构造器/取点器为人工fixture，Mamba为人工因果mixer；未使用真实PointNet2/CUDA/Mamba内核。
2. 人工完整模型参数量18,992,995受替身结构影响，不能作为真实Mamba模型参数量；只把新增693,507报告为已实测。
3. B8只验证残差模块的批次隔离；完整batch8 train、真实GPU显存/速度/资源尚未验证。
4. 测试了联合coarse+dense loss反传，没有分别量化两项loss对头梯度的贡献。
5. 新参数分组使用人工共有分区检查接口；生产入口仍须传入并绑定现有共有分组，不能照抄测试中的人工分区进行训练。
6. CPU通过不代表科学效果、Native全骨块覆盖或contact rim改善；没有消除错位Q0读取远邻的已知局限。

## 6. 下一步最小范围

下一步建议仅准备**人工CUDA短入口与待授权request**，绑定新增两模块及初始化材料，复用已存在运行环境和provider，不发展通用审计框架。

保持既定工作量：B batch1、F batch1、S batch1、S batch8 train各一次原完整forward/loss/backward，即 **4 forward／4 backward／0 optimizer step**。记录实际native Mamba/PointNet2身份、原loss与活跃梯度、峰值显存/资源及状态/RNG恢复证据。不得额外增加临时试跑。

短入口和request尚未创建，部署与GPU执行尚未授权。完成独立执行授权、实际CUDA准入及正式冻结后，才准备首对训练request；不跳过或混同这些边界，也不重复旧整套FullMamba preflight。

## 7. 交付材料

- `P3_implementation_v1.json`：限定本机P3，包含实现、结果、初始化及原证据哈希。
- `static_review_v1.json`：执行前编译/AST及原文件身份核对。
- `cpu_batch_v1/result_v1.json`：唯一一次49项人工CPU检查的逐项结果与局限。
- `delivery_manifest_v1.json`：最终交付清单。
- `local_tools/prepare_scq_initialization_v1.py`：固定初始化生成来源。
- `local_tools/freeze_scq_implementation_P3_v1.py`：本机只读P3汇总来源。

本轮材料位于本机项目输出目录，未部署、打包运输、推送GitHub或删除服务器文件。
