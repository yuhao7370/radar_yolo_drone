# INITIAL_RESULTS

## 时间

2026-04-15

## 已完成内容

1. 独立视觉工作区 `vision_uav/` 已建立。
2. `Anti-UAV` RGB 到 YOLO detect 的转换脚本已落地。
3. `YOLO26` 训练、评估、离线推理、ONNX 导出入口已落地。
4. `predictions.jsonl` 的结果契约已固定。
5. 独立 `conda` 环境 `vision-uav` 已创建完成。

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

以下结果还没有真实跑出，因为当前工作区没有本地 `Anti-UAV` 原始数据，也还没有完成独立 CUDA 环境安装后的训练：

1. `Anti-UAV` 真实转换统计
2. `YOLO26n` 1 epoch 冒烟训练
3. `YOLO26s` 正式训练指标
4. `best.pt -> model.onnx` 的真实导出产物
5. `Drone-vs-Bird` 上的鸟类误检率

## 下一步最短路径

1. 下载并解压 `Anti-UAV` RGB 数据到 `vision_uav/data/raw/anti_uav/`。
2. 执行 `prepare_anti_uav.py` 生成训练集。
3. 在 `vision-uav` 环境中先跑 `train_smoke.yaml`，再跑 `train_baseline.yaml`。
4. 用 `infer_video.py` 和 `export_onnx.py` 产出第一版可消费结果。
