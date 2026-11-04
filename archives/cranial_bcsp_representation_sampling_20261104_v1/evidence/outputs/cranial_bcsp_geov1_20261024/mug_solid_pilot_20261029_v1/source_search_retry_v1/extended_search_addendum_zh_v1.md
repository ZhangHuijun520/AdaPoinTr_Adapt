# 固定三病例扩展检索补充

日期：2026-10-29。

用户提供的另一段 ChatGPT 检索回答未声称已获取可用文件：其明确说明 A0136/A0137 暂未找到验证通过的修复版，A0138 尚需检查，文件名按命名规范推定。其引用与当前检索一致，没有新增病例分割直链。

扩展检查 MedShapeNet 官方项目、论文、MedShapeNet 2.0 仓库以及 MedShapeNetCore Zenodo。论文有 MUG500+ 包含二值 masks 的数据集级描述，但没有证明三个固定病例都存在完整可用分割。

实际从官方项目页面提供的下载索引获取 10,921,900 bytes 文本，共 106,101 行链接，保存为本目录 `MedShapeNetDataset_index.txt`。未找到 A0136/A0137/A0138 或 MUG 名称。索引使用重编号和解剖结构名称，例如 `000000_tumoredbrain.stl`，故名称未命中不能证明病例不存在；该索引也不能直接提供固定三病例 mask 与原编号、坐标的对应关系。未下载形状 payload 或进行 STL 体素化。

MedShapeNetCore 当前所查 Zenodo 清单未列 MUG500 命名的包；不能凭其他颅骨相关包名认定为固定三病例。

来源：

- https://mml.ikim.nrw/ait/projects/medshapenet/
- https://mml.ikim.nrw/ait/projects/medshapenet/MedShapeNetDataset.txt
- https://github.com/GLARKI/MedShapeNet2.0
- https://zenodo.org/records/10623506
- https://pmc.ncbi.nlm.nih.gov/articles/PMC13332746/

当前结论保持“尚未找到经文件内容与身份验证的三病例完整骨分割”，而不是“确定任何渠道都不存在”。A0138 未在历史异常名单中不构成完整性证明；本机已有其官方归档，实际空间覆盖不满足既定切除位置，仍需原完整分割或独立验证的派生实体方法。现有 STL 的存在与二值分割可直接取得是不同事实。
