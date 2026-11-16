# RIVE Static_C：v2不覆盖安装结果

状态：**安装及即时回读通过；没有启动训练。**

- 当前hostname：`shu-common-25721452-notebook-qx2k0r-0`，uid1000。
- GPU：`GPU-383d118a-368c-94e3-166a-cad3efab8fd7, NVIDIA GeForce RTX 4090 D, 570.190, 24564`。
- 阶段A：58个复用文件精确大小/哈希检查通过。
- 阶段B：冻结上传包、sidecar、成员、当前设备及选择器检查通过。
- 阶段C：父目录、安装根/11目标不存在和包内目标身份复核通过后，独占创建新根及11文件；逐文件回读大小/SHA与冻结映射一致，目录文件集合精确一致。
- 本v2尝试一次，A/B/C返回码均0，无本机超时；本机受控调用累计约2.969秒，不是模型性能计时。

安装根：`/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1`。共11文件、139758字节；包含代码和只读证据，没有安装额外依赖。

训练request SHA256仍为`fdcb6cacef71bfae9395baf7b3bd05506b34b4053b75bfb03f54bff6bbe82bda`，状态保持`AWAITING_EXPLICIT_USER_AUTHORIZATION`。本次授权只用于安装；没有材料化生产训练授权回执、runtime、launcher或claim，控制/结果路径在本次结束时仍不存在。没有覆盖、删除、运行测试、preflight、forward或训练。

原始阶段stdout/stderr、有效命令、独立超时标记、调用声明和completion保存在本目录。旧失败记录不变；v2成功不能证明上次超时的唯一根因。

**下一步需单独授权正式只读post-installation freeze audit，仅重新核验11目标及冻结映射；本次即时回读不代替该独立审计，也不构成训练准入。**
