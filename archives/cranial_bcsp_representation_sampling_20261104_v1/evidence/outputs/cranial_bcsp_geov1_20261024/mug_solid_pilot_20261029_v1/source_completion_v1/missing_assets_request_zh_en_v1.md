# 完整骨分割索取清单／作者联系草稿（未发送）

仅限A0136、A0137、A0138；不要求或替换成其他患者。

所需：同编号的完整骨组织binary labelmap（例如NRRD／NIfTI／seg.nrrd）、骨标签取值说明、原始spacing／direction／origin、与对应原STL及clear STL的物理坐标关系；如mask来自原CT，需提供完整CT及专家分割或明确的原始分割参数／处理记录。若公开版本有修正，请提供正式下载位置与校验值。

已有文件来自Figshare v20 A0136-A0140.zip（2,113,114,570字节，MD5 93b5498c885765bc222e507aa60af6f4）。NRRD分别为638×512×125、512×512×2、512×512×38的signed-int16多值标量图像。原STL头均为SPACE=RAS；NRRD为LPS。我们已记录RAS/LPS转换，无意通过配准修改几何以满足预期。

## English draft

Dear MUG500+ maintainers,

We are validating solid cranial-defect construction for the fixed cases A0136, A0137 and A0138. Our local archive matches the published v20 archive MD5 above. The distributed NRRDs for these cases contain multivalued scalar images with the dimensions listed above, rather than directly usable complete bone labelmaps. The corresponding original STL headers explicitly declare RAS, whereas the NRRDs declare LPS. Applying this coordinate convention conversion does not make the available volume field of view cover the complete clear STL.

Could you provide the complete expert bone segmentation labelmaps for these exact case IDs, or point us to corrected official files? We would also appreciate the label definitions, physical image affine, and any transform or processing history relating each labelmap to its original and clear STL. If only the full original CTs are available, please clarify the expert segmentation parameters and whether the missing volume ranges can be obtained. If no corrected assets are available, a confirmation would help us report the limitation accurately.

Thank you.

This draft has not been sent. The exact source hashes and local evidence are retained in coordinate_contract_v1.json and the preceding source-admission records.
