# MODEL_OPTIMIZATION

## 目标

这份文档记录当前正式视觉模型在 hard negative 场景下的优化过程，重点回答两个问题：

1. 单靠调置信度阈值是否足够；
2. 是否必须进入一轮 hard negative 补训。

当前正式模型固定为：

- `vision_uav/runs/train/anti_uav_rgb_yolo26s_a800_b643/weights/best.pt`

## 本轮执行顺序

### 1. 先跑背景负样本阈值搜索

执行内容：

- 从 `Anti-UAV300` 处理后数据中提取空标签背景帧；
- 构建 `anti_uav_background_only/val + test`；
- 在阈值 `0.20 ~ 0.50` 上做 hard negative 搜索。

对应入口：

- `vision_uav/scripts/prepare_background_hard_negatives.py`
- `vision_uav/scripts/sweep_hard_negative_thresholds.py`
- `vision_uav/configs/hard_negative_threshold_sweep.yaml`

实际结果：

- 背景负样本总帧数：`913`
- 最好的一档阈值是 `0.50`
- 但聚合 `frame_false_positive_rate = 0.06681`
- 没有达到目标上限 `0.05`

结论：

- 只用背景负样本时，单靠调阈值不够。

### 2. 接入鸟类 hard negative

为了避免只用背景负样本得出片面结论，本轮额外接入 `FBD-SV-2024` 作为鸟类 hard negative 源。

实际处理方式：

- 下载 `FBD-SV-2024.zip`
- 抽取 `40` 段 train 鸟类视频
- 抽取 `8` 段 val 鸟类视频
- 从 train 鸟类视频中按固定步长抽帧
- 生成 `375` 张鸟类 hard negative 训练图像，并为其创建空标签

对应入口：

- `vision_uav/scripts/prepare_fbd_sv_hard_negatives.py`
- `vision_uav/configs/hard_negative_bird_threshold_sweep.yaml`
- `vision_uav/configs/train_hn_a800_b64.yaml`

说明：

- `train_hn_a800_b64.yaml` 已经准备好，作为“如果阈值不够则立刻补训”的备用入口；
- 但本轮最终没有执行这一步，因为阈值优化已经满足约束。

## 鸟类 + 背景联合阈值搜索结果

联合 hard negative 来源：

- `Anti-UAV` 空标签背景帧
- `FBD-SV-2024` 抽取的 `8` 段鸟类验证视频

聚合 hard negative 总帧数：

- `1573`

阈值搜索规则：

- 目标：`frame_false_positive_rate <= 0.05`
- 同时要求：
  - `val recall` 相比基线下降不超过 `0.03`
  - `test recall` 相比基线下降不超过 `0.03`

当前正式基线：

- `baseline val recall = 0.978`
- `baseline test recall = 0.900`

最终推荐阈值：

- `confidence = 0.45`

推荐阈值下的结果：

| 项目 | 数值 |
| --- | ---: |
| hard negative 总帧数 | 1573 |
| hard negative 检出帧数 | 77 |
| hard negative 聚合 `frame_false_positive_rate` | 0.04895 |
| val recall | 0.97538 |
| val recall drop | 0.00262 |
| test recall | 0.87975 |
| test recall drop | 0.02025 |

结论：

- `0.45` 已满足 hard negative 误检率约束；
- `val/test recall` 降幅都没有超过 `0.03`；
- 因此本轮**不需要**进入 hard negative 补训。

## 当前最终结论

本轮模型优化结论如下：

1. 背景负样本单独使用时，阈值优化不够。
2. 引入鸟类 hard negative 后，`confidence = 0.45` 已经满足约束。
3. 当前最合理的工程动作不是立刻重训，而是：
   - 将正式默认推理阈值调整到 `0.45`
   - 后续继续积累更真实的鸟类/纯天空/复杂背景负样本
   - 如果未来 hard negative 误检率再次超标，再启用 `train_hn_a800_b64.yaml`

## 相关产物

### 背景负样本阶段

- `vision_uav/runs/hard_negatives/anti_uav_rgb_yolo26s_a800_b643_threshold_sweep/threshold_sweep.csv`
- `vision_uav/runs/hard_negatives/anti_uav_rgb_yolo26s_a800_b643_threshold_sweep/hard_negative_summary.json`

### 鸟类 + 背景阶段

- `vision_uav/runs/hard_negatives/anti_uav_rgb_yolo26s_a800_b643_bird_threshold_sweep/threshold_sweep.csv`
- `vision_uav/runs/hard_negatives/anti_uav_rgb_yolo26s_a800_b643_bird_threshold_sweep/hard_negative_summary.json`
- `vision_uav/data/processed/anti_uav_rgb_detect_hn/summary.json`

## 下一步建议

- 把正式离线推理的默认阈值统一改到 `0.45`
- 用这组推荐阈值继续推进融合 MVP
- 后续如果有 `Drone-vs-Bird` 或自采鸟类视频，再复用当前流程重新验证

## 结论补充（2026-04-16）

这一轮的直接结论可以压缩成三点：

1. 只看 `Anti-UAV300` 中的空标签背景帧时，`0.20 ~ 0.50` 的阈值搜索仍然无法把 `frame_false_positive_rate` 压到 `0.05` 以下，说明“只靠背景负样本调阈值”不够。
2. 接入 `FBD-SV-2024` 鸟类视频后，推荐阈值收敛到 `confidence = 0.45`。在该阈值下，联合 hard negative 的 `frame_false_positive_rate = 0.04895`，同时 `val recall` 下降 `0.00262`，`test recall` 下降 `0.02025`，仍在预设的 `0.03` 约束内。
3. 因此本轮**不需要**启动 hard negative 补训。当前最合理的工程动作是把正式离线推理阈值统一到 `0.45`，继续推进融合链路，而不是立即再训一版模型。

对“鸟类是否是主要误检来源”的回答也可以明确一点：

- 从背景负样本单独评估看，误检问题没有被充分解释。
- 加入鸟类 hard negative 后，阈值搜索结果明显改善，说明鸟类确实是当前误检来源中的重要组成部分。
- 但现阶段还不能把“鸟类”断言为唯一或绝对主导来源，因为我们还没有覆盖更多自采纯天空、复杂背景和远距离非目标视频。

本轮应默认采用的模型与阈值组合为：

- 模型：`vision_uav/runs/train/anti_uav_rgb_yolo26s_a800_b643/weights/best.pt`
- 推荐阈值：`0.45`
- 对应结果目录：`vision_uav/runs/hard_negatives/anti_uav_rgb_yolo26s_a800_b643_bird_threshold_sweep/`
