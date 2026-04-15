# RESULT_SCHEMA

`predictions.jsonl` 是未来视觉模块与 `mmradar` 对接的唯一结构化输出。

## 顶层结构

文件按行存储 JSON，每一行对应一帧：

```json
{
  "source_id": "anti_uav_demo",
  "frame_id": 42,
  "timestamp_ms": 1400.0,
  "width": 1920,
  "height": 1080,
  "detections": [
    {
      "bbox_xyxy": [801.0, 312.0, 845.0, 356.0],
      "class_id": 0,
      "class_name": "uav",
      "confidence": 0.91
    }
  ]
}
```

## 字段约定

- `source_id`：输入源标识，来自推理配置。
- `frame_id`：从 0 开始递增的帧编号。
- `timestamp_ms`：毫秒时间戳。视频按视频 FPS 推导，图片目录按配置 FPS 推导，摄像头按运行时采样时间推导。
- `width` / `height`：原始帧尺寸。
- `detections`：当前帧的检测结果数组。允许为空数组。

## 检测项字段

- `bbox_xyxy`：左上和右下角坐标，顺序为 `[x1, y1, x2, y2]`。
- `class_id`：当前阶段固定为 `0`。
- `class_name`：当前阶段固定为 `uav`。
- `confidence`：检测置信度，范围 `[0, 1]`。

## 当前范围

- 第一阶段只输出检测框，不输出跟踪 ID。
- 不输出分割掩码、关键点或融合结果。
- 未来如果加入跟踪，新增字段应保持向后兼容，不能破坏上述字段。
