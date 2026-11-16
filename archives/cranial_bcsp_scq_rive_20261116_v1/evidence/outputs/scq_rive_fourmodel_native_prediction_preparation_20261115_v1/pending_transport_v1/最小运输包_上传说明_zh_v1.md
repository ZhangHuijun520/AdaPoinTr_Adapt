# RIVE四模型Native预测最小运输包上传说明 v1

必要服务器只读就绪核对已通过；随后仅在本机冻结本运输包。未安装、测试、重复GPU准入或运行预测。

## 上传位置

本机目录：`E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution\outputs\scq_rive_fourmodel_native_prediction_preparation_20261115_v1\pending_transport_v1\upload`。

将以下四个文件保持原名上传到 `/home/jovyan/`：

- `bcsp_rive_fourmodel_native_pending_20261115_v1.tar.gz`：83164字节；SHA256 `ae7f8633365a8cd483590f1c6dc5087e6afa0887554db31028f6e2d1ef5036ef`。
- `bcsp_rive_fourmodel_native_pending_20261115_v1.tar.gz.bytes`：6字节；SHA256 `699eb981f54a3063c5dce106763a90c60252c74c400496878e2e08f2f9e6243d`。
- `bcsp_rive_fourmodel_native_pending_20261115_v1.tar.gz.contents.sha256`：1731字节；SHA256 `de1b0a199b9523cd5d7df7214bf978870034e3e7ca5e77726b0f9b9ae6858728`。
- `bcsp_rive_fourmodel_native_pending_20261115_v1.tar.gz.sha256`：120字节；SHA256 `525a7ba37a51fcecff22d31cf5c63b67c598b6a0ca638242d78e60a9c8bc6709`。

## 冻结安装范围

归档16个常规成员：1个映射元数据（不安装）＋15个固定目标，内容为隔离入口、测试及CPU/P3证据、index、protocol、numeric policy、四份正式训练审计和待授权request。仅允许未来新建目录 `/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1` 并xb写入这15个文件。55个现有必要资产、210份真实点集和四个checkpoint均不重复运输或复制。

所有目标与新安装根均在只读核对时不存在；后续安装仍必须重新核验，不能把本次快照当作永久保证。父目录必须已有且无链接；异常即停，不覆盖、不回滚删除、不自动重试。训练输出、权重和控制目录全部保留。

request完整SHA256 `ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774` 不变；仍为AWAITING_EXPLICIT_USER_AUTHORIZATION。映射SHA256 `c67690dc37f1b3d77a0822ac3069cb508cdca1b7c4bac536702a9aadbe383dd5`。

本机14项包内容／映射核对通过。当前空间快照6981419008字节；正式执行前重验输出1GiB＋最低4GiB余量、210输入和四个checkpoint哈希。

## 下一步

上传后单独授权只读上传核验，不自动安装或预测。通过后再按冻结映射单独授权不覆盖安装和正式安装后冻结审计；最终还需对完整request哈希单独授权唯一一次420次Native预测。禁止训练、BNCal、loss/backward、额外forward、自动重试或resume。
