# BCSP限定适配候选v1：实现与CPU验证状态

_2026-10-24 · implementation-only · 未部署／未读真实数据／未运行模型_

## 📋 实际交付

- `bcsp_adapter.py`：PyTorch query分块全key KNN、NumPy参考实现、normalized BCSP数据读取接口、独立3900更新守卫及epoch调用钩子。
- `test_bcsp_adapter.py`：固定一次人工CPU契约测试，临时文件均为合成数组，不是新真实数据集。
- `bcsp_fork_knn.patch`：仅供未来独立BCSP候选fork接入的最小KNN替换补丁，尚未应用。不得应用到归档父版、旧v1.1／QA生产路径。
- `cpu_tests_v1/result.json`与`stdout.txt`：保留本次唯一测试结果，不覆盖已有实验。

## 📊 验证结果

静态AST解析通过。31项测试中30项通过，1项因本机Python缺少PyTorch而跳过，失败／错误均为0；退出码0，测试耗时约0.215秒。测试成功状态明确为 `PASS_AVAILABLE_CPU_CONTRACTS_TORCH_UNVERIFIED`，不是完整P3。

通过项目覆盖：随机分块／边界chunk、self-neighbor、重复／等距、空query、非法k／shape／dtype／nonfinite；legacy scope退出恢复；人工数据来源／路径／哈希／frame／点数检查；GT替换不改变推理输入；3900次人工optimizer回调、100遍／31200次case曝光计数；越界／缺批／待提交／提前结束／异常后禁止续跑。

人工optimizer只是计数对象，不是PyTorch optimizer，没有模型forward、backward或参数更新。本轮模型调用、GPU、真实数据读取、服务器操作、生产文件修改和训练request均为0。

## ⚙️ 接口合同

KNN保留全key和父版平方距离公式，默认query块256；PyTorch返回topk(sorted=False)，不强制改变并列点索引。NumPy参考按稳定索引处理并列，不能以其运行代替PyTorch／CUDA结果认证。理论128MiB仅指B8、N16384的一个FP32距离块，不是总显存实测。

数据接口使用manifest record的source_id、point_path、sha256、schema=`BCSP-normalized-v1`、normalization_source=`defective_bbox`，读取float32 `partial[N,3]`和训练时的`implant[8192,3]`。推理不读取implant数组；schema元数据只是声明，不能替代真实几何／归一化QC。本轮接口不负责生成或转换真实NPZ。原研究包的xyz/provenance格式不可直接混入。

独立stage=`BCSP_INPUT_DENSITY_V1`，固定315case、batch8、drop_last、100遍标签0–99，39batch/遍、3900次step。before_step预检，optimizer.step返回后after_step提交；异常锁定失败，不做resume。如果optimizer本身先修改再抛异常，守卫不能回滚参数，只能禁止继续。

run_epoch调用compute_gradients和optimizer.step；回调须只计算梯度／clip而不能自行step。此接口尚未接入真实runner，不能防御任意不可信回调伪造更新次数。候选接口不是执行授权入口，不可把能调用函数解释为已获训练授权。

## ⚠️ 未闭合项

1. **真实PyTorch CPU KNN未运行**：当前可访问Python环境无torch；没有安装、解包其他运行时、调用WSL或切换服务器。本次1项跳过必须保留，不能写全部31项通过。
2. **补丁未应用、实际runner／Dataset registry未接入**：候选提供核心API和epoch钩子，不是已验证的端到端训练入口。新stage分派、source/fold配置装载、数值设置、scheduler、clip、checkpoint与最终收据仍须在限定候选集成中接入。旧生产路径保持原样。
3. **ContextVar不是DataParallel线程传播保证**：scope/dispatch只是单上下文辅助接口，不作为多线程模型的接入依据；拟议fork补丁直接调用torch_knn，避免把ContextVar未传播导致回退误认成新KNN已使用。未测试DataParallel。
4. 真数据全量QC、新manifest/共同target、CUDA等价与资源验证未完成；不部署、不建立execution request。

## 🎯 当前判定和下一步

状态：**核心候选已实现；可用人工CPU合同通过；PyTorch后端与端到端集成未验证**。不能宣称用户要求的全部适配已闭合，不能自动进入GPU。

下一步只需解决上述两个直接缺口：在明确授权的已有PyTorch CPU环境验证真实tensor路径，并在隔离候选中完成最小runner／数据注册接入及人工调用链验证；不扩张库存框架，不重跑真实几何。新增依赖安装或使用其他执行环境需要另行明确授权。

科学文档技能用于保留跳过项、接入限制和未执行范围；本报告不把参考实现测试包装为实际PyTorch／CUDA验证。
