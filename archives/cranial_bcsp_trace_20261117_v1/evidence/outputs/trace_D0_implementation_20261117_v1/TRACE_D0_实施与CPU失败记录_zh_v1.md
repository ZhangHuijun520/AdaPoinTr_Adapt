# TRACE D0：限定实施与单批CPU失败记录

日期：2026-11-17。状态：**隔离实现和静态审查完成；CPU批次失败；P3未通过；未创建最终execution request。**

## 本轮实施

只新增四个隔离源码文件，没有修改既有生产源码：

| 文件 | 作用 |
|---|---|
| bcsp_trace_D0_observer_v1.py | 复用head capture，捕获真实H输入，对G2原生排序分数做原样返回的实例级观察包装 |
| bcsp_trace_D0_entry_v1.py | 授权和精确绑定、四模型各20例的80次forward上限、状态/RNG核验及失败落盘 |
| bcsp_trace_D0_analysis_v1.py | 后续单独授权的本机CPU重放与空间分析；不由GPU入口自动调用 |
| test_bcsp_trace_D0_CPU_v1.py | 一批30项人工CPU合同检查，保留fixture及失败材料 |

静态语法检查通过，CPU测试前已冻结四文件哈希和单批范围。没有部署、服务器操作、GPU调用或真实权重/NPZ数组读取。

## 实际测试结果

使用既有本机PyTorch CPU环境执行唯一一次批次。前4项通过：惰性导入、完整授权／单向runtime、范围漂移拒绝、循环绑定及未授权回执拒绝。

在第5项“实际母版FC及G1/G2观察等价性”开始构建人工模型时停止。失败位置为既有`bcsp_spcg_factory_v1.py::replacement_forward`的`Path(source).read_bytes()`。收到的仍是服务器路径：

`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/AdaPoinTr.py`

本机没有该路径，因此报FileNotFoundError。4/30表示4项通过、随后一项失败，其余未运行；不能写成29项或全部30项验证通过。

## 原因与边界

这是本轮测试fixture遗漏了配置副本的路径映射。测试中的`mapped()`只覆盖`exact()`读取；实际factory直接读取传入的`mother_source.path`，不经过该函数。虽然本机母版字节已经核对，构建调用仍传入原服务器记录。

此前已有Native CPU测试通过以下办法处理同一接口：创建独立`buildq`，将`mother_source`替换为本机已核验文件的record，并显式断言大小和SHA256与原绑定一致。本轮没有沿用这一步，是可明确定位的测试适配遗漏。

失败发生在首次模型forward之前。尚不能判断新观察器等价性、完整80次循环、读取守卫加载链或CUDA执行是否通过；更不能判断TRACE科研假设。

四个新增实现文件自测试前冻结后保持不变；原head、SPCG factory、LQI decoder和母版源码哈希仍与冻结记录匹配。未自动修复、未再次测试。失败材料原样保留，此记录不代替未来单独的正式post-test冻结审计。

`CPU_batch_v1/`内的ARTIFICIAL_request、ARTIFICIAL_authorization、ARTIFICIAL_runtime和ARTIFICIAL_P3均为本机测试fixture，不是生产授权或P3证据，禁止运输并执行。

## P3与request结论

P3状态为`TRACE_D0_P3_NOT_PASSED_CPU_FAILED`。CPU尚未验证完成，不能创建绑定“已通过实现”的最终request。当前只有标记为不可执行的draft配置，不是最终execution request；没有材料化生产授权回执、runtime、launcher或单次启动claim。

## 下一步最小修订建议

仅修正测试构建配置副本中的母版路径映射，并断言本机文件大小和SHA256仍与原记录相同；观察器、生产入口、CPU分析实现及既有生产守卫保持不变。新增版本化测试／范围和全新保留目录后，单独执行一批新版人工CPU验证。通过后再完成P3并创建待授权80次forward request。

不需要修改服务器路径、模型公式、checkpoint、provider、数值阈值或重做GPU preflight。
