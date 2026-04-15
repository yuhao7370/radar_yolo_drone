# INITIAL_RESULTS

## 时间

2026-04-15

## 已完成内容

1. 独立视觉工作区 `vision_uav/` 已建立。
2. `Anti-UAV` RGB 到 YOLO detect 的转换脚本已落地。
3. `YOLO26` 训练、评估、离线推理、ONNX 导出入口已落地。
4. `predictions.jsonl` 的结果契约已固定。
5. 独立 `conda` 环境 `vision-uav` 已创建完成。
6. `Anti-UAV300.zip` 已下载并解压到 `vision_uav/data/raw/anti_uav/Anti-UAV300/`。
7. 冒烟数据集已从真实数据成功生成。
8. `YOLO26n` 1 epoch 冒烟训练已跑通。
9. 完整 `Anti-UAV300` 检测数据集已展开为 YOLO detect 目录。

## 本机环境现状

以仓库原有 Python 环境执行探测，结果如下：

- GPU：`NVIDIA GeForce RTX 4070 Laptop GPU`
- 现有 Python：`3.11.7`
- `torch`：`2.6.0+cpu`
- `torch.cuda.is_available()`：`False`
- `ultralytics`：`8.3.163`
- `cv2`：`4.10.0`
- `onnx`：`1.19.1`
- `onnxruntime`：`1.16.3`

结论：当前默认环境只能做 CPU 推理验证，不能作为正式训练环境，必须切到独立 CUDA conda 环境。

## 独立训练环境验证

以 `C:\Users\27377\anaconda3\envs\vision-uav\python.exe` 执行 `check_env.py --smoke-model yolo26n.pt`，结果如下：

- Python：`3.11.15`
- `torch`：`2.5.1`
- `ultralytics`：`8.4.37`
- `cv2`：`4.13.0`
- `onnx`：`1.21.0`
- `onnxruntime`：`1.24.4`
- `torch.cuda.is_available()`：`True`
- GPU：`NVIDIA GeForce RTX 4070 Laptop GPU`
- `yolo26n.pt`：可正常加载

结论：`vision-uav` 环境已经满足第一阶段的 CUDA 训练和模型加载前提。

## 数据落地结果

- 数据源：Hugging Face 镜像 `Anti-UAV300.zip`
- 压缩包大小：`7,937,237,349` 字节
- 解压位置：`vision_uav/data/raw/anti_uav/Anti-UAV300/`
- 真实目录结构：`train/val/test/<sequence>/visible.mp4 + visible.json`
- Windows 兼容处理：已创建 `C:\vision_uav_data` junction，供 `Ultralytics` 避开中文路径问题
- 完整正式数据集转换统计：
  - `train`：`160` 个序列，`29,924` 帧，`28,470` 个正样本帧，`1,454` 个空标签背景帧
  - `val`：`67` 个序列，`6,208` 帧，`5,850` 个正样本帧，`358` 个空标签背景帧
  - `test`：`91` 个序列，`8,547` 帧，`7,992` 个正样本帧，`555` 个空标签背景帧

## 冒烟数据集结果

使用 `vision_uav/configs/anti_uav_prepare_smoke.yaml` 从真实数据生成：

- `train`：`8` 个序列，`988` 帧，`949` 个正样本帧，`39` 个空标签背景帧
- `val`：`2` 个序列，`168` 帧，`168` 个正样本帧
- `test`：`2` 个序列，`113` 帧，`95` 个正样本帧，`18` 个空标签背景帧

## 冒烟训练结果

使用 `YOLO26n`、`imgsz=640`、`batch=8`、`epochs=1` 在 CUDA 环境上完成训练：

- 训练输出目录：`vision_uav/runs/train/anti_uav_rgb_yolo26n_smoke3/`
- 权重文件：`best.pt`、`last.pt`
- 验证指标：
  - `precision = 0.786`
  - `recall = 0.745`
  - `mAP50 = 0.835`
  - `mAP50-95 = 0.311`

这组结果仅用于验证“数据转换 + dataloader + CUDA 训练链”已打通，不代表正式基线性能。

## 已知环境问题

- `conda run -n vision-uav ...` 在当前 Windows GBK 控制台下会触发一次 `UnicodeEncodeError` 的 Conda 输出编码问题。
- 直接使用环境内的 `python.exe` 可以正常执行，不影响训练脚本本身。

## 当前已验证的脚本状态

已通过静态或启动级验证：

- `scripts/check_env.py`
- `scripts/prepare_anti_uav.py`
- `scripts/train.py`
- `scripts/evaluate.py`
- `scripts/infer_video.py`
- `scripts/export_onnx.py`

验证方式：

- `python -m py_compile`
- `python <script> --help`

## 当前未完成项

以下结果还没有真实跑出：

1. `YOLO26s` 正式训练指标
2. `best.pt -> model.onnx` 的真实导出产物
3. `Drone-vs-Bird` 上的鸟类误检率

## 下一步最短路径

1. 在 `vision-uav` 环境中从 `train_baseline.yaml` 开始跑正式训练。
2. 用 `infer_video.py` 对真实测试视频导出 `overlay.mp4 + predictions.jsonl`。
3. 用 `export_onnx.py` 导出第一版 `model.onnx` 并做 `onnxruntime` 验证。
4. 引入 `Drone-vs-Bird` 评估鸟类误检率，再决定要不要补第二阶段分类头。
