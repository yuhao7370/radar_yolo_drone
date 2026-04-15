# vision_uav

独立于 `mmradar/` 的视觉工作区，先做地面反无人机离线检测基线。

当前阶段只覆盖 4 件事：

1. 建立可复现的 CUDA 训练环境。
2. 把 `Anti-UAV` RGB 数据转成 YOLO detect 结构。
3. 固化 `YOLO26` 冒烟训练与正式训练配置。
4. 提供离线推理、JSONL 结果输出和 ONNX 导出入口。

这条线暂时不做：

1. 不接 `mmradar` Qt 主程序。
2. 不接板端同步。
3. 不做雷达-视觉融合。
4. 不做跟踪、重识别或鸟机二阶段分类。

建议先看 [VISION_RUNBOOK.md](docs/VISION_RUNBOOK.md)。
