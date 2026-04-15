# VISION_RUNBOOK

## 目标

先把“地面摄像头看低空无人机”的离线检测链跑通，独立于 `mmradar/`。

## 工作区结构

- `configs/`：环境、数据集、训练、推理、导出配置
- `docs/`：运行说明、数据集说明、结果契约、论文笔记
- `scripts/`：环境检查、数据转换、训练、评估、推理、导出
- `data/`：原始数据集和转换后数据，默认不入 Git
- `runs/`：训练、评估、推理输出，默认不入 Git
- `weights/`：本地模型权重缓存，默认不入 Git
- `cache/`：临时缓存，默认不入 Git

## 环境基线

- 操作系统：Windows
- Python 管理：`conda`
- 训练框架：CUDA 版 `PyTorch`
- 检测框架：`ultralytics`
- 导出与验证：`onnx`、`onnxruntime`

## 环境创建

在仓库根执行：

```powershell
conda env create -f vision_uav/configs/conda-env.yaml
conda activate vision-uav
python vision_uav/scripts/check_env.py --smoke-model yolo26n.pt
```

如果 `yolo26n.pt` 在当前 `ultralytics` 版本中无法加载，再退回：

```powershell
python vision_uav/scripts/check_env.py --smoke-model yolo11n.pt
```

## 第一阶段完整顺序

1. 建环境并执行 `check_env.py`。
2. 下载并解压 `Anti-UAV`，只准备 RGB 可见光数据。
3. 执行 `prepare_anti_uav.py` 生成 YOLO detect 数据集。
4. 执行 1 epoch 冒烟训练，确认数据链和训练命令无误。
5. 执行正式训练，产出 `best.pt`。
6. 执行离线视频推理，生成 `overlay.mp4` 和 `predictions.jsonl`。
7. 导出 ONNX，并用 `onnxruntime` 做一次最小推理验证。

## 当前约束

- 第一阶段只做检测，不做多目标跟踪。
- 主训练集只用 `Anti-UAV` RGB，不混入 `VisDrone/UAVDT`。
- `Drone-vs-Bird` 只做硬负样本评估，不并入主训练集。
- 默认按视频序列切分数据，禁止按帧随机切分。
