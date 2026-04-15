# FUSION_MVP

## 1. 本轮目标

这一轮推进的不是实时联显，也不是完整的雷达-视觉坐标级融合，而是一版**离线融合 MVP**：

- 先把雷达侧导出能力补齐，形成稳定的数据契约。
- 再把视觉 `predictions.jsonl` 与雷达 `radar_frames.jsonl` 做时间对齐。
- 在没有真实同步采样样本的前提下，先验证链路、字段、状态判定和可视化演示是否完整。

因此，本轮输出的价值在于“接口可用、流程可跑、演示可看”，而**不在于给出融合性能结论**。

## 2. 输入与输出

### 2.1 雷达输入

雷达侧输入根目录固定为：

- `mmradar/resources/fusion_sessions/<session_id>/radar/`

其中至少包含：

- `session_meta.json`
- `radar_frames.jsonl`
- `frames/frame_000000.jpg`
- `final_res.jpg`

如果是通过 Qt 上位机离线成像导出，上述文件来自 `sar_bp_1d` 的快照导出流程。

如果当前没有真实同步采样样本，也允许通过：

- `mmradar/tools/fusion/generate_demo_radar_session.py`

先生成一套**接口演示会话**。这类会话只用于验证融合链路，不代表真实配对数据。

### 2.2 视觉输入

视觉侧继续沿用已经固定的输出契约：

- `predictions.jsonl`
- `overlay.mp4`

字段定义见：

- `vision_uav/docs/RESULT_SCHEMA.md`

### 2.3 融合输出

融合输出根目录固定为：

- `mmradar/resources/fusion_sessions/<session_id>/fusion/`

本轮固定生成：

- `aligned_pairs.jsonl`
- `fusion_summary.json`
- `fusion_review.csv`
- `fusion_demo.mp4`

## 3. 核心流程

### 3.1 时间对齐

本轮只做最近邻时间对齐：

- 对齐字段：`timestamp_ms`
- 最大允许时间差：`150 ms`
- 超过阈值的样本直接丢弃，不参与融合统计

### 3.2 决策级状态判定

本轮不做外参标定，也不做空间坐标映射，只做决策级融合。

视觉正例规则：

- 当前帧中存在任一检测框，其 `confidence >= 0.45`

雷达正例规则：

- 读取当前 BP 快照灰度图
- 取图像最大灰度值并归一化为 `radar_score`
- 当 `radar_score >= 0.60` 时，判为雷达正例

对齐后每条样本只会落入四类之一：

- `agree_positive`
- `vision_only`
- `radar_only`
- `agree_negative`

## 4. 当前本地演示样例

为了在没有真实同步样本的情况下验证整条链路，本轮生成并跑通了一套本地演示会话：

- 会话目录：`mmradar/resources/fusion_sessions/demo_20190925_111757_1_10/`
- 视觉输入：
  - `vision_uav/runs/backup/20260415_a800_formal/stage2_eval_infer_export/extracted/stage2_eval_infer_export/infer_1_anti_uav_rgb_yolo26s_a800_b643_20190925_111757_1_10/predictions.jsonl`
  - `vision_uav/runs/backup/20260415_a800_formal/stage2_eval_infer_export/extracted/stage2_eval_infer_export/infer_1_anti_uav_rgb_yolo26s_a800_b643_20190925_111757_1_10/overlay.mp4`
- 雷达演示输入：
  - `radar/radar_frames.jsonl`
  - `radar/session_meta.json`
  - `radar/frames/*.jpg`
- 融合输出：
  - `fusion/aligned_pairs.jsonl`
  - `fusion/fusion_summary.json`
  - `fusion/fusion_review.csv`
  - `fusion/fusion_demo.mp4`

本轮演示结果摘要如下：

| 项目 | 数值 |
| --- | ---: |
| aligned_pair_count | 348 |
| discarded_pair_count | 0 |
| agree_positive | 63 |
| vision_only | 60 |
| radar_only | 112 |
| agree_negative | 113 |

这组数字只说明：

- 时间对齐逻辑正常；
- 四类状态都能被稳定判定；
- 融合视频和人工复核表可以生成。

它**不能**说明真实雷达和真实视频之间的融合效果。

## 5. 脚本入口

本轮新增的主要脚本有两个：

- `mmradar/tools/fusion/generate_demo_radar_session.py`
  - 作用：在没有真实同步雷达会话时，基于视觉时间轴生成一套演示用雷达会话
- `mmradar/tools/fusion/fuse_offline_session.py`
  - 作用：读取雷达 JSONL、视觉 JSONL 和视觉 overlay 视频，生成离线融合结果

## 6. 当前限制

必须明确当前限制，避免把 MVP 演示误写成完整融合结果：

- 没有真实的雷达+视频同步采集样本。
- 没有做相机与雷达之间的外参标定。
- 没有做坐标级映射或目标框级空间融合。
- 雷达侧当前输出的是 BP 快照和几何元数据，而不是目标框。
- 当前演示中的雷达会话可以是“真实导出”也可以是“接口演示生成”，两者都不能直接用于性能论文结论。

## 7. 下一步建议

在当前 MVP 基础上，后续最值得推进的顺序是：

1. 获取真实的雷达+视频同步样本。
2. 把当前 `timestamp_ms` 对齐从“最近邻”升级为“同步采样时间戳”。
3. 为雷达侧增加更稳定的目标级分数或候选框输出。
4. 再进入外参标定和空间级融合。

在这几步之前，不建议把当前演示结果包装成“完整融合性能”。
