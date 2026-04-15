# EVAL_PROTOCOL

## 目标

这份流程用于固定 `vision_uav` 当前阶段的验收顺序，避免训练结束后只看总指标，不看泛化和误检来源。

当前正式模型默认指向：

- `vision_uav/runs/train/anti_uav_rgb_yolo26s_a800_b643/weights/best.pt`

## 固定顺序

### 1. 先看正式训练结果

优先读取：

- `vision_uav/docs/INITIAL_RESULTS.md`
- `vision_uav/runs/backup/20260415_a800_formal/stage1_train_snapshot/manifest.txt`
- `vision_uav/runs/backup/20260415_a800_formal/stage1_train_snapshot/extracted/stage1_train_snapshot/formal_run/results.csv`

当前正式训练结论：

- 最佳 epoch：`18`
- 实际训练到：`26` epoch
- `val precision ≈ 0.980`
- `val recall ≈ 0.978`
- `val mAP50 ≈ 0.993`
- `val mAP50-95 ≈ 0.686`

### 2. 再看 test 集评估

固定入口：

- 配置：`vision_uav/configs/eval_a800_test_yolo26s.yaml`
- 脚本：`vision_uav/scripts/evaluate.py`

当前 `test` 结果：

- `precision ≈ 0.961`
- `recall ≈ 0.900`
- `mAP50 ≈ 0.937`
- `mAP50-95 ≈ 0.537`

用途：

- 用来判断模型是否真的能泛化到未参与调参的测试集。
- 后续所有提分动作都应优先解释为什么 `test mAP50-95` 和 `recall` 还能继续提高。

### 3. 再看 3 段代表性视频

优先查看本地备份里的：

- `stage2_eval_infer_export/.../infer_1_*/overlay.mp4`
- `stage2_eval_infer_export/.../infer_2_*/overlay.mp4`
- `stage2_eval_infer_export/.../infer_3_*/overlay.mp4`

同时配合：

- `predictions.jsonl`

重点看：

- 远距离小目标是否漏检
- 连续帧是否抖动明显
- 背景复杂处是否有稳定误检
- 框中心是否偏离目标

### 4. 最后才看硬负样本

硬负样本默认指：

- 鸟类视频
- 纯天空背景
- 远景复杂背景但没有无人机的序列

固定入口：

- 配置模板：`vision_uav/configs/eval_hard_negatives_template.yaml`
- 脚本：`vision_uav/scripts/evaluate_hard_negatives.py`

核心思路：

- 当前阶段先把所有检测都当成“误检”
- 先回答“鸟类是不是主要误检来源”
- 不先急着做二阶段分类或重新训练

## 推荐命令

### 跑硬负样本评估

```powershell
python vision_uav/scripts/evaluate_hard_negatives.py `
  --model vision_uav/runs/train/anti_uav_rgb_yolo26s_a800_b643/weights/best.pt `
  --source <你的硬负样本视频或图片目录> `
  --source-id bird_eval_001 `
  --project vision_uav/runs/hard_negatives `
  --name bird_eval_001
```

输出固定包括：

- `overlay.mp4`
- `predictions.jsonl`
- `false_positive_summary.json`
- `top_false_positive_frames.json`
- `frame_detections.csv`

## 当前建议

- 下一轮不要立刻再训模型。
- 先把 `Drone-vs-Bird` 或你自己的鸟类视频拿来跑硬负样本评估。
- 如果误检主要来自鸟类，再决定是否做：
  - 阈值调整
  - hard negative 补训
  - 二阶段鸟机分类
