# F0首对训练准备 v1

正式post-CUDA审计v2通过；只准备既定F0的C/D两折，先C后D，各3900更新、8k输入/8k输出、固定BCSP V1及原CD，不新增T0/M0重训。详细合同见F0_pair_training_preparation_contract_v1.json。

现有P1短入口限制T0/M0及旧schema；F0已有模型工厂和未改生命周期bridge，但没有可执行的专用训练授权入口。下一步只需限定新增F0训练短入口＋针对性人工CPU验证＋P3，然后绑定最新准入回执SHA、真实训练QC/顺序及当前资源，创建首个Fold C待授权request。不要把PASS字符串当可信回执，不重复已通过GPU preflight，不扩展通用工具。

本次未实施该短入口、读取训练payload、创建训练request、材料化训练内容或启动训练。真实数据与当前设备训练准入尚需相应有限核对；GPU人工通过不能承诺3900步效果或稳定性。
