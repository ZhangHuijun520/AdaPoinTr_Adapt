# RIVE两臂统一CPU评分入口实施、人工验证与P3 v1

结论：隔离实现完成，46项人工CPU契约检查及36项本机P3核对全部通过。最终request已创建，状态AWAITING_EXPLICIT_USER_AUTHORIZATION，execution_authorized=false。

## 科学合同

RF-Static／RF-Requery、C／D两折，每模型105份预测，420行模型＋420行共享控制，共840病例评分行、168来源行；每来源5缺损等权，再按每折21来源等权。C、D分别报告，之后来源等权描述汇总；主比较Requery减Static，不筛病例或调参。两折同设备配对，保留有限Mamba梯度非确定性及单seed限制，不改写旧RF跨设备限制。

主指标A1面积加权E_P95毫米；J_P95、E/J覆盖、CD-L1、反向离群、位置和尺度及coarse/dense诊断沿用既有定义。13个指标／风险／来源汇总／数组读取函数AST逐项未变，metric源码哈希保持 `af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766`。共享控制必须逐行等于旧冻结控制，否则整批停止。无配准、Oracle、过滤、bootstrap、p值或正式gate。

## 实现差量

新增隔离两臂评分入口，仅改authorize、index/archive验证、run_scoring及main五个函数与对应常量。绑定本轮四个RIVE checkpoint／训练request／正式审计身份，420预测、426归档成员和49967684字节已核验展开上限；不修改旧RF评分器或指标实现。

## 唯一一次人工CPU验证

本机既有PyTorch CPU环境，退出0、无stderr、无超时。46项检查覆盖完整授权、错误行数／配对／资格拒绝、九数组与阶段方程、真实归档格式的人工426成员读取、状态/RNG异常拒绝、哈希错误、phantom指标方向、来源等权、严重病例新增／挽回分开计数、首次失败即停及共享控制漂移停止。

8行实际指标计算使用解析体素phantom及人工8192点张量；840行完整编排使用人工模板，非840次真实指标计算。未读取真实预测／参考数组，真实评分0行，服务器及GPU调用0。人工fixture和日志完整保留。

P3完成36项核对：实现／测试／metric哈希、版本及Python绑定、真实档案只读字节指纹、人工结果／失败保留、前台托管合同和真实输出／授权路径未创建等均通过。未将CPU通过视为真实评分已完成。

## 最终待授权request

文件：`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\scq_rive_score_implementation_20261116_v1\local_scoring_execution_request_v1.json`。

大小：11507字节。

完整SHA256：`fb84bccd3ebcbaa5346ff8897d8e05cf9c10586c99411040bd01dae51856b9e7`。

资源合同保持18000秒、两线程、RSS8GiB、输出2GiB。真实评分前须重新散列评分器、metric、CPU/P3证据、归档＋3校验文件、冻结控制、210参考及210点集；失败即停、不自动重试或resume。运行采用保留工具会话的前台托管子进程，不使用脱离会话的后台启动。

前台调用器已静态绑定上述request完整哈希，尚未执行。没有创建真实授权回执／attempt claim、真实输出目录，也未启动评分。

下一步对上述完整哈希单独明确授权后，才可进行一次本机CPU评分；完成后需正式只读评分后冻结审计，通过再解读RIVE科研结果。
