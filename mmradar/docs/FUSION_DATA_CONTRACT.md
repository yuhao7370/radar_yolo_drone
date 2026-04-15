# FUSION_DATA_CONTRACT

当前融合 MVP 只定义离线接口，不定义实时协议。

## 1. 雷达导出接口

雷达导出根目录固定为：

- `mmradar/resources/fusion_sessions/<session_id>/radar/`

固定文件：

- `session_meta.json`
- `radar_frames.jsonl`
- `frames/frame_000000.jpg`
- `final_res.jpg`

### `session_meta.json`

最少包含：

- `session_id`
- `source_file`
- `trip_len`
- `trip_num`
- `snapshot_stride_trip`
- `img_x`
- `img_y`
- `img_w`
- `img_h`
- `grid_x`
- `grid_y`
- `sar_height`
- `speed`
- `export_mode`
- `note`

### `radar_frames.jsonl`

每行一个 JSON 对象，最少包含：

```json
{
  "session_id": "demo_session",
  "frame_id": 0,
  "trip_idx": 120,
  "now_pt": 48000,
  "timestamp_ms": 48.0,
  "sar_pos_x_m": 0.00576,
  "img_path": "frames/frame_000000.jpg",
  "img_x": -2.0,
  "img_y": 2.5,
  "img_w": 5.0,
  "img_h": 8.0,
  "grid_x": 500,
  "grid_y": 800,
  "sar_height": 0.872,
  "speed": 0.12
}
```

字段约定：

- `frame_id`：导出快照编号，从 `0` 递增
- `trip_idx`：当前快照对应的 trip 序号
- `now_pt`：来自 `clean.bin` 的原始位置索引
- `timestamp_ms`：固定按 `now_pt / 1000.0`
- `sar_pos_x_m`：固定按 `speed * now_pt / 1000000.0`
- `img_path`：相对于雷达导出根目录的相对路径

## 2. 视觉输入接口

视觉继续沿用：

- `predictions.jsonl`
- `overlay.mp4`

字段定义见：

- `vision_uav/docs/RESULT_SCHEMA.md`

融合 MVP 只消费以下字段：

- `source_id`
- `frame_id`
- `timestamp_ms`
- `detections[].confidence`

## 3. 融合输出接口

融合输出根目录固定为：

- `mmradar/resources/fusion_sessions/<session_id>/fusion/`

固定文件：

- `aligned_pairs.jsonl`
- `fusion_summary.json`
- `fusion_review.csv`
- `fusion_demo.mp4`

### `aligned_pairs.jsonl`

每条记录最少包含：

- `session_id`
- `vision_source_id`
- `vision_frame_id`
- `radar_frame_id`
- `vision_timestamp_ms`
- `radar_timestamp_ms`
- `time_delta_ms`
- `vision_top_confidence`
- `radar_score`
- `vision_positive`
- `radar_positive`
- `state`
- `radar_img_path`

### `fusion_summary.json`

最少包含：

- `session_id`
- `max_time_delta_ms`
- `vision_conf_threshold`
- `radar_score_threshold`
- `aligned_pair_count`
- `discarded_pair_count`
- `agree_positive`
- `vision_only`
- `radar_only`
- `agree_negative`

### `fusion_review.csv`

供人工复核使用，至少保留：

- `vision_frame_id`
- `radar_frame_id`
- `time_delta_ms`
- `vision_top_confidence`
- `radar_score`
- `state`

## 4. 当前限制

- 这套契约只支持离线时间对齐，不含外参标定。
- 雷达侧当前输出的是 BP 成像快照，不是目标框。
- 因此本轮融合只做决策级融合和可视化，不做空间级融合结论。
