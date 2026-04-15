# DATASETS

## 第一阶段主线

第一阶段主训练集固定为 `Anti-UAV` 的 RGB 可见光子集。

原因只有三个：

1. 它和当前项目目标一致，都是地面视角下的低空无人机检测。
2. 数据里目标很小、背景复杂，比通用检测数据更接近真实反无人机场景。
3. 官方公开资料明确把它定义为反无人机 benchmark，而不是航拍车人数据集。

官方入口：

- 数据集主页：https://anti-uav.github.io/dataset/
- 官方仓库：https://github.com/ucas-vg/Anti-UAV

## 为什么不选 VisDrone / UAVDT 作为主线

`VisDrone` 和 `UAVDT` 更适合“无人机俯拍地面小目标”，典型目标是车、人、交通场景。  
你的项目目标是“地面设备看空中的低空无人机”，视角、目标尺度和误检来源都不一样。

它们可以作为后续泛化性补充，但不适合作为第一阶段主训练集。

## Drone-vs-Bird 的角色

`Drone-vs-Bird` 不并入第一阶段主训练集，而是先作为硬负样本评估集。

原因：

1. 这个数据集的核心价值是“鸟和远距离小无人机的混淆”。
2. 当前最需要先回答的问题不是“怎么做复杂多类训练”，而是“主检测链是否稳定、鸟类是否是主要误检来源”。

官方挑战仓库：

- https://github.com/wosdetc/challenge

## Anti-UAV410 的角色

`Anti-UAV410` 当前不进第一阶段主线。

原因：

1. 它更偏红外跟踪 benchmark。
2. 第一阶段只做 RGB 检测离线基线，不做多模态、不做跟踪。

官方仓库：

- https://github.com/HwangBo94/Anti-UAV410

## 当前数据准备约定

- 只读取每个序列目录下的 `RGB.mp4` 和 `RGB_label.json`
- 只保留一个类别：`uav`
- 按视频序列切分 `train/val/test`
- `train` 默认每 5 帧抽 1 帧，`val/test` 默认每 10 帧抽 1 帧
- 无目标帧保留为空标签图像
