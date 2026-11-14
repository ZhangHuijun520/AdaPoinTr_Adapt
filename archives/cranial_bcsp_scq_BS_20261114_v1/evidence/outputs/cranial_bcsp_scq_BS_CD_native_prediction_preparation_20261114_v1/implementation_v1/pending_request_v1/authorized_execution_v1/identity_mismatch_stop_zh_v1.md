# SCQ四模型预测：身份核验停止

本次依据用户对request完整SHA256 `760191aeb674533e341d7050db58039eab6ddc7421a773bf36b05e816dea02c4` 的单独授权，尝试执行冻结范围。

第一个远端脚本在hostname／UID断言处返回失败，已停止，未重试。脚本后续资源、上传包、权重、输入核验及安装均未执行。

随后仅只读回查hostname及UID，实际返回：

```json
{"hostname":"shu-common-25721452-notebook-zbpgzu-0","uid":1000}
```

request预期hostname为 `shu-common-25721452-notebook-t6ibfm-0`。UID匹配，但hostname不匹配；因此不能把本次错误解释为模型、CUDA或数据失败。

本轮服务器写入0；安装文件0；真实授权回执／runtime／launcher材料化0；tmux启动0；forward0。本机保留首项调用的原始stdout／stderr、stop_receipt及预执行静态渲染记录。

本次本机预执行静态检查曾发现本机scope镜像索引缺项及单条控制文件传输命令过长，均在任何远端调用之前修正；冻结request、运输包、模型及入口源码未改变。27个最终远端脚本均通过静态语法与2048字节长度检查，最大1997字节。此静态通过不构成新容器执行准入。

需用户确认zbpgzu-0是否为当前目标容器。若确认，应先限定只读核验新身份、资源及冻结资产，再制定最小resource-rebind与新待授权request；不得自动改期望身份、复用旧执行授权或启动预测。
