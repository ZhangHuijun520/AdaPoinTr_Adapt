# RIVE Static_C唯一一次训练启动凭据

状态：**已启动，确认实际更新，最近观察仍在运行。**

## 执行范围与新鲜核验

request SHA256：`fdcb6cacef71bfae9395baf7b3bd05506b34b4053b75bfb03f54bff6bbe82bda`。用户已明确授权该完整哈希。

当前qx2k0r-0，RTX4090D，UUID GPU-383d118a-368c-94e3-166a-cad3efab8fd7，driver570.190。启动前显存占用1MiB、可用空间9111076864字节；58复用文件+11安装文件精确哈希通过。Fold C315训练文件流式哈希全部通过，63来源、49440750字节，无开发payload访问。

依次创建授权回执→计算SHA→创建单向runtime→生成原始字节单次launcher。每个控制文件独占写入及回读哈希通过。为满足短命令限制，本机在任何远端控制写入前调整了控制字节的调用封装；未改变launcher原始字节、request或生产源码，未提交失败的远端材料化调用。

已安装入口的完整纯文本authorize路径通过，模型调用0；随后再核对资源、控制哈希、无会话/claim及输出不存在，创建唯一claim并提交一次tmux。没有重试或resume。

## 实际运行证据

- session：`SCQ_RIVE_Static_foldC_seed0_train_20261115_v1`。
- worker PID：`27290`。
- 启动确认时60条已提交指标；后续资源快照已提交215/3900步。两次为不同时间快照，不要求行数同步。
- 完整参数/持久状态初始指纹匹配冻结值；C折canonical order SHA为`349189dcada4c41b9e6b0152fa24695b2c71ce5fce4144865247d03c445f795f`。
- 实际模型RF-Static、40827847参数，RF增量231171，共同初态保持；run_identity明确stage RIVE/fold C/mode A。
- 实际生效3600秒预算；旧86400秒仅是历史配置身份。最近资源检查全部通过，未发现failure/startup_failure记录。

SMI PID与容器PID不一致按既定DIAGNOSTIC_ONLY口径记录，不作归属硬保证，不新增PID框架或更改守卫。

## 服务器路径

结果目录：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Static_foldC_seed0_train_20261115_v1`

日志：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Static_foldC_seed0_train_20261115_v1/launch.log`

退出码：`/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Static_foldC_seed0_train_20261115_v1/exit_code.txt`

训练固定8k→8k、batch8、100 traversals、3900 updates、31200曝光/300drop；未进入评价、BNCal或其他臂。本轮只确认启动和实际更新，未判断训练完成、测量最终checkpoint哈希或完成正式训练后冻结审计，也未获得补全效果结论。后续训练完成仍需单独正式只读冻结审计。
