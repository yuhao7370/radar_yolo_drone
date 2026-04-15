# HARD_NEGATIVE_ROUND2

## 1. 本轮目标

这一轮的目标不是继续堆大模型，而是在现有 `YOLO26s` 正式基线之上做一次更贴近场景的多源 hard negative 优化，重点回答三个问题：

1. 公开鸟类、纯天空、复杂背景负样本补进来后，误检还能不能继续压下去。
2. 用“误检挖掘 + 轻量补训”能不能在不明显伤主任务的前提下进一步优化模型。
3. 如果做不到，下一轮应该继续堆 detector，还是应该切到两阶段 bird rejector。

## 2. 数据池与套件实际落地情况

本轮实际接入的数据源如下：

- `FBD-SV-2024`
- `Distant Bird Detection for Safe Drone Flight`
- `Anti-UAV300` 空标签帧

最终落地的评估套件与候选池规模如下：

| 名称 | 用途 | 实际规模 |
| --- | --- | ---: |
| `bird_public_train_pool` | 鸟类训练候选池 | 1500 张 |
| `bird_eval_public` | 公开鸟类评估套件 | 336 张 |
| `pure_sky_pool` | 纯天空候选池 | 46 张 |
| `sky_eval` | 纯天空评估套件 | 35 张 |
| `clutter_background_pool` | 复杂背景候选池 | 122 张 |
| `clutter_eval` | 复杂背景评估套件 | 18 张 |

需要明确的一点是：`Anti-UAV300` 空标签帧中真正满足本轮阈值规则的复杂背景样本比预期少很多，因此这一轮虽然流程完整，但数据供给并没有达到最初设想的 `2000 / 400` 级别。

## 3. 基线误检评估

在当前正式基线 `best.pt` 上，对 `bird_eval_public / sky_eval / clutter_eval` 进行了阈值扫描，阈值集合固定为：

- `0.35, 0.40, 0.45, 0.50, 0.55`

评估结果表明：

- `bird_eval_public` 在 `0.45` 下仅有 `4` 帧误检。
- `sky_eval` 在 `0.45` 下误检为 `0`。
- `clutter_eval` 在 `0.45` 下误检为 `0`。

这说明当前正式基线在公开 hard negative 套件上的误检已经不算高，尤其是纯天空与复杂背景两套件并不是主要瓶颈。

## 4. 误检挖掘与 hn_v2 构建结果

本轮没有把所有候选负样本直接灌进训练，而是先以 `conf = 0.20` 跑一遍 detector，只保留模型自己会报框的样本，再做 perceptual hash 去重。

实际挖掘结果如下：

| 类别 | 目标配额 | 实际挖到 | 最终用于 `hn_v2` |
| --- | ---: | ---: | ---: |
| `bird` | 2500 | 59 | 59 |
| `pure_sky` | 1000 | 5 | 5 |
| `clutter` | 1500 | 2 | 2 |
| 合计 | 5000 | 66 | 66 |

这个结果本身就说明了一个现实问题：

- 当前公开 hard negative 数据对这版正式模型的“诱骗性”已经不强。
- 真正会让模型报框的高价值负样本数量远小于原先设想。
- 如果继续机械扩大配额，只会让训练目标和真实难样本分布脱节。

## 5. A800 补训结果

本轮在 A800 上从当前正式基线 `best.pt` 出发继续微调，配置为：

- `imgsz = 960`
- `batch = 64`
- `epochs = 10`
- `patience = 3`
- `workers = 16`
- `cache = ram`

实际训练行为：

- 训练 run：`vision_uav/runs/train/anti_uav_rgb_yolo26s_a800_b643_hn_v26/`
- `EarlyStopping` 触发
- 最佳结果出现在 `epoch 1`
- 总共实际运行到 `epoch 4`

最佳验证结果（对应 `epoch 1`）为：

| 指标 | 数值 |
| --- | ---: |
| Precision | 0.97658 |
| Recall | 0.97590 |
| mAP50 | 0.99238 |
| mAP50-95 | 0.66358 |

对比上一版正式基线可以看到：

- `val recall` 基本持平
- 但 `val mAP50-95` 从约 `0.686` 降到了约 `0.664`

也就是说，这轮补训并没有在主任务上带来正收益。

## 6. Post-train 阈值网格与最终结论

补训后，又在 `val/test` 与三套 hard negative 上重新扫了一遍阈值。关键结论是：

### 6.1 Hard negative 侧

在 `0.35` 阈值下：

- `bird_eval_public frame_false_positive_rate = 0.00595`
- `sky_eval frame_false_positive_rate = 0.0`
- `clutter_eval frame_false_positive_rate = 0.0`

也就是说，误检确实进一步压低了。

### 6.2 主任务侧

但同时，`Anti-UAV test` 的结果明显退化：

| 阈值 | Test Recall | Test mAP50-95 |
| --- | ---: | ---: |
| 0.35 | 0.84409 | 0.47980 |
| 0.40 | 0.83646 | 0.47611 |
| 0.45 | 0.82820 | 0.47243 |
| 0.50 | 0.81969 | 0.46812 |
| 0.55 | 0.80906 | 0.46325 |

而本轮验收线要求：

- `test recall >= 0.88`
- `test mAP50-95 >= 0.507`
- `test recall` 相比基线下降不超过 `0.02`

所以最终结论是：

- `selected_threshold_v2 = null`
- 这轮优化**不通过**

## 7. 为什么这轮失败

这轮失败不是因为链路没跑通，而是因为结果本身说明了当前方法边界：

1. 公开 hard negative 侧的误检已经不高，继续压它会很容易牺牲主任务 recall。
2. 当前挖出来的高价值难样本总量只有 `66` 张，规模太小，不足以支撑一次稳定的 detector 微调收益。
3. 继续沿着“同一个 detector 上不断补 hard negative 再微调”的路线，很可能只会持续把 decision boundary 收紧，导致 UAV 主任务召回继续下降。

## 8. 下一步建议

下一轮不建议继续在同一路线上加 epoch 或换更大 detector，而是应该转向：

1. 保留当前原始正式基线 `anti_uav_rgb_yolo26s_a800_b643/weights/best.pt` 作为现阶段部署候选。
2. 把 `bird_eval_public` 和未来申请到的 `Drone-vs-Bird` 作为二阶段拒识器的数据基础。
3. 进入 `bird rejector` 两阶段方案：
   - 第一阶段仍由 UAV detector 给候选框
   - 第二阶段专门做 bird-vs-uav 拒识

换句话说，这一轮最大的价值不是“又得到一版更好的 detector”，而是**验证了当前单阶段 detector 数据型优化已经接近收益上限**。
