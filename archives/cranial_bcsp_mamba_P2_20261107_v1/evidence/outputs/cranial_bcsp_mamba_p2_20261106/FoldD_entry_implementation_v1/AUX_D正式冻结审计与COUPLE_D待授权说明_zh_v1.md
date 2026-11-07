# AUX_D 正式训练后冻结审计与COUPLE_D待授权准备

日期：2026-11-07。AUX_D审计结论PASS，25项检查全部通过。

退出码0，worker和tmux退出。精确3900次forward/backward/clip/optimizer step，100次遍历、31200曝光、300次丢弃。完整3900条实际case/source批次、LR和BN日程逐条匹配原Fold D顺序；order原始/规范哈希、exposure及初始化记录相互一致。H2始终AUX，scale全部1、raw/used coarse矩相同；动态log半径目标、SmoothL1和单次0.1加权全部核对。原M0共有初始化factory证据一致，范围头全零初始化及首批delta0通过；原优化器分组保持不变，仅增加1025参数头。

checkpoint为407239343字节，实测SHA256：

```text
0e8afe3ba44e8b35105d7e4f45677517442fbcc54b48b7ada899075ee6e1162f
```

15个精确产物文件和74个冻结资产重新核验；payload manifest集合、大小和哈希一致，审计前后inode/权限/大小/mtime稳定，排除atime。3902条资源记录满足原阈值；设备显存峰值14210 MiB。BNCal、评价、resume均false。本次未写服务器、加载权重或运行模型。

限制：不重建初始张量、不反序列化checkpoint；依靠记录指纹、已绑定factory和零初始化断言。PID仅诊断、采样监测不是硬隔离；有限Mamba梯度非确定性继续披露。训练审计不证明形状或接口效果改善。

## COUPLE_D request

通过后已创建待授权request，复用同一Fold D入口、三个H2模块、P3、数据和provider，不新增模型代码或重复测试/GPU preflight。仅H2.mode改为COUPLE；保持原D完整批次顺序、初始共有状态、1025全零头、8k→8k、3900步、100遍历及原资源阈值。实际启动分派会比较全量初始参数和持久state指纹与AUX_D一致，禁止使用AUX最终checkpoint初始化。

完整request SHA256：

```text
be3988719fce8860729c80daaa1dcd634000b50c5378605fb6fe377c511e6718
```

状态AWAITING_EXPLICIT_USER_AUTHORIZATION。运输包包含4个不覆盖安装目标：COUPLE静态配置、AUX_D正式审计、无授权值的launcher模板和request。采用全新COUPLE_D安装根、control、run和tmux路径；旧AUX_D及初始化文件精确引用。COUPLE_D_pending_request_v1目录中的tar.gz及.sha256、.bytes、.contents.sha256四文件应上传到/home/jovyan。

压缩包SHA256：`e4a7eca9f8b81fa91430e70c04c81e640f88d6b1fb38802cd43813aef7328c21`，大小9972字节。上传后需对完整request哈希单独授权不覆盖安装及唯一一次训练。执行前重新核验资源、所有新目标不存在和复用资产。不自动重试/resume、评价、BNCal或调参。

没有部署COUPLE_D，没有材料化正式授权回执/runtime/launcher/claim，也没有启动训练。
