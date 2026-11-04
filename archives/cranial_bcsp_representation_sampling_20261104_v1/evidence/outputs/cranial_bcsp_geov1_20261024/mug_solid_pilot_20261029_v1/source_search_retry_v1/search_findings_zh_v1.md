# MUG500+ 固定三来源完整骨分割重新检索

日期：2026-10-29。固定来源：A0136、A0137、A0138。本次仅检索公开资料、获取官方版本元数据并保存记录；未生成 mask、改变病例、构造缺损或运行模型。

## 结论

重新连接后，官方 Figshare 主页面与本机 HTTPS API 查询均已成功。官方当前版本为 v20，文件清单 98 项。读取全部 v1–v20 的官方元数据后，仍未找到固定三来源的另一份完整骨分割或修正版下载。

此前“v13 尚未核实”的缺口已补齐：v13 的 63 项文件清单没有覆盖 A0136–A0138 的编号压缩包。不能将 v13 视为包含这三例旧版替换数据的来源。此判断基于文件清单，不宣称逐个解压所有不相关压缩包。

## 官方版本对照

v1–v16 的文件清单没有覆盖固定三编号的编号范围压缩包。v17、v18、v19、v20 均提供同一文件：

- 名称：`A0136-A0140.zip`
- file ID：`32386331`
- bytes：`2113114570`
- computed MD5：`93b5498c885765bc222e507aa60af6f4`
- 下载地址：https://ndownloader.figshare.com/files/32386331

上述身份与此前已读取并核验的本机官方 v20 压缩包一致。没有必要为相同归档重复下载约 2.11 GB。各版原始元数据及提取摘要保存在本目录 `v1.json` 至 `v20.json`、`current.json`、`versions.json`、`version_comparison.json`。

官方接口：https://api.figshare.com/v2/articles/9616319 。各版接口为其后追加 `/versions/<版本号>`。主页面：https://figshare.com/articles/dataset/MUG500_Repository/9616319 。本轮 web 抓取与本机 API 的可访问性存在差异；web 抓取 API 失败不能代表本机 API 也失败。

## 病例数据适用性

此前实际读取的固定三 NRRD 为多灰度值图像，不能直接当作二值骨 mask；FOV 与完整 STL 不一致。A0137 仅两层，A0138 的既定切除中心不在该 NRRD 物理覆盖内。详细测量沿用已有 source-admission 与 coordinate-evidence 结果，本轮未重复处理原始几何。

多灰度值本身不必然代表影像损坏，也不能仅凭扩展名将其认作完整分割。此处不把三个病例一概判为完全相同的问题。

## 新增历史文献证据

Michel Simões Martins，2024 年 UNESP 硕士论文，题名 *O uso de inteligência artificial generativa na modelagem digital de implantes personalizados para cranioplastia*。

公开原文：https://repositorio.ifsp.edu.br/bitstreams/73cc4693-5bc1-4f8d-be4f-5d3c0daebb2e/download

印刷页 76（PDF 第 94 页）的表格将 A0136、A0137 列入异常文件；印刷页 78（PDF 第 96 页）记录研究者向维护者 Jianning Li 请求替换数据，并转述对方当时无法提供未损坏替换版本，因此剔除了相关文件。该处名单包含 A0136、A0137，未列 A0138。

这是一手研究者对自己数据处理和联系过程的公开记录，但不是本次直接获得的作者回复，也不是当前官方维护公告。因此仅作为支持 A0136/A0137 存在历史上游问题的证据；不据此断言 A0138 同样损坏，或永久不存在其他数据。

## 作者 MONAI 预处理渠道

官方 README：https://github.com/Project-MONAI/research-contributions/tree/main/SkullRec

其链接 https://files.icg.tugraz.at/f/9642058af1744b4b961b/ 本轮再次访问仍失败；直接下载参数的访问记录见 `monai_link_retry.json`。没有检查该包病例清单，不能断言其中有或没有固定三来源。README 明确描述轴向裁剪至 256 层及不足时补零，因此即使获得该包，也需另查病例身份、空间变换和保留范围，不能直接视为原分辨率完整骨分割。

## 对科研下一步的含义

目前没有可直接接入的固定三病例完整骨 mask。官方版本检索这一分支已收敛，继续重下相同文件不能解决问题。现有 STL 仍是独立可用的表面几何来源；是否据其构造派生骨实体，需要明确独立方法及几何验证，不能冒称恢复作者原始 mask。本次未执行此类重建，也未替换三个固定来源。
