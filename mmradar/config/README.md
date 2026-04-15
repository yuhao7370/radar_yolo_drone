# sar_tcp.ini 说明

`sar_tcp.ini` 是当前上位机运行参数模板，路径相对 `mmradar/` 根目录解释。

## 字段

### `[paths]`

- `data_dir`
  - 原始采样文件和清洗输出所在目录
- `noise_file`
  - 成像使用的噪声标定文件

### `[network]`

- `listen_port`
  - 上位机本地监听端口

### `[capture]`

- `target_size_kb`
  - 单次采集目标文件大小，单位 KB

### `[imaging]`

- `x/y/w/h`
  - 成像几何范围
- `grid_x/grid_y`
  - 成像网格
- `speed`
  - 合成孔径运动速度
- `sar_height`
  - 雷达高度
- `contrast_level`
  - 成像对比度基线参数

## 当前使用约定

- 所有路径默认相对 `mmradar/` 根目录解释。
- 如果后续参数增加，优先继续放到这个 INI 中，不再把新参数散落到源码里。
