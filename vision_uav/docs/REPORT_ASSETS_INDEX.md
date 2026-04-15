# REPORT_ASSETS_INDEX

## 说明

这份索引用来给后续报告写作直接找素材。当前建议优先使用本地备份目录下的文件，而不是远端原始路径。

本地备份根目录：

- `vision_uav/runs/backup/20260415_a800_formal/`

该目录位于 `vision_uav/runs/` 下，默认被 `.gitignore` 忽略，不会进入 Git。

## 目录结构

### 1. 训练快照

路径：

- `vision_uav/runs/backup/20260415_a800_formal/stage1_train_snapshot/`

内容：

- `stage1_train_snapshot.tar.gz`
- `manifest.txt`
- `sha256.txt`
- `extracted/stage1_train_snapshot/formal_run/`
- `extracted/stage1_train_snapshot/probe_run/`
- `extracted/stage1_train_snapshot/logs/a800_yolo26s_b64.log`

用途：

- `formal_run/results.csv`
  - 正式训练逐 epoch 指标
- `formal_run/results.png`
  - 训练过程曲线总览
- `formal_run/BoxPR_curve.png`
  - PR 曲线
- `formal_run/BoxP_curve.png`
  - Precision 曲线
- `formal_run/BoxR_curve.png`
  - Recall 曲线
- `formal_run/BoxF1_curve.png`
  - F1 曲线
- `formal_run/confusion_matrix.png`
  - 混淆矩阵
- `formal_run/confusion_matrix_normalized.png`
  - 归一化混淆矩阵
- `formal_run/val_batch*_pred.jpg`
  - 验证集预测示例
- `formal_run/weights/best.pt`
  - 最终报告默认引用的正式模型
- `formal_run/weights/last.pt`
  - 训练结束时最后一版权重

### 2. 评估、推理与导出快照

路径：

- `vision_uav/runs/backup/20260415_a800_formal/stage2_eval_infer_export/`

内容：

- `stage2_eval_infer_export.tar.gz`
- `manifest.txt`
- `sha256.txt`
- `extracted/stage2_eval_infer_export/eval/`
- `extracted/stage2_eval_infer_export/infer_1_anti_uav_rgb_yolo26s_a800_b643_20190925_111757_1_10/`
- `extracted/stage2_eval_infer_export/infer_2_anti_uav_rgb_yolo26s_a800_b643_20190925_111757_1_1/`
- `extracted/stage2_eval_infer_export/infer_3_anti_uav_rgb_yolo26s_a800_b643_20190925_111757_1_2/`
- `extracted/stage2_eval_infer_export/onnx/best.onnx`
- `extracted/stage2_eval_infer_export/logs/`

用途：

- `eval/`
  - `test` 集评估图表和样例
- `infer_*/overlay.mp4`
  - 报告里最直观的推理可视化视频
- `infer_*/predictions.jsonl`
  - 结构化检测结果，可用于后处理和统计
- `onnx/best.onnx`
  - 部署模型备份
- `logs/a800_eval_test.log`
  - `test` 集评估日志
- `logs/a800_export_onnx.log`
  - ONNX 导出和 `onnxruntime` 验证日志
- `logs/a800_infer_*.log`
  - 三段视频推理日志

## 报告中建议优先使用的素材

### 正式结果

- 正式训练指标：
  - `stage1_train_snapshot/manifest.txt`
  - `stage1_train_snapshot/extracted/stage1_train_snapshot/formal_run/results.csv`
- `test` 集指标：
  - `stage2_eval_infer_export/manifest.txt`
  - `stage2_eval_infer_export/extracted/stage2_eval_infer_export/logs/a800_eval_test.log`

### 图表

- 训练过程总览：
  - `formal_run/results.png`
- PR / P / R / F1 曲线：
  - `formal_run/BoxPR_curve.png`
  - `formal_run/BoxP_curve.png`
  - `formal_run/BoxR_curve.png`
  - `formal_run/BoxF1_curve.png`
- 混淆矩阵：
  - `formal_run/confusion_matrix.png`
  - `formal_run/confusion_matrix_normalized.png`

### 视觉案例

- 优先展示 3 段 `overlay.mp4`
- 如果需要帧级结果或统计，配套使用对应的 `predictions.jsonl`

### 模型与部署

- 训练模型：
  - `formal_run/weights/best.pt`
- 导出模型：
  - `stage2_eval_infer_export/extracted/stage2_eval_infer_export/onnx/best.onnx`

## 当前默认引用规则

- 写正式训练结果时，默认引用 `best.pt` 对应结果，不引用 `last.pt`
- 写模型泛化时，默认引用 `test` 集评估结果，不用 `val` 代替
- 写部署可行性时，默认引用 `best.onnx` 和 `a800_export_onnx.log`
