# MUG三个同编号来源：分割补齐与坐标证据报告 v1

日期：2026-10-29。**坐标约定已补证；完整骨分割未取得。** 用户确认没有其他分割路径／下载链接。没有生成任何替代mask、缺损、点云、训练或GPU结果。

## 已完成的来源与坐标补证

1. 本机A0136-A0140.zip共2,113,114,570字节，MD5为93b5498c885765bc222e507aa60af6f4，与已保存的官方Figshare v20文件元数据一致；SHA256为5dbe7b303ae70080bd92c535b13aac4f4b647644735391f8fb49580e9f981481。这排除了相对该官方v20文件的本机下载损坏，不证明原发布内容无问题。仅对封包整体按字节校验，没有解码A0139/A0140几何。
2. 三个原STL文件头均明确写有`3D Slicer output. SPACE=RAS`；NRRD声明`left-posterior-superior`。依据[3D Slicer官方文件规范](https://slicer.readthedocs.io/en/latest/user_guide/data_loading_and_saving.html#specifying-the-coordinate-system-in-model-files)，RAS与LPS之间使用diag(-1,-1,1,1)，无需拟合配准。
3. clear STL文件头只有VCG，不含坐标声明。本轮逐例固定256个顶点位置，在同编号原STL中均找到完全相同的float32坐标（256/256）。比较最后还核对12字节坐标，未以哈希碰撞或近邻容差冒充精确一致。它支持clear STL沿用RAS，但不是全顶点坐标或完整解剖配准认证。
4. 已保存逐例NRRD index→LPS、index→RAS矩阵；历史切除中心及frame均按同一T转换、radii不变。仅记录派生参数，没有改动旧生成器、NRRD或STL。6项人工CPU检查通过。

```text
[x_LPS,y_LPS,z_LPS,1]^T = diag(-1,-1,1,1) [x_RAS,y_RAS,z_RAS,1]^T
p_LPS = A^T i + origin   (A的行是NRRD各体素轴的space direction)
center_LPS = T3 center_RAS; frame_LPS = T3 frame_RAS; radii保持mm不变
```

## 坐标修正仍不能补齐缺失体积

| 来源 | 精确采样坐标匹配 | 转换后NRRD覆盖完整clear STL | 历史切除中心在NRRD FOV内 |
|---|---:|---|---|
| A0136 | 256/256 | 否 | 是 |
| A0137 | 256/256 | 否 | 否 |
| A0138 | 256/256 | 否 | 否 |

NRRD实际形状仍为A0136:638×512×125、A0137:512×512×2、A0138:512×512×38，且均为多值标量图像。X／Y符号翻转不会增加缺失切片或产生骨标签。A0137和A0138的原固定切除中心甚至落在现有体积FOV之外；不得通过零填充、重采样或移动切除中心伪装为原始实体完整。A0136切除中心在FOV内也不等于完整骨mask已成立。

原先pilot报告关于“未建立坐标关系”的判断已由本轮补充为：原STL和NRRD坐标约定可解析，clear继承关系获固定采样支持；完整体积／骨标签及完整几何对应仍未成立。旧报告保留，不覆盖。

## 完整分割的查找情况

- 在本机所查目录及指定ZIP三个来源子目录中，未找到独立骨分割mask；已确认NRRD并非可直接作为C的骨标签。
- [数据集原论文](https://www.sciencedirect.com/science/article/pii/S2352340921008003)说明网格由专家按病例设定阈值的分割产生。该描述不等于当前三份标量NRRD就是所需骨mask，也不能据此猜测每例阈值。
- [作者仓库](https://github.com/Jianningli/mug500plus)列出的常规成员为NRRD、PNG、STL及clear STL；本轮没有找到可核验的这三个编号的单独修正mask。实时Figshare API访问失败，因此不宣称最新版本一定没有修复。
- [MONAI SkullRec作者实现](https://github.com/Project-MONAI/research-contributions/tree/main/SkullRec)链接了预处理数据包，但该下载端点经web访问及15秒有界curl均超时。本轮未下载或检查其内部病例，也不把经过裁剪／补零的训练数据自动视为原网格完整专家mask。
- [MONAI论文](https://doi.org/10.1016/j.softx.2023.101432)报告曾排除21份损坏图像；它没有在已查正文中提供当前三编号的对应判定，故不能替代本轮逐例证据。
- 用户已确认没有其他文件路径或链接。没有向作者发送邮件，也没有拿其他病例替换固定三例。

## 当前结论与可执行的后续选择

**当前不能完成“原始完整骨分割补齐”。** 缺少的源标签和扫描范围不是坐标转换能恢复的信息。完整骨mask取得数为0；缺损及8k采样配对生成数为0。

保留固定三病例时，有两条诚实路线：其一，取得作者／数据持有方的原始完整骨标签或修正影像与标签，并核验同编号及物理坐标；其二，另行明确从现有STL重建骨组织体积的派生方法，先验证内外板、孔洞与骨厚度，再进行切除。第二条路线是新的派生几何构造，不能标成找回原始专家分割。

具体上游索取清单见missing_assets_request_zh_en_v1.md（草稿，未发送）。本轮不自动阈值分割、不填洞、不做自由配准、不更换source、不训练。

## 可核验产物

- coordinate_contract_v1.json：三例完整矩阵、坐标证据等级、固定切除参数转换及FOV缺口。
- results/*_coordinate_evidence.json：原STL哈希、固定样本及精确匹配结果。
- asset_search_coverage_v1.json：已查来源、网络失败及未核验范围。
- CPU_tests.json、scope.json：6项CPU检查及固定读取预算。
- 上一阶段原始标量剖面、分布与源核查报告位于上级results目录。
