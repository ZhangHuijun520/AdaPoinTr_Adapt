# RIVE Requery_C正式训练后冻结审计与Static_C配对核验

**通过，43项检查全部通过。**

## 完成和产物

退出码0，tmux与worker均结束；精确3900更新、100 traversals、31200曝光、300drop。16输出文件、21安装/控制文件、目录集合及12成员payload manifest符合冻结合同。审计前后37个文件SHA及内容相关属性完全相同，未用atime作为漂移判据。

最终checkpoint为489927058字节，两次独立流式实测SHA256：

```text
5fc095755fa22fec79230394f3d3cd5dc461fd18e4ff1e366e52e5ae033dc87e
```

与completion和产物manifest一致；未反序列化权重。

## 两臂配对

Static_C与Requery_C的initialization、order_plan、exposure、optimizer_actual_defaults、optimizer_parameter_groups五文件逐字节相同；完整3900实际batch的病例/来源、LR、BN动量、clip及提交计数逐条一致。相同设备、共同模型母版、初态、初始化bin、原runtime和资源预算；模型构造RF记录除variant外一致。Static已冻结控制文件未漂移。两臂训练终态权重不同属于预期，不要求相同。

## 重查询与资源

3900条阶段几何及loss记录逐项核对通过。Requery仅第一步全部N0=N1，平均邻域重合约64.48%；第二残差非零3899步，摘要满足Q0→Q1→Q2及Q2/coarse关系。这证明绑定实现和记录存在重查询变化，不证明精度改善；未重新运行KNN或forward。

3902资源记录全部条件独立重算通过，实际3600秒预算；完成elapsed1494.55秒。峰值SMI14638MiB，Torch allocated约12.99GiB、reserved约13.82GiB，workerRSS约1.55GiB，低于冻结阈值。采样监测不等于硬隔离或连续峰值保证；SMI/容器PID映射继续仅诊断。

BNCal、evaluation、resume均false；没有自动重试。completion里的旧stage为原runtime历史标签，run_identity明确RIVE/Requery/C；AdamW默认decay0.01被实际参数组5e−4/0覆盖，分组核验通过。

## 边界与下一步

本轮服务器零写入、模型调用零、checkpoint加载零、无评价或BNCal，没有根据训练loss判断补全质量。冻结原始回传、43项检查、产物哈希与配对结果已保存在本目录。

下一步按模式A矩阵可单独**准备Fold D Static待授权训练request**，复用已验证入口，绑定D折既定315病例、原order、相同初始化和3900步；不依据C折loss或邻域重合调参，不自动训练。执行前仍须重验当前资源与至少6GiB空间；完整矩阵容量仍未认证。补全收益需要后续四模型420次Native及统一来源配对评分，当前不作提前结论。
