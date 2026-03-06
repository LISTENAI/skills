# 经验知识库

> 用于快速诊断。执行前按需读取对应 topic。本文件内容由维护者手动维护，**模型不要修改本文件**。
> topic：仓库管理 / 环境安装 / 编译 / 烧录 / 串口 / 代码调试 / JLink

---

## Topic 0: 仓库管理

### 0-1. 子模块下载耗时长
- **现象**: `git submodule update --init --recursive` 需要 3-5 分钟，子模块较多
- **原因**: 仓库模块多，部分模块体量大
- **解决**: 超时设为 300s；若只需部分模块，可 `git submodule update --init <specific_module>`

### 0-2. 子模块重定向警告
- **现象**: `warning: 重定向到 https://...collections-c.git/`
- **原因**: `.gitmodules` 中 URL 末尾缺少 `.git`，服务器自动重定向
- **判定**: 不影响功能，属正常现象，无需处理

---

## Topic 1: 环境安装

### 1-1. 需要两个安装脚本
- **现象**: 只运行 `prepare_listenai_tools.sh` 后编译报找不到 gcc
- **原因**: 该脚本只安装构建工具（cmake/ninja）；GCC 交叉编译工具链需额外运行 `prepare_toolchain.sh`
- **解决**: 依次运行 `prepare_listenai_tools.sh` → `prepare_toolchain.sh`

### 1-2. cskburn 缺少执行权限
- **现象**: `权限不够` / `Permission denied`
- **原因**: 下载解压后的二进制文件未保留执行权限
- **解决**: `chmod +x ./tools/burn/cskburn`

### 1-3. 仓库中存在两个 cskburn
- **现象**: 使用 `listenai-dev-tools/listenai-tools/cskburn/cskburn` 烧录失败
- **原因**: 仓库中有两个不同版本的 cskburn：
  - `./tools/burn/cskburn` — 正确版本，支持 `-C arcs`，烧录前自动擦除
  - `./listenai-dev-tools/listenai-tools/cskburn/cskburn` — 通用版本，不支持 `-C`，烧录行为不正确
- **解决**: 始终使用 `./tools/burn/cskburn -C arcs`

---

## Topic 2: 编译

（暂无记录）

---

## Topic 3: 烧录

### 3-1. 串口设备号变化
- **现象**: `/dev/ttyACM0` 变成 `/dev/ttyACM1` 或其他
- **原因**: USB 重新枚举（拔插、复位、烧录工具操作等）
- **解决**: 每次操作前扫描 `ls /dev/ttyACM* /dev/ttyUSB*`，不硬编码

### 3-2. 串口被占用 (EBUSY)
- **现象**: cskburn 报 `Failed opening device: EBUSY`
- **原因**: 其他进程未关闭（串口监视器/脚本等）
- **解决**: `fuser <设备>` 找到占用进程并结束 → 重试

### 3-3. cskburn ETIMEDOUT
- **现象**: `Failed changing baud rate: ETIMEDOUT`，反复重试失败
- **原因**: 串口被占用或 USB 连接不稳定，设备无法进入更新模式
- **解决**: 先 `fuser` 释放占用 → 重新扫描设备号 → 重试

---

## Topic 4: 串口


（暂无记录）

---

## Topic 5: JLink

### 5-1. JLink 无法识别 ARCS 芯片
- **现象**: JFlashExe 报 `Could not find device` 或 `Unknown device`
- **原因**: `~/.config/SEGGER/JLinkDevices/Listenai.xml` 缺失或缺少 ARCS 条目
- **解决**: 执行操作 7（JLink 环境检测与部署），自动部署 JLinkDevices 配置

### 5-2. VTref too low
- **现象**: JLink 报 `VTref too low` 或 `Could not connect`
- **原因**: JLink 的 VTref 引脚未接到目标板 3.3V，或目标板未上电
- **解决**: 确认 VTref 接到 3.3V，确认目标板已上电

### 5-3. 不要使用 JFlashExe 进行连接测试
- **现象**: JFlashExe 弹出图形界面，或在无头环境报 `no display`
- **原因**: JFlashExe 是 GUI 程序，即使有 xvfb-run 也可能在桌面环境弹窗
- **解决**: 连接测试和 flash 读取统一使用 `JLinkExe`（纯 CLI），参见 `jlink-setup.md` 步骤 6

### 5-4. JLink Script 文件找不到
- **现象**: JFlash 日志报 `Script file not found`
- **原因**: arcs.jflash 中的 ScriptFile 路径不正确
- **解决**: 检查从模板生成 jflash 文件时 `{{SKILL_DIR}}` 占位符是否被正确替换为技能目录绝对路径

### 5-5. ARCS JLink 接线
- **接口**: cJTAG (2-pin)，TargetIF=7
- **接线**: PA01-SWDIO, PA00-SWCLK, GND, VTref(3.3V)
- **注意**: 必须接 VTref，JLink 依赖此引脚检测目标电压

### 5-6. CPU-TAP not found in JTAG chain
- **现象**: JLinkGDBServerCLExe 或 JLinkExe 报 `ERROR: CPU-TAP not found in JTAG chain`
- **原因**: 启动时未指定 `-JLinkScriptFile` 参数。ARCS 是双 TAP JTAG chain（AP + CP），没有 JLinkScript 定义各 TAP 的 IR/DR 位置，JLink 无法定位正确的 CPU TAP
- **解决**: 所有 JLink 工具调用**必须**加上 `-JLinkScriptFile <skill_dir>/assets/jlink/jtagscan0.JLinkScript`（debug CP 时用 `jtagscan1.JLinkScript`）

### 5-7. CPU could not be halted
- **现象**: JTAG chain 识别正常（找到 2 个设备），但报 `CPU could not be halted` / `Timeout while waiting for core to halt after reset and halt request`
- **原因**: 目标芯片处于异常运行状态，不响应调试 halt 请求
- **解决**:
  1. 按 RESET 键或断电重新上电后重试
  2. 尝试 connect under reset：在 JLinkExe 中使用 `-AutoConnect 1` 参数
  3. 检查 JTAG 接线信号质量（接线是否过长或松动）
  4. 确认目标板固件未禁用调试接口

---
