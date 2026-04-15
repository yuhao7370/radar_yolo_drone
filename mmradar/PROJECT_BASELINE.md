# mmradar 项目基线梳理

一句话结论：当前仓库已经具备一条可验证的“毫米波雷达采集 + ZYNQ 端 DMA/TCP 传输 + Qt 上位机接收/清洗/BP 成像”链路；“视觉识别/雷达视觉融合”目前更多停留在申报目标层，而不是仓库里已落地的主实现。

## 说明与边界

- 本文是给自己后续接手项目用的技术接管材料，不是申报书复述。
- 结论只基于当前工作区里实际存在并可读取的内容：`大饼.txt`、根目录申报材料、源码、工程文件、数据文件、PCB 报告文件。
- 本文不深挖 `.SchDoc`、`.PcbDoc`、PDF 内部电路细节，只基于文件存在性、命名、报告文件和源码做可靠整理。
- IDE 中打开的 `0.md`、`DEVELOPMENT_ROADMAP.md`、`__encoding_test.md`、`aitest.py` 在当前工作区磁盘扫描中均未找到，因此本文不把它们作为证据来源。

## 1. 项目想做什么

这一部分来自 `大饼.txt`，以及工作区根目录里的申报材料 `20250217_毫米波雷达融合视觉小目标融合探测技术.pdf` / `20250217_毫米波雷达融合视觉小目标融合探测技术 (1).doc`。

### 1.1 目标定位

- 项目目标是做一套便携式低空小目标探测系统，核心关键词是：
  - 24GHz 毫米波雷达
  - 视觉目标识别
  - 多传感器融合
  - 低空无人机/小目标探测
- 申报材料中的主控平台是 `ZYNQ-7020`，传感器侧提到毫米波雷达前端和摄像头，上位机侧提到数据显示、处理与目标识别。

### 1.2 申报层面的应用场景

- 城市低空管理
- 农业植保
- 空中交通与应急救援
- 安防监控

### 1.3 申报层面的技术路线

- 硬件集成：雷达前端、摄像头、ZYNQ 核心板、系统底板、上位机。
- 板端软件：PS 侧完成采样数据传输。
- 上位机软件：完成数据接收、存储、实时显示、处理。
- 感知算法：计划部署视觉识别与雷达/视觉融合能力。

### 1.4 申报材料里声称的“已有基础”

从 `大饼.txt` 的表述看，团队自述已有以下基础：

- 已经做过基于 `ZYNQ-7020` 和 `ADS7853` 的雷达控制/回波采集底板。
- 已购置并使用毫米波雷达前端板。
- 已有 C++/Qt 上位机开发基础。
- 已经在上位机侧尝试过视觉识别方向。

### 1.5 这一部分与仓库现状的关系

- 申报材料里的“毫米波雷达 + 视觉识别 + 融合探测”是**项目目标**。
- 当前仓库里能直接验证到的**主实现重点**，仍然是雷达链路本身：采样、传输、保存、清洗、成像。
- 因此后续阅读仓库时，应该把“目标愿景”和“已落地工程”分开理解，避免高估当前完成度。

## 2. 工作区真实结构

当前 `mmradar/` 根目录只有三大块内容和一份申报文本：

- `archives/`
  - 归档包，包含 `Miz_sys.rar`、`MZ7XB.zip`、`sar_tcp.rar`。
  - 作用更像历史快照备份，不是当前阅读源码的主入口。
- `resources/`
  - 数据、标定、资料库。
  - 包含真实采样文件、噪声标定文件、PDF 数据手册、说明图片。
- `projects/`
  - 真正的工程主体。
  - 又分成 `hardware_pcb/`、`fpga_pspl/`、`host_qt/` 三条线。
- `大饼.txt`
  - 申报书文本导出版本，UTF-8 编码，可直接读。

### 2.1 `archives/`

- 当前只有 3 个压缩包，体量约 210 MB。
- 适合做“历史版本对照”，不适合作为当前代码入口。

### 2.2 `resources/`

- `resources/data/`
  - `sar_3.bin`：原始采样文件，大小 `76,813,014` 字节。
  - `clean.bin`：清洗后的成像输入，大小 `76,854,340` 字节。
  - `baseline_20260302_112851.md`：一次基线记录。
  - `radar_data_plot.png`：数据可视化图片。
- `resources/calibration/`
  - `sar_noise_500M.bin`：噪声标定文件，大小 `1,082,052` 字节。
- `resources/docs/`
  - 包含 `RKB1201T`、`ADF4158/4159`、`ads7853`、`MZ7XB_Fun` 等资料。
- `resources/notes/`
  - 有一张 `说明.png`，看起来是辅助说明图。

### 2.3 `projects/`

- `projects/hardware_pcb/`
  - Altium 原理图、PCB、Gerber、SMT 对单文件。
- `projects/fpga_pspl/`
  - ZYNQ/Vivado 工程、SDK 裸机程序、生成的 IP/仿真/缓存目录。
- `projects/host_qt/`
  - Qt 上位机工程 `sar_tcp`，另带本地 `fftw/` 和 `build/`。

### 2.4 当前结构的一个重要现实

- `projects/fpga_pspl/` 中混有大量 Vivado 生成目录，例如 `.Xil/`、`Miz_sys.cache/`、`Miz_sys.ip_user_files/`、`Miz_sys.runs/`、`Miz_sys.sim/`、`Miz_sys.sdk/`。
- `projects/host_qt/sar_tcp/` 中混有 `build/` 和本地打包的 `fftw/`。
- `projects/hardware_pcb/MZ7XB/` 中混有 `History/`、`Project Logs/`、`Project Outputs/`。
- 这意味着当前仓库更像“工作盘快照”，不是一个已经清理干净的源码仓库。

## 3. 已有工程基础

这一部分只写“已经在磁盘里看到并能验证”的基础。

### 3.1 硬件基础：PCB 不是空白设计

`projects/hardware_pcb/MZ7XB/` 明显不是空壳目录，至少说明硬件设计已经走到出板甚至生产准备阶段。

可直接看到的证据：

- 有完整分层原理图：
  - `01_TOP.SchDoc`
  - `02_connector.SchDoc`
  - `07_PS_ETH_RJ45.SchDoc`
  - `10_HDMI_OUT.SchDoc`
  - `15_PMU.SchDoc`
  - 以及其他分模块原理图
- 有 PCB 文件：
  - `new.PcbDoc`
  - `new - 备份_未布线版本.PcbDoc`
  - `new - 备份_具有准确的打孔.PcbDoc`
- 有生产输出：
  - `Gerber_mmradar_2.0_2024-10-18.zip`
  - `嘉立创SMT订单核对_PCB_MMRADAR-1_mmradar_2.0_20241018113401_2024-10-18.pdf`
- 有板信息报告：
  - `projects/hardware_pcb/MZ7XB/new.txt`
  - `projects/hardware_pcb/MZ7XB/new - 备份_未布线版本.txt`

其中两个 `.txt` 报告都写明 `Routing completion, 100.00%`，说明至少对应版本的板级连线已完成。

结论：硬件底板/核心板方向已经有实际板级设计成果，不是“还没开始画板”。

### 3.2 板端基础：ZYNQ 侧的 DMA + TCP 传输链路已经成形

#### 3.2.1 Vivado 设计层

`projects/fpga_pspl/Miz_sys/Miz_sys.srcs/sources_1/bd/system/hw_handoff/system_bd.tcl` 显示的核心硬件链路是：

- 外部输入 `S_AXIS`：`system_bd.tcl:160`
- `axis_data_fifo_0`：`system_bd.tcl:202`
- `axi_dma_0`：`system_bd.tcl:181`
- `axi_gpio_0`：`system_bd.tcl:189`
- DMA 通过 `S_AXI_HP0` 访问 DDR：`system_bd.tcl:521`
- `S_AXIS -> FIFO`：`system_bd.tcl:515`
- `FIFO -> DMA(S2MM)`：`system_bd.tcl:522`

这说明板端主线不是“直接裸采”，而是典型的：

`PL AXIS 数据流 -> FIFO -> AXI DMA -> PS DDR`

#### 3.2.2 SDK 裸机程序层

`projects/fpga_pspl/Miz_sys/Miz_sys.sdk/PL2PS_DMA_Test/src/main.c` 是当前最关键的板端软件证据。

可以直接确认：

- 板端静态 IP 设为 `192.168.1.11`：`main.c:264`
- 板端主动连接上位机 `192.168.1.2:2829`：`main.c:428-430`
- 板端接收控制词 `start` / `stop`：`main.c:345-353`
- 板端采样通过 `XAxiDma_SimpleTransfer` 触发：`main.c:682`
- 采样数据在 FIFO/DDR 中缓存后，通过 `tcp_send` 推送给上位机：`main.c:724-748`

结论：板端不是只做了 DMA 实验，而是已经做到了“受上位机控制并通过 TCP 回传采样数据”。

### 3.3 上位机基础：Qt 侧已经完成接收、保存、观测、清洗、成像

上位机主工程在 `projects/host_qt/sar_tcp/`。

#### 3.3.1 工程形态

- Qt 工程文件：`projects/host_qt/sar_tcp/sar_tcp.pro`
- 界面文件：`projects/host_qt/sar_tcp/mainwindow.ui`
- 主要源码：
  - `mainwindow.cpp/.h`
  - `sar_data_cleaner.cpp/.h`
  - `sar_bp_1d.cpp/.h`
  - `sar_bp.cpp/.h`

#### 3.3.2 TCP 接收与控制

`projects/host_qt/sar_tcp/mainwindow.cpp` 可以直接确认：

- 本地监听 `2829` 端口：`mainwindow.cpp:12`
- 采集态给板端发 `start` / `stop`：`mainwindow.cpp:481`、`mainwindow.cpp:496`
- 观测态给板端发 `start` / `stop`：`mainwindow.cpp:531`、`mainwindow.cpp:541`

这和板端 `main.c` 里的 `192.168.1.2:2829` 是对得上的。

#### 3.3.3 原始数据落盘

- 文件索引与文件名规则由 `MainWindow::file_open()` 管理：`mainwindow.cpp:501-512`
- 原始采样会写入 `sar_%1.bin`：`mainwindow.cpp:503-505`
- 当前路径宏硬编码在 `projects/host_qt/sar_tcp/mainwindow.h:22-24`

结论：`sar_*.bin` 是上位机保存下来的原始采样，不是手工放进去的演示文件。

#### 3.3.4 观测态 FFT 距离像

- `MainWindow::getData()` 在观测态把采样拆分成 4 路，并对一路做 FFT：`mainwindow.cpp:304-457`
- `paintEvent()` 里同时画时域波形和距离像：`mainwindow.cpp:185-257`

结论：上位机并不只是“收包保存”，还提供了一个在线观测界面。

#### 3.3.5 数据清洗

`projects/host_qt/sar_tcp/sar_data_cleaner.cpp` 是清洗阶段的关键实现。

它做的事情包括：

- 测量 trip 平均长度并补偿：`sar_data_cleaner.cpp:42-75`
- 识别并补齐漏掉的 trip：`sar_data_cleaner.cpp:118-190`
- 生成清洗后的输出文件：`sar_data_cleaner.cpp:78-80`
- 清洗完成后发 `clean_finish(output_file)`：`sar_data_cleaner.cpp:210`

从 `mainwindow.cpp` 也能看到，上位机会把清洗输出固定写到 `clean.bin`：`mainwindow.cpp:553`。

结论：`clean.bin` 是一个有明确生成逻辑的中间产物，不是随手保存的数据副本。

#### 3.3.6 BP 成像

`projects/host_qt/sar_tcp/sar_bp_1d.cpp` 是当前真正承担成像工作的实现。

可直接确认：

- 默认补零倍数 `zero_times = 10`：`sar_bp_1d.cpp:16`
- 成像时默认 `gap_h = 15`、`gap_t = 50`：`sar_bp_1d.cpp:73-75`
- 成像主流程在 `sar_bp_1d::run()` 中：`sar_bp_1d.cpp:49-331`
- 支持加载噪声标定文件：`sar_bp_1d.cpp:332-358`
- 支持根据阈值调对比度：`sar_bp_1d.cpp:363-412`

从 `mainwindow.cpp` 能看到当前常用成像参数：

- `set_geo(-2, 2.5, 5, 8)`：`mainwindow.cpp:566`
- `set_grid(500, 800)`：`mainwindow.cpp:567`
- `set_sar_high(0.872)`：`mainwindow.cpp:568`
- `set_speed(0.12)`：`mainwindow.cpp:574`

结论：当前仓库已经具备“原始采样 -> 清洗 -> BP 成像”的一条完整雷达后处理链路。

#### 3.3.7 `sar_bp` 当前不是主力模块

- `projects/host_qt/sar_tcp/sar_bp.cpp` 中 `sar_bp::run()` 还是空函数：`sar_bp.cpp:33`

结论：真正可用的成像实现是 `sar_bp_1d`，不是 `sar_bp`。

### 3.4 数据与标定基础：仓库里有真实样本

#### 3.4.1 已有真实数据

- `resources/data/sar_3.bin`：`76,813,014` 字节
- `resources/data/clean.bin`：`76,854,340` 字节
- `resources/calibration/sar_noise_500M.bin`：`1,082,052` 字节

#### 3.4.2 `clean.bin` 的可解析结果

按 `sar_data_cleaner.cpp` / `sar_bp_1d.cpp` 的文件格式读取，当前 `clean.bin` 可直接解析出：

- `trip_len = 3000`
- `trip_num ≈ 3198`
- 第一个记录的 `now_pt = 48`

这说明：

- 当前清洗后的数据文件不是坏文件。
- 代码和数据格式在样本层面是对得上的。

#### 3.4.3 基线记录文件

`resources/data/baseline_20260302_112851.md` 记录了一次运行状态，里面明确写到：

- 当前采集文件是 `sar_3.bin`
- 目标采样长度是 `75000 KB`
- 当前 BP 参数是：
  - `x/y/w/h = -2 / 2.5 / 5 / 8`
  - `网格 = 500 x 800`
  - `速度 = 0.12 m/s`
  - `SAR高度 = 0.872`
  - `补零倍数 = 10`

这和 `mainwindow.cpp`、`sar_bp_1d.cpp` 里的默认参数是能对应起来的。

### 3.5 资料库基础

`resources/docs/` 已经聚齐一批硬件/芯片资料：

- `RKB1201T datasheet1.0.pdf`
- `SRK1201L_1T2R_24GHz_Transceiver_MMIC_Datasheet (1).pdf`
- `ADF4158_cn.pdf`
- `ADF4159.pdf`
- `ads7853.pdf`
- `MZ7XB_Fun.pdf`

这说明当前目录不只是“源码”，也在承担项目资料库的作用。

## 4. 当前端到端链路

按当前仓库里可验证到的实现，主链路可以概括为：

```text
PL 侧 S_AXIS 采样流
-> axis_data_fifo_0
-> axi_dma_0 (S2MM)
-> ZYNQ DDR
-> lwIP/TCP 板端程序
   (192.168.1.11 -> 192.168.1.2:2829)
-> Qt 上位机 sar_tcp
-> sar_*.bin 原始采样文件
-> sar_data_cleaner 生成 clean.bin
-> sar_bp_1d 做 BP 成像
-> 界面显示时域波形 / 距离像 / 成像结果
```

这个链路的关键证据分别在：

- 硬件链路：`projects/fpga_pspl/Miz_sys/Miz_sys.srcs/sources_1/bd/system/hw_handoff/system_bd.tcl`
- 板端传输：`projects/fpga_pspl/Miz_sys/Miz_sys.sdk/PL2PS_DMA_Test/src/main.c`
- 上位机接收：`projects/host_qt/sar_tcp/mainwindow.cpp`
- 数据清洗：`projects/host_qt/sar_tcp/sar_data_cleaner.cpp`
- 成像：`projects/host_qt/sar_tcp/sar_bp_1d.cpp`

## 5. 当前现状诊断

### 5.1 项目真实完成度判断

- 当前仓库的**实质完成度**在“雷达链路打通”这一侧已经不低。
- 当前仓库的**融合感知完成度**仍偏低，至少从源码看，尚不能说已经完成“雷达 + 视觉融合探测系统”。

### 5.2 已验证到的事实

- `mainwindow.cpp` 监听 `2829` 并收发 `start/stop`：`mainwindow.cpp:12`、`481`、`496`、`531`、`541`
- `PL2PS_DMA_Test/src/main.c` 用 lwIP 主动连 `192.168.1.2:2829`，并收 `start/stop` 控制词：`main.c:428-430`、`345-353`
- `sar_data_cleaner` 负责 trip 对齐/补齐并生成 `clean.bin`：`sar_data_cleaner.cpp:42-80`、`118-190`
- `sar_bp_1d` 负责基于几何参数的 BP 成像：`sar_bp_1d.cpp:49-331`

### 5.3 未在仓库中验证到的事实

- 没有看到真正的摄像头采集链路代码。
- 没有看到 YOLOv5 或其他视觉检测模型的部署代码。
- 没有看到雷达与视觉的时间同步、空间标定、融合决策等主实现代码。

换句话说，当前仓库里“视觉/融合”更多是项目愿景，不是当前主工程事实。

### 5.4 当前最明显的问题

#### 1. 路径硬编码严重

- `mainwindow.h` 里直接写死了：
  - `E:/mmradar/data/`：`mainwindow.h:22`
  - `E:/mmradar/sar_noise_500M.bin`：`mainwindow.h:24`
- 代码里还残留了历史 `D:/Desktop/毕设/...`、`D:/Download/...` 路径。

这意味着当前工程对原作者机器环境耦合很强，换机后直接运行的概率不高。

#### 2. 生成产物和源码混放

- Qt 的 `build/` 目录直接在工程内。
- Vivado 的 `.Xil/`、`cache/`、`runs/`、`sim/`、`sdk/` 与源码同级放置。
- PCB 目录里有大量 `History/`、`Project Logs/`、`Project Outputs/`。

问题不是“不能工作”，而是会显著提高阅读和接管成本。

#### 3. 工程当前不在 Git 仓库中

- 当前 `mmradar/` 目录下没有 `.git`，执行 `git rev-parse --show-toplevel` 会直接报错。

这意味着：

- 现在没有可追溯的版本边界。
- 也没有办法判断哪些文件是手工源码，哪些是生成物，哪些是历史遗留。

#### 4. 模块命名与真实状态不完全一致

- `sar_bp` 名字看起来像主成像模块，但 `sar_bp::run()` 为空。
- 真正工作的成像逻辑在 `sar_bp_1d`。

这会误导后续接手者的阅读顺序。

#### 5. 视觉融合目标与仓库实现有明显落差

- 申报材料主轴是“毫米波雷达融合视觉小目标探测”。
- 当前仓库主实现是“雷达采样、传输、清洗、成像”。

这不是坏事，但必须正视，否则后续排期会失真。

#### 6. 有零散实验脚本，但位置不合理

- `projects/fpga_pspl/Miz_sys/Miz_sys.srcs/sources_1/bd/system/ipshared/b2d0/hdl/verilog/` 下有：
  - `radar.py`
  - `import numpy as np.py`

这两个 Python 脚本明显不是 Vivado 主构建链路的一部分，更像临时实验脚本；放在这个位置会降低可维护性。

## 6. 我对当前项目的判断

如果只问“这个项目现在真正做到了什么”，我会这样概括：

- 已经做到了：
  - 有实际板卡设计
  - 有 ZYNQ 端采样与 TCP 传输
  - 有 Qt 上位机接收与保存
  - 有数据清洗
  - 有 BP 成像
  - 有真实数据样本和噪声标定样本
- 还没有在仓库里证明做到：
  - 摄像头链路工程化接入
  - 视觉目标检测部署
  - 雷达/视觉融合闭环

因此当前最准确的阶段判断应是：

> 这是一个“雷达链路已基本打通、视觉融合尚未真正落仓”的中期工程快照。

## 7. 建议的下一步

建议按优先级做，不要同时乱推三条线。

### 第一优先级：先把工程收拾到“可接手”

- 把路径硬编码改成配置项或相对路径。
- 把 `build/`、Vivado 生成目录、历史归档、实验脚本和主源码分层。
- 写一份最小运行说明：
  - 板端 IP
  - 上位机 IP
  - 端口
  - 数据目录
  - 噪声文件路径
  - 一次完整采集/清洗/成像的操作顺序

如果这一步不做，后面任何算法或融合工作都会继续堆在混乱结构上。

### 第二优先级：把“当前雷达链路”补成可复现实验链

- 明确 `sar_*.bin` 和 `clean.bin` 的文件格式。
- 固化一组基准数据和成像参数。
- 把采样、清洗、成像的输入输出关系写成文档或脚本。

目标不是先做新功能，而是让现有能力稳定可复现。

### 第三优先级：再决定后续主线

到这一步再选方向，而不是现在同时开三条战线。

可选主线有两条：

- 继续强化雷达链路
  - 提升采样稳定性
  - 优化清洗逻辑
  - 优化成像速度和参数管理
- 正式开始视觉/融合接入
  - 明确摄像头输入链路
  - 明确检测模型部署位置
  - 明确雷达与视觉的同步/标定/融合接口

如果项目目标仍然是“融合探测”，那前提不是直接加模型，而是先把“视觉链路放到哪里、和雷达在哪一层汇合”设计清楚。

## 8. 接手时最值得记住的四句话

- 这个项目最终想做的是“毫米波雷达 + 视觉”的低空小目标探测系统。
- 现在已经真正做好的主线是“雷达采样、传输、清洗、BP 成像”。
- 当前工程最大的现实问题不是算法，而是路径硬编码、生成物混放、仓库边界不清。
- 下一步最值得先做的不是继续加功能，而是先把现有雷达链路整理成一个可复现、可迁移、可维护的基线工程。
