# mmradar 复现实验基线

这份文档固定当前仓库已经验证过的一组基准参数，并给出最小检查命令。

## 1. 当前基准参数

### 网络

- `listen_port = 2829`
- 板端 IP：`192.168.1.11`
- 上位机 IP：`192.168.1.2`

### 路径

- `data_dir = resources/data`
- `noise_file = resources/calibration/sar_noise_500M.bin`

### 采集

- `target_size_kb = 75000`

### 成像

- `x/y/w/h = -2 / 2.5 / 5 / 8`
- `grid = 500 x 800`
- `speed = 0.12`
- `sar_height = 0.872`
- `zero_times = 10`
- `gap_h/gap_t = 15 / 50`
- `contrast_level = 6764`

## 2. 当前本地样本

当前工作区中已经存在并可直接检查的本地样本：

- 原始采样：`resources/data/sar_3.bin`
- 清洗结果：`resources/data/clean.bin`
- 噪声标定：`resources/calibration/sar_noise_500M.bin`

说明：

- 这些大样本默认不纳入 Git。
- 但脚本和文档默认按当前工作区已有样本进行复现与检查。

## 3. 最小检查命令

以下命令默认在 `mmradar/` 根目录执行。

### 检查原始采样

```bash
python tools/radar/inspect_raw_capture.py resources/data/sar_3.bin
```

建议关注输出：

- 文件大小
- 16 位样本数
- `bit0` 标记统计
- `bit1` 标记统计
- 基于现有 cleaner 逻辑估算出的 trip 长度

### 检查清洗结果

```bash
python tools/radar/inspect_clean_capture.py resources/data/clean.bin
```

建议关注输出：

- `trip_len`
- `trip_count`
- 首个 `now_pt`
- 单通道块大小
- 单 trip 大小
- 首个通道块的采样预览

## 4. 预期结果

对当前本地 `clean.bin`，预期至少能看到：

- `trip_len = 3000`
- `trip_count ≈ 3198`
- 首个 `now_pt = 48`

对当前本地 `sar_3.bin`，预期能看到：

- 文件大小约 `76.8 MB`
- 文件可按 `uint16` 连续解析
- 低两位标记位存在明显分布

## 5. 采样 -> 清洗 -> 成像的固定关系

```text
1. 板端推流
2. 上位机保存 sar_*.bin
3. cleaner 读取 sar_*.bin，输出 clean.bin
4. imager 读取 clean.bin + 噪声文件，执行 BP 成像
```

当前复现实验的目标不是新增能力，而是确保这条链路在本地稳定可解释、可检查、可重复。
