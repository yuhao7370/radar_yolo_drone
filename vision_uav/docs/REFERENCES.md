# REFERENCES

本文件固定记录 `vision_uav` 分支当前直接使用或明确参考的数据源与论文，后续写报告时优先从这里取引用，不再临时回忆。

## 1. 主训练数据与基准

### 1.1 Anti-UAV

- 名称：Anti-UAV Dataset / Anti-UAV Challenge
- 作用：当前 UAV 主训练集与 `val/test` 主评估基准
- 官方数据页：<https://anti-uav.github.io/dataset/>
- 官方仓库：<https://github.com/ucas-vg/Anti-UAV>
- 备注：本项目当前只使用 RGB 分支，不使用 IR 分支做训练

### 1.2 Anti-UAV 综述

- 标题：Securing the Skies: A Comprehensive Survey on Anti-UAV Methods Benchmarking
- 来源：CVPRW 2025 Anti-UAV Workshop
- 链接：<https://arxiv.org/abs/2504.11967>
- 作用：作为本项目反无人机场景、公开 benchmark 和方法边界的综述参考

## 2. 鸟类 Hard Negative 数据

### 2.1 FBD-SV-2024

- 标题：Flying Bird Dataset-Single Video 2024
- Scientific Data：<https://www.nature.com/articles/s41597-025-04872-6>
- arXiv：<https://arxiv.org/abs/2409.00317>
- 作用：当前公开鸟类 hard negative 的主来源之一
- 当前状态：已下载并接入本地

### 2.2 Distant Bird Detection for Safe Drone Flight and Its Dataset

- 论文：<https://www.mva-org.jp/Proceedings/2021/papers/O1-1-3.pdf>
- 数据仓库：<https://github.com/kakitamedia/drone_dataset>
- 作用：补充高分辨率、远距离、小目标鸟类负样本
- 当前状态：本轮直接接入公开子集

### 2.3 Drone-vs-Bird Challenge

- 官方仓库：<https://github.com/wosdetc/challenge>
- Challenge 综述论文：<https://www.mdpi.com/1424-8220/21/8/2824>
- 作用：作为更贴近“鸟机混淆”问题的 held-out 评估集
- 当前状态：并行申请中；到手后只做 held-out 评估，不直接并入本轮训练

## 3. 方法参考

### 3.1 OHEM

- 标题：Training Region-Based Object Detectors with Online Hard Example Mining
- 来源：CVPR 2016
- 链接：<https://www.cv-foundation.org/openaccess/content_cvpr_2016/papers/Shrivastava_Training_Region-Based_Object_CVPR_2016_paper.pdf>
- 作用：作为“先挖误检帧、再加入 hard negative”的经典方法参考

## 4. 本轮直接使用与仅参考的边界

本轮**直接使用**：

- Anti-UAV RGB
- FBD-SV-2024
- Distant Bird Detection 的公开子集

本轮**并行申请、尚未直接进入训练**：

- Drone-vs-Bird Challenge

本轮**只作方法或背景参考，不直接作为训练输入**：

- Anti-UAV 综述
- OHEM 经典论文
