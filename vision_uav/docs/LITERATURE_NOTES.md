# LITERATURE_NOTES

## 当前文献阅读的作用

这份文档不追求写成综述论文，而是服务于当前这条工程主线：先把“低空无人机视觉检测 + hard negative 优化”做成一条可复现、可解释、可继续迭代的链路。

因此，本文件只保留三类高价值信息：

1. 为什么当前主训练集选 `Anti-UAV`
2. 为什么 hard negative 要重点看鸟类、纯天空和复杂背景
3. 哪些论文或 benchmark 会直接影响这一轮的数据与训练决策

## 1. 反无人机主数据：Anti-UAV

### 1.1 资料入口

- 官方数据页：<https://anti-uav.github.io/dataset/>
- 官方仓库：<https://github.com/ucas-vg/Anti-UAV>

### 1.2 对当前工程最有用的结论

1. 这是反无人机场景的专门 benchmark，不是泛航拍检测数据集。
2. 目标普遍很小、背景复杂、成像距离远，更贴近你当前项目的地面反无人机场景。
3. 虽然官方同时提供 RGB / IR，但当前工程分支只做 RGB 检测，不混多模态。

### 1.3 当前用法

- 继续作为 UAV 主训练集和 `val/test` 主评估基准
- 不把它的空标签帧简单当“背景噪声”，而是进一步拆成 `pure_sky` 和 `clutter_background`

## 2. 鸟类误检相关数据

### 2.1 FBD-SV-2024

- Scientific Data 论文：<https://www.nature.com/articles/s41597-025-04872-6>
- arXiv：<https://arxiv.org/abs/2409.00317>

对当前工程最有用的结论：

1. 它是公开可用的鸟类视频数据，适合直接作为第一手 bird hard negative。
2. 它的价值在于“先把鸟类误检这个问题具体化”，而不是替代主 UAV 训练集。
3. 当前工程已经接入该数据源，并已用于第一轮鸟类 hard negative 阈值搜索。

### 2.2 Distant Bird Detection for Safe Drone Flight and Its Dataset

- 数据仓库：<https://github.com/kakitamedia/drone_dataset>
- 论文：<https://www.mva-org.jp/Proceedings/2021/papers/O1-1-3.pdf>

对当前工程最有用的结论：

1. 这是高分辨率、远距离鸟类检测数据，对“鸟机远距离混淆”更有针对性。
2. 它不是视频数据，而是图像数据，因此更适合补充 bird hard negative 的多样性，而不是替代视频类负样本。
3. 本轮只使用公开子集，不下载全量 67GB 图像。

### 2.3 Drone-vs-Bird Challenge

- 官方仓库：<https://github.com/wosdetc/challenge>
- Challenge 综述论文：<https://www.mdpi.com/1424-8220/21/8/2824>
- 相关 benchmark 汇总：<https://github.com/KostadinovShalon/UAVDetectionTrackingBenchmark>

对当前工程最有用的结论：

1. 它仍然是最贴近“鸟 vs 无人机混淆”的 held-out 评估候选。
2. 但它的数据获取存在申请门槛，因此不适合作为当前这一轮优化的启动依赖。
3. 当前正确策略是“并行申请 + 到手后做 held-out 评估”，而不是卡住主流程等它。

## 3. 方法参考：Hard Negative Mining

### 3.1 OHEM

- 论文：Training Region-Based Object Detectors with Online Hard Example Mining
- 链接：<https://www.cv-foundation.org/openaccess/content_cvpr_2016/papers/Shrivastava_Training_Region-Based_Object_CVPR_2016_paper.pdf>

对当前工程最有用的结论：

1. hard negative 不是“随便多加背景图”，而是优先加入模型自己容易误报的样本。
2. 当前分支最合理的做法不是重新搭 head，而是先做误检挖掘，再构建 `hn_v2` 数据集继续微调。
3. 这个思路和你当前的目标完全一致：优先压误检，同时尽量不伤主任务 recall。

## 4. 反无人机场景综述

### 4.1 Anti-UAV 综述

- 论文：Securing the Skies: A Comprehensive Survey on Anti-UAV Methods Benchmarking
- 链接：<https://arxiv.org/abs/2504.11967>

对当前工程最有用的结论：

1. 当前公开反无人机研究仍然高度依赖“检测、跟踪、融合”分阶段推进。
2. 视觉链路先独立做稳，再和雷达做接口级融合，是符合公开研究路径的。
3. 当前项目这一轮应该继续做“数据型优化”，而不是过早切到更复杂的结构。

## 5. 当前文献边界

这轮不做的事：

- 不追新结构
- 不追更大主模型
- 不做二阶段 bird rejector
- 不做部署压缩

只有在以下情况出现时，下一轮才考虑切策略：

1. 多源 hard negative 优化后，整体误检率仍然压不进 `3%~5%`
2. `Anti-UAV test recall` 为了压误检而明显受损
3. `Drone-vs-Bird` held-out 评估到手后，鸟类误检仍明显不可接受
