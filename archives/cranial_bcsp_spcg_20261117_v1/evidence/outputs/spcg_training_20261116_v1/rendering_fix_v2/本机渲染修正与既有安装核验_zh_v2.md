# 本机材料化命令渲染修正与既有安装核验

2026-11-16。本轮仅修订本机调用；生产entry／bridge、运输包、冻结request、模型及资源阈值未修改。

修正：授权／runtime JSON序列化的末尾换行使用chr(10)，避免外层三引号把转义展开为远端Python字符串中的字面换行。四段实际渲染后的远端脚本均完成compile静态检查；新版启动driver删除安装分支，只重验既有资产／资源和已安装哈希，随后等待单独授权才执行材料化／单次启动。

只读回查：9个已安装文件的精确集合、大小及SHA均匹配，control目录不存在，输出目录不存在，固定tmux不存在。没有授权回执、runtime、launcher或claim，单次正式训练尚未消耗。

request完整SHA256保持：

`0f5a8aca25b1acd43c3bd258ae8ddf7ea3d06f81d020f2c38bde1ea7a944ef08`

本轮未重新安装、材料化或启动训练。下一步须单独授权沿用此request执行一次新启动尝试；启动前再次重验315输入／order、复用资产、当前GPU、资源和control／输出不存在。失败停止、不自动重试；无需上传、重做CPU测试或GPU准入。

证据：static_review_v2.json、四份rendered_static.py及existing_installation_readback_v2.json。新调用为上级目录start_existing_installation_attempt_v2.py，尚未执行。
