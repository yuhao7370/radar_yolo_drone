# mmradar 最小运行说明

这份说明只覆盖当前仓库已经落地的雷达链路：

- 板端采样
- TCP 传输
- 上位机接收
- 原始数据保存
- 数据清洗
- BP 成像

不覆盖视觉识别、摄像头接入和雷达视觉融合。

## 1. 当前网络参数

### 板端

- 板端 IP：`192.168.1.11`
- 掩码：`255.255.255.0`
- 网关：`192.168.1.11`

### 上位机

- 上位机目标 IP：`192.168.1.2`
- 监听端口：`2829`

说明：

- 当前板端程序会主动连接上位机 `192.168.1.2:2829`。
- 当前上位机程序会监听本地 `2829` 端口，并通过 TCP 回写 `start` / `stop` 控制词。

## 2. 当前数据与标定路径

这些路径以 `mmradar/` 根目录为基准：

- 数据目录：`resources/data`
- 噪声文件：`resources/calibration/sar_noise_500M.bin`
- 原始采样文件命名：`resources/data/sar_*.bin`
- 清洗输出：`resources/data/clean.bin`

当前基准配置模板见：

- `config/sar_tcp.ini`

## 3. 一次完整采集到成像的操作顺序

### 步骤 1：准备网络

- 把上位机网卡配置到与板端同网段，确保上位机地址为 `192.168.1.2`。
- 确认板端使用当前程序配置，板端 IP 为 `192.168.1.11`。
- 确认 `2829` 端口未被其他程序占用。

### 步骤 2：准备运行目录

- 确认 `resources/data/` 存在并可写。
- 确认 `resources/calibration/sar_noise_500M.bin` 存在。
- 确认上位机将使用 `config/sar_tcp.ini` 中的路径与参数。

### 步骤 3：启动上位机

- 启动 `projects/host_qt/sar_tcp` 对应的 Qt 程序。
- 程序启动后应监听本地 `2829` 端口。
- 如果板端已在线，板端会主动发起 TCP 连接。

### 步骤 4：执行采集

- 在上位机点击“开始采集数据”。
- 上位机会向板端发送 `start`。
- 板端开始采样并通过 TCP 推送数据。
- 上位机把收到的数据落盘为 `sar_*.bin`。
- 达到目标采样大小后，上位机停止采集并关闭文件。

### 步骤 5：执行清洗

- 在上位机点击“开始清洗”。
- 清洗程序读取刚采到的 `sar_*.bin`。
- 程序识别 trip 边界、补齐丢失 trip，并输出 `clean.bin`。

### 步骤 6：执行成像

- 在上位机点击“开始成像”。
- 成像程序读取 `clean.bin` 和噪声标定文件。
- 程序按当前参数执行 BP 成像，并在界面上显示结果。
- 如需调对比度，可在成像完成后再用界面滑块调整。

## 4. 当前基准参数

当前仓库里已经验证过的一组基准参数如下：

- `listen_port = 2829`
- `target_size_kb = 75000`
- `x/y/w/h = -2 / 2.5 / 5 / 8`
- `grid = 500 x 800`
- `speed = 0.12`
- `sar_height = 0.872`
- `contrast_level = 6764`

## 5. 目录分层约定

为了后续接手方便，当前仓库按下面的理解阅读：

- `projects/`
  - 主工程源码与设计文件
- `resources/`
  - 数据、标定、资料库
- `docs/`
  - 接手说明、运行说明、文件格式说明、复现实验说明
- `config/`
  - 上位机运行参数模板
- `tools/`
  - 与实验链复现相关的小工具
- `archives/`
  - 历史归档包，不作为当前主入口

## 6. 哪些目录不是主源码

以下内容不应作为当前主实现阅读入口：

- `projects/host_qt/sar_tcp/build/`
- `projects/fpga_pspl/Miz_sys/.venv/`
- `projects/fpga_pspl/Miz_sys/Miz_sys.cache/`
- `projects/fpga_pspl/Miz_sys/Miz_sys.ip_user_files/`
- `projects/fpga_pspl/Miz_sys/Miz_sys.runs/`
- `projects/fpga_pspl/Miz_sys/Miz_sys.sim/`
- `projects/hardware_pcb/MZ7XB/History/`
- `projects/hardware_pcb/MZ7XB/Project Logs for MZ7XB_Fun/`
- `projects/hardware_pcb/MZ7XB/Project Outputs for ZED/`
- `archives/`

这些目录主要是：

- 构建产物
- Vivado 生成目录
- 硬件会话/历史输出
- 历史打包备份

## 7. 当前主入口

如果只想抓主线，请按这个顺序看：

1. `PROJECT_BASELINE.md`
2. `docs/RUNBOOK.md`
3. `config/sar_tcp.ini`
4. `projects/host_qt/sar_tcp/`
5. `projects/fpga_pspl/Miz_sys/Miz_sys.sdk/PL2PS_DMA_Test/src/`
6. `projects/fpga_pspl/Miz_sys/Miz_sys.srcs/sources_1/`
