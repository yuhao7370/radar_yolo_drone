# mmradar 数据文件格式说明

这份文档只描述当前仓库里已经能从源码验证到的两类数据文件：

- `sar_*.bin`
- `clean.bin`

对应实现入口：

- 原始采样接收与落盘：`projects/host_qt/sar_tcp/mainwindow.cpp`
- 数据清洗：`projects/host_qt/sar_tcp/sar_data_cleaner.cpp`
- 成像读取：`projects/host_qt/sar_tcp/sar_bp_1d.cpp`

## 1. 数据链路总览

```text
板端 DMA/TCP 推送原始采样
-> 上位机直接落盘为 sar_*.bin
-> sar_data_cleaner 读取 sar_*.bin
-> 识别 trip / 补齐 / 重排四通道
-> 输出 clean.bin
-> sar_bp_1d 读取 clean.bin 成像
```

## 2. `sar_*.bin` 格式

### 2.1 文件性质

- `sar_*.bin` 是上位机在采集态下直接把 TCP 收到的字节流顺序写入文件后的结果。
- 文件中没有额外文件头，也没有单独的包级元数据。
- 可以把它理解为“原始 16 位采样字序列的直接拼接结果”。

### 2.2 基本单元

- 按当前代码逻辑，原始数据按小端序 `uint16` 解释。
- 每个 16 位字包含：
  - `bit0`
    - 采样边界辅助标记
  - `bit1`
    - mux / trip 边界辅助标记
  - `bit15..2`
    - 原始采样值

上位机在线观测时，恢复采样值的方式是：

```text
sample = (word & 0xFFFC) >> 2
```

也就是说，当前实现把高 14 位视为有效幅值。

### 2.3 在当前代码中的使用方式

在 `mainwindow.cpp` 的观测逻辑中：

- `bit0` 用于检查分组边界是否稳定，理想情况下相邻标记间隔是 4 个 `uint16`
- `bit1` 用于辅助寻找 trip 起点与通道同步
- 解析后得到 4 路通道数据，再进行在线 FFT 观测

在 `sar_data_cleaner.cpp` 的清洗逻辑中：

- 主要依赖 `bit1` 的翻转去测量 trip 长度
- 然后依据标记与间距关系补齐漏掉的 trip
- 最终重排成固定结构的 `clean.bin`

### 2.4 当前可以确认的结构边界

当前能确认的是：

- 文件按 `uint16` 连续排列
- 低两位是控制/辅助位
- 高 14 位是采样值
- 文件本身不带显式头部

当前不能仅凭仓库保证的事情：

- 单个 TCP 包在文件中的边界位置
- 板端每次 DMA 发送块与文件内部偏移的严格对应关系

因为 `sar_*.bin` 是 TCP 字节流直接落盘，包边界天然不会保存在文件里。

## 3. `clean.bin` 格式

### 3.1 文件头

文件开头 4 字节：

```text
offset 0x00: int32 trip_len
```

含义：

- `trip_len` 是清洗后单通道单个 trip 的采样点数

当前本地样本 `resources/data/clean.bin` 可解析出：

- `trip_len = 3000`

### 3.2 文件主体布局

`clean.bin` 在文件头之后按 trip 顺序排列。

每个 trip 固定包含 4 个通道块，顺序来自 `sar_data_cleaner.cpp` 中的注释：

- 通道 1：`1a`
- 通道 2：`1b`
- 通道 3：`2a`
- 通道 4：`2b`

每个通道块格式为：

```text
<uint64 now_pt><uint16 samples[trip_len]>
```

所以：

- 单个通道块大小 = `8 + 2 * trip_len` 字节
- 单个 trip 大小 = `4 * (8 + 2 * trip_len)` 字节

如果 `trip_len = 3000`，则：

- 单通道块大小 = `6008` 字节
- 单 trip 大小 = `24032` 字节

### 3.3 `now_pt` 的含义

`now_pt` 是清洗阶段记录下来的原始位置索引。

写入方式来自 `sar_data_cleaner.cpp`：

- 在输出每个通道块前，把当前位置 `now_pt / 4` 写成 `uint64`

当前本地样本 `clean.bin` 中：

- 第一个通道块的 `now_pt = 48`

### 3.4 trip 数量计算

给定文件大小 `file_size`，trip 数量可按下面方式计算：

```text
trip_len = read_int32_le(file[0:4])
channel_block_size = 8 + 2 * trip_len
trip_size = 4 * channel_block_size
trip_count = (file_size - 4) / trip_size
```

当前本地样本 `resources/data/clean.bin` 可计算出：

- `trip_count ≈ 3198`

## 4. 成像程序如何读取 `clean.bin`

`sar_bp_1d.cpp` 的读取方式可以概括为：

1. 先读文件头 `trip_len`
2. 计算单通道块大小 `8 + 2 * trip_len`
3. 计算 `trip_count`
4. 每次循环：
   - 读取一个通道块的 `now_pt`
   - 读取对应 `trip_len` 个 `uint16` 采样
   - 跳过后面 3 个通道块
5. 对读取到的这一路数据做：
   - 去均值/减噪声
   - 截取有效区间
   - 加窗
   - FFT
   - BP 成像

从当前实现看，`sar_bp_1d` 主要消费的是四通道中的其中一路固定布局数据，而不是每次同时把 4 路都用于成像。

## 5. 输入输出关系

### 5.1 采集阶段

```text
输入:
  板端 TCP 推送的原始 16 位采样字流

输出:
  sar_*.bin
```

### 5.2 清洗阶段

```text
输入:
  sar_*.bin

处理:
  识别 trip 长度
  找 trip 边界
  补齐缺失 trip
  重排成固定四通道结构

输出:
  clean.bin
```

### 5.3 成像阶段

```text
输入:
  clean.bin
  sar_noise_500M.bin
  几何与成像参数

输出:
  BP 成像结果
  在线显示图像
```

## 6. 当前应如何使用这份说明

如果后续需要复现实验链：

- 用 `sar_*.bin` 验证原始采样大小、控制位分布和 trip 粗略长度
- 用 `clean.bin` 验证 `trip_len`、`trip_count` 和 `now_pt` 布局
- 让文档说明、脚本输出和成像参数三者保持一致

这也是后续 `tools/radar/inspect_raw_capture.py` 和 `inspect_clean_capture.py` 的直接依据。
