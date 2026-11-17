# SPCG G1_D v2 正式训练后冻结审计及G0_D合同核验

日期：2026-11-17。结论：`FORMAL_SPCG_G1_D_POST_TRAINING_FREEZE_PASS`，机器可读结果中全部检查通过。

## 范围与绑定

当前容器yxwd3w-0。request SHA256：`d0e171d7ef70bef996cb1e4b1fb7006bd7173cc0aecf9b580d130b25fb2d998e`。

本次服务器操作全部只读，在本机保存证据。checkpoint仅流式读取字节，不反序列化；服务器写入、模型调用及GPU执行为零，未训练、评价或BNCal。

## 完成与产物

退出码0，worker和固定tmux均退出。forward/backward/clip/optimizer step各3900次，100轮遍历，31200次曝光、300次drop。完整metrics及SPCG日志各3900条，资源日志3902条。耗时1513.537秒，约25分14秒；BNCal、evaluation、resume均为false。

checkpoint路径：

`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G1_foldD_seed0_train_20261117_v2/ckpt-last.pth`

实测大小478923818 bytes；本次重算SHA256：

`beac40e64a15eba8be8c6c583eca1d2171ccf293d96ba1dbc9dd51c9811dd275`

与completion及manifest一致。全部产物文件集合、大小和哈希、manifest唯一性、空tmp目录、10个安装文件及复用implementation哈希均通过。授权回执、runtime单向绑定、唯一启动claim符合冻结request。

## 初始化与配对合同

共同scratch母版raw-state指纹为 `366e5a6c752270708d30a2459933812d92accb8bb24f84adb29a2c6a15053f46`。G1替换head后的完整初态指纹为 `3cfdbac9149b99e24ea6641fb9e00cf975754ad21c7a88fc6d34e17e01724ab9`，与request及CUDA准入对应G1记录一致。共同母版相同不意味着G0/G1完整模型指纹应相同。未用已训练G0_D权重初始化G1。

初始化身份依据冻结构建源码、运行时断言和准入记录；本次未重建模型或从checkpoint读取张量。不同state指纹算法分别按其对应证据核验。

重新核验G0_D正式冻结凭据，其metrics、初始化、order和exposure证据哈希未改变。两组全3900步的step、epoch、batch、case_ids、source_ids、LR、BN momentum和clip阈值逐条一致；order原始字节及完整exposure字典相同。

D折order原始SHA256：`4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720`。初始化、completion、exposure中的canonical order指纹相同。每轮39个batch、每batch8病例，100轮共31200次曝光及300drop，可由冻结计划重建。

数据根、static config、science、counts和运行资源阈值保持相同。U、H、母版源码和G0_D冻结凭据均重新核验大小及SHA256。

## 数值、几何与资源

3900条SPCG记录与训练顺序逐步对应，坐标口径为D-only normalized，coarse/dense中心与半径及coarse_CD/dense_CD均无非有限数值。loss按实际FP32加法舍入核验，LR与BN调度一致。指定step 1、39、390、1950、3900的总loss Q梯度记录完整，L2有限且大于0；不能将其单独解释为coarse loss贡献。

3902条资源记录守卫均通过。峰值RSS 1660686336 bytes，Torch allocated 13929265664 bytes、reserved 14805893120 bytes，SMI显存14608 MiB。PID口径差异按既有诊断性合同披露，不声称获得GPU进程所有权保证。

## 设备迁移与容量限制

| 运行 | GPU UUID |
| --- | --- |
| G0_D | GPU-c25d6be2-173c-031a-89c6-b96e0f5f8190 |
| G1_D v2 | GPU-4b19574a-832d-b4fe-e655-a57462954d6a |

hostname及GPU UUID变化符合已接受的迁移合同，CUDA_VISIBLE_DEVICES与新GPU同步，其他环境字段不变。启动容量为6GiB，运行期间4GiB下限和1GiB输出上限保持原值。

**共同训练合同核验通过，不等于严格同设备配对。** G0_D相关性能差异存在设备数值因素，不能全部归因为结构。G1_D/G2_D应维持新设备的配对块，作为局部与全局聚合的核心比较。原有限梯度非确定性继续披露，本次没有因审计通过撤销限制。

## 证据与后续

同目录保存正式结果JSON、五阶段远端只读脚本、原始stdout/stderr、结构化结果及本机哈希清单。

下一步按矩阵准备G2_D，绑定本次G1_D冻结证据及相同新设备、D折顺序、U/H与3900步合同，不根据本次训练loss调参。本次未创建或执行后续request，尚不能判断补全效果改善。
