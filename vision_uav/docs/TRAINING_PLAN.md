# TRAINING_PLAN

## 目标

这一轮不是冲极限精度，而是拿到一版一夜内可复现、可导出、可推理的正式基线。

## 指标门槛

- 过线：
  - `val mAP50 >= 0.80`
  - `val mAP50-95 >= 0.35`
  - `val recall >= 0.72`
- 目标：
  - `val mAP50 >= 0.85`
  - `val mAP50-95 >= 0.40`
  - `val recall >= 0.76`
- 理想：
  - `val mAP50 >= 0.88`
  - `val mAP50-95 >= 0.45`
  - `val recall >= 0.80`

## 训练顺序

1. `train_probe_full_yolo26s.yaml`
2. `train_full_yolo26s_nightly_b8.yaml` 或 `train_full_yolo26s_nightly_b4.yaml`
3. `evaluate.py --config eval_full_test_yolo26s.yaml`
4. 对 `Anti-UAV300/test/` 中按名称排序的前 3 段 `visible.mp4` 逐个运行推理
5. `export_onnx.py --config export_onnx_formal.yaml`

## Probe 规则

- `YOLO26s`
- `imgsz=960`
- `batch=8`
- `epochs=1`
- `fraction=0.02`
- `workers=4`
- `device=0`

如果 probe 能正常完成训练，则夜训默认走 `b8`。

如果 probe 抛出显存不足或明显训练不稳定，则夜训退到 `b4`。

如果 probe 估算的正式训练时长已经明显超过一夜预算，则 pipeline 不会盲目开跑，而是直接在 probe 处终止。

## 夜训配置

### b8 方案

- `YOLO26s`
- `imgsz=960`
- `batch=8`
- `epochs=30`
- `patience=8`
- `workers=4`
- `cos_lr=true`
- `close_mosaic=5`

### b4 方案

- `YOLO26s`
- `imgsz=896`
- `batch=4`
- `epochs=24`
- `patience=8`
- 其余参数与 `b8` 一致

## 当前现实检查

2026-04-15 的真实 probe 已经跑过一次：

- `YOLO26s`
- `imgsz=960`
- `batch=8`
- `fraction=0.02`
- `epochs=1`
- `val precision = 0.497`
- `val recall = 0.435`
- `val mAP50 = 0.303`
- `val mAP50-95 = 0.0958`
- probe 总耗时约 `217.1s`

基于当前实现里的保守估算，这台 `RTX 4070 Laptop GPU 8GB` 上：

- `b8` 方案约 `90.46h`
- `b4` 方案约 `144.74h`

结论：`YOLO26s` 的这套全量夜训参数不符合“一夜内出结果”的预算，所以当前 pipeline 默认不会继续往下跑正式训练。

## 当前边界

- 不切到 `YOLO26m`
- 不引入 `Drone-vs-Bird` 训练
- 不做跟踪
- 不做二阶段鸟机分类
- 不根据 `test` 反复调参

## Windows 路径兼容

- `C:\vision_uav_data`：数据目录 ASCII junction
- `C:\vision_uav_workspace`：工作区 ASCII junction

两者存在的目的都是规避 Windows 中文路径对 `Ultralytics` / `OpenCV` 的兼容问题。

## A800 训练机专项

如果训练放在 `A800-SXM4-80GB` 上，不应该继续沿用 `batch=8, workers=4, cache=false` 这套保守参数。

仓库里单独提供了 A800 配置：

- `train_probe_full_yolo26s_a800_b64.yaml`
- `train_full_yolo26s_a800_b64.yaml`
- `train_full_yolo26s_a800_b48.yaml`

建议顺序：

1. 先跑 `train_probe_full_yolo26s_a800_b64.yaml`
2. 如果显存和吞吐稳定，则正式训练走 `train_full_yolo26s_a800_b64.yaml`
3. 如果 `b64` 不稳定或显存不足，再退到 `train_full_yolo26s_a800_b48.yaml`

这套 A800 配置的核心变化只有三点：

- `batch` 提到 `64` 或 `48`
- `workers` 提到 `16`
- `cache=ram`

目标不是改算法，而是先把大显存和大带宽真正吃起来。
