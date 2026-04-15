# 历史实验脚本登记

这里先登记仓库中已经发现、但当前不直接纳入主工程结构的历史实验脚本来源。

## 已发现脚本

来源目录：

- `projects/fpga_pspl/Miz_sys/Miz_sys.srcs/sources_1/bd/system/ipshared/b2d0/hdl/verilog/`

脚本列表：

- `radar.py`
- `import numpy as np.py`

## 当前处理原则

- 本轮不直接修改这些原始脚本。
- 它们所在位置明显不是正式工具目录，更像历史实验残留。
- 后续如果需要保留功能，将在 `tools/radar/` 下用新的规范化脚本重写或替代。

## 备注

- 这些文件当前更多作为“曾做过临时分析/画图尝试”的证据，而不是正式运行入口。
