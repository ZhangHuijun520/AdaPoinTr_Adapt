# P1 配对预测入口 v2：精确源码读取修正与本机 P3

日期：2026-11-06。状态：implementation-only 完成，42/42 CPU 检查通过，本机 P3 通过，request 保持 AWAITING_EXPLICIT_USER_AUTHORIZATION。未操作服务器。

## 限定修正

只新增隔离 v2 预测入口与对应测试文件；保留 v1 失败现场。问题是 sys.path 已加入 P1 factory 目录，FilePolicy 却未允许读取这两个冻结源码文件。

新版只为 request 已绑定的 factory 与 encoder 两个精确 .py 路径增加只读例外，校验大小与 SHA256。预先打开只读文件描述符，审计回调通过描述符复核内容及 inode/size/mtime/ctime 一致性，避免 open → audit → 再 open 的递归。所有原有目录读取边界、秘密、payload/checkpoint、链接和写入拒绝规则保留；没有放行整个 factory 所在目录。

两个模块按精确源码字节直接编译加载：先 encoder，再 factory，使原始 factory 的 encoder 导入引用已绑定模块；不咨询邻近字节码。模块代码本身及其导出保持不变，不修改任何科研模型源码。

## CPU 验证

同一批42项检查全部通过：保留原35项人工循环/数据元信息/授权/状态RNG/失败停止合同，新增7项加载与拒绝回归。

- 独立CPU子进程启用真实既有 FilePolicy.audit，经新版实际生产加载函数读取、编译原始 factory 和 encoder；哈希与生产冻结身份相同；模块路径、导出类引用一致。
- 人工准备一个未绑定 .pyc，验证正常加载不读取或咨询它。
- 邻近未绑定源码、精确源码写入、未绑定字节码、初始哈希漂移、加载期内容漂移均被拒绝。
- 链接拒绝使用模拟链接元数据回归，不假设Windows有创建原生符号链接权限。

全部fixture均为本机人工文件；未加载真实checkpoint、未读取真实NPZ、未调用native Mamba或GPU kernel。原35项中完整210次循环使用人工Tiny模型；它验证调用与保存合同，不是科研预测结果。

## P3 与不变项

源码/测试/结果/stdout哈希已核对。AST确认 Budget、execute_pair、predict_once、load_checkpoint、load_partial、geometry_summary、rng_state、pack、validate_index/source/evidence 等原合同保持不变。只修改 authorize 的v2 schema、make_policy精确例外及main的加载接线/描述符关闭；新增三项精确读取/加载辅助。

重新核验人工完整循环归档213个成员的内容哈希。实际加载fixture中的原始factory和encoder字节与既定生产SHA256一致。P3见 local_P3_v2.json。

T0/M0两份最终权重、21来源105病例、V1点集、8k输入/输出、batch1、T0→M0顺序、210次forward、状态/RNG守卫均保持不变。训练/BNCal/loss/backward/optimizer均为0。不重复GPU preflight。资源阈值与环境配置保持原request不变。

## 新待授权 request 与运输

request：transport_payload/FoldC_T0_M0_development_execution_request_v2.json

完整SHA256：`187a19712d92cb5cdf92eebc2a46ffe5caf6e99614224bc8fbac0a2498e76b82`

运输包：bcsp_p1_foldC_paired_development_transport_v2.tar.gz，53233 bytes。SHA256：`e65944650e22742516a2a1619042f03a4fb49ecb02d48001771d4a927c5bf4f1`。9个成员，均已逐字节核验。另有 .sha256、.bytes、.contents.sha256 三个校验文件；安装映射见 transport_manifest_v2.json。不含真实点集或权重。

使用全新安装根、control、输出及tmux路径，末尾为v2。尚未材料化授权回执、runtime、launcher或launch claim；包中 .sh 仅为含占位哈希的模板。旧v1 request已消耗，不可复用。

本轮服务器操作、部署、真实推理及GPU preflight均为0。上传后须对本request完整SHA256另行明确授权，再核验当前身份、上传包、全部新目标不存在、父目录与复用资产，不覆盖安装并唯一一次执行；失败即停，不自动重试。
