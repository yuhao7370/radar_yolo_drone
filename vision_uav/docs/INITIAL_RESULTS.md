# INITIAL_RESULTS

## 日期

2026-04-16

## 当前状态

- `vision_uav/` 已经从“离线基线骨架”推进到“有真实正式结果”的阶段。
- `Anti-UAV300` RGB 数据已经完整转成 YOLO detect 目录，可直接复现训练、评估、推理和导出。
- A800 正式训练、`test` 评估、3 段测试视频推理和 ONNX 导出都已完成。
- 远端关键产物和日志已经拉回本地，并在 `vision_uav/runs/backup/20260415_a800_formal/` 做了双阶段备份。

## 数据与环境基线

- 原始数据：`vision_uav/data/raw/anti_uav/Anti-UAV300/`
- 处理后数据：`vision_uav/data/processed/anti_uav_rgb_detect/`
- 处理后规模：
  - `train = 29,924` 帧
  - `val = 6,208` 帧
  - `test = 8,547` 帧
- 本地已验证的独立环境：`vision-uav`
- 本地 GPU：`NVIDIA GeForce RTX 4070 Laptop GPU`
- 正式训练 GPU：`NVIDIA A800-SXM4-80GB`

## 本地冒烟结果

使用 `YOLO26n` 在本地 4070 上完成过 1 epoch 冒烟训练，用于确认数据转换、CUDA 环境和训练入口已打通：

- 输出目录：`vision_uav/runs/train/anti_uav_rgb_yolo26n_smoke3/`
- 指标：
  - `precision = 0.786`
  - `recall = 0.745`
  - `mAP50 = 0.835`
  - `mAP50-95 = 0.311`

这组结果只用于证明链路已通，不作为正式基线。

## A800 正式训练结果

正式训练使用：

- 模型：`YOLO26s`
- 图像尺寸：`960`
- batch：`64`
- 训练卡：`A800 80GB`
- 训练目录：`vision_uav/runs/train/anti_uav_rgb_yolo26s_a800_b643/`

训练结论：

- 触发 `EarlyStopping`
- 最佳 epoch：`18`
- 实际运行到：`26` epoch
- 总耗时：`2.554` 小时

最佳模型 `best.pt` 的最终验证结果：

- `precision ≈ 0.980`
- `recall ≈ 0.978`
- `mAP50 ≈ 0.993`
- `mAP50-95 ≈ 0.686`

`results.csv` 中最佳行对应指标：

- `best_row_epoch = 18`
- `best_row_precision = 0.97998`
- `best_row_recall = 0.97897`
- `best_row_mAP50 = 0.99289`
- `best_row_mAP50_95 = 0.68635`

## Test 评估结果

使用 `best.pt` 在 `test` 集上单独评估：

- 配置：`vision_uav/configs/eval_a800_test_yolo26s.yaml`
- 输出目录：`vision_uav/runs/eval/anti_uav_rgb_yolo26s_a800_b643_test/`

指标：

- `precision = 0.96060`
- `recall = 0.90000`
- `mAP50 = 0.93655`
- `mAP50-95 = 0.53709`

## 测试视频推理与 ONNX 导出

已完成 3 段测试视频离线推理：

- `20190925_111757_1_10/visible.mp4`
- `20190925_111757_1_1/visible.mp4`
- `20190925_111757_1_2/visible.mp4`

每段都生成了：

- `overlay.mp4`
- `predictions.jsonl`

ONNX 导出结果：

- 导出配置：`vision_uav/configs/export_onnx_a800_formal.yaml`
- 实际导出文件：`vision_uav/runs/train/anti_uav_rgb_yolo26s_a800_b643/weights/best.onnx`
- `onnxruntime` 最小验证已通过：
  - `onnx_input=images`
  - `onnx_outputs=1`

## 本地备份位置

本轮正式结果的本地备份根目录：

- `vision_uav/runs/backup/20260415_a800_formal/`

其中分成两段：

- `stage1_train_snapshot/`
  - 保存正式训练目录、A800 probe 目录、主训练日志
  - 同时保留 `tar.gz`、`manifest.txt`、`sha256.txt` 和解压目录
- `stage2_eval_infer_export/`
  - 保存 `test` 评估目录、3 段推理输出、`best.onnx` 和对应日志
  - 同时保留 `tar.gz`、`manifest.txt`、`sha256.txt` 和解压目录

这两个目录位于 `vision_uav/runs/` 下，已经被 `.gitignore` 排除，不会进入 Git。

## 当前结论

- 视觉链路已经具备“可训练、可评估、可推理、可导出、可备份”的完整闭环。
- 当前最有价值的正式模型是 `anti_uav_rgb_yolo26s_a800_b643/weights/best.pt`。
- 下一步不应该再重复做同类训练，而应转到：
  - 错误分析
  - 鸟类硬负样本评估
  - 与 `mmradar` 的时间戳和结果接口对接准备
