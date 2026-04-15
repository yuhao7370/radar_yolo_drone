# LITERATURE_NOTES

## 当前只记录和第一阶段强相关的资料

第一阶段不是做论文复现，而是建立可复现实验链。所以这里只保留会直接影响模型、数据和评估选择的资料。

## 1. Anti-UAV Benchmark

- 官方数据页：https://anti-uav.github.io/dataset/
- 官方仓库：https://github.com/ucas-vg/Anti-UAV

对当前工程最有用的结论：

1. 这是反无人机场景的专门 benchmark。
2. 目标普遍很小，背景复杂，适合做低空无人机视觉检测基线。
3. 有 RGB / IR 两种模态，但当前阶段只取 RGB。

## 2. Drone-vs-Bird Challenge

- 官方挑战仓库：https://github.com/wosdetc/challenge
- Benchmark 汇总说明：https://github.com/KostadinovShalon/UAVDetectionTrackingBenchmark

对当前工程最有用的结论：

1. 它不是主训练集候选，而是典型硬负样本来源。
2. 它直接对应“鸟类误检”这个真实风险点。
3. 第一阶段先拿它做误检评估，比直接并入训练更容易判断瓶颈。

## 3. Ultralytics 检测主线

- 官方文档：https://docs.ultralytics.com/zh/

对当前工程最有用的结论：

1. 当前优先采用 `YOLO26`，保留 `YOLO11` 作为回退。
2. 先把训练、推理、导出打通，再决定是否需要额外小目标增强技巧。
3. 第一阶段不把跟踪、分割和自定义复杂 head 一起塞进主线。

## 4. 当前论文阅读边界

第一阶段不追求“先找最好论文再实现”，而是先拿一个稳定、可导出、可复现的检测基线。

只有在以下情况出现时，才进入第二阶段文献深化：

1. `Anti-UAV` 主验证集召回率明显不足。
2. `Drone-vs-Bird` 上鸟类误检率明显偏高。
3. `YOLO26s` 在 1280 输入下仍无法覆盖远距离 tiny target。
