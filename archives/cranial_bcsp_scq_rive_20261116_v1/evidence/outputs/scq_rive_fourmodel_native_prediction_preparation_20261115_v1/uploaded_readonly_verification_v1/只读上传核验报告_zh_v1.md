# RIVE四模型预测只读上传核验报告 v1

结论：通过。9项汇总检查全部通过。当前容器qx2k0r-0、UID1000；两次只读远端调用均退出0，无本机超时。

四个上传文件大小和SHA256与本机冻结值完全匹配。压缩包83164字节，SHA256 `ae7f8633365a8cd483590f1c6dc5087e6afa0887554db31028f6e2d1ef5036ef`。

归档16个唯一安全常规成员：映射元数据＋15份payload。所有成员大小、哈希及contents校验文件一致。映射仅允许新目录和15目标xb不覆盖写入，55个复用文件不复制。entry、index、protocol、numeric及P3绑定一致，P3检查通过。

request完整SHA256 `ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774`；仍为AWAITING_EXPLICIT_USER_AUTHORIZATION，execution_authorized=false，固定420次forward，loss/backward/optimizer/BNCal/warmup/TTA均为0。

只在内存读取归档；服务器写入、解压安装、测试、预测及训练均为0，未创建授权回执、runtime、launcher或claim。未在此次范围重验55个复用资产或新目标不存在性。

下一步可单独授权按冻结映射不覆盖安装15个文件及1个新安装目录；写入前重验身份、上传包、55个复用文件、父目录及全部新目标不存在，异常即停。不自动安装或预测。
