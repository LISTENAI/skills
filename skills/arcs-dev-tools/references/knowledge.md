# 经验知识库

> 用于快速诊断。执行前按需读取对应 topic，执行后将新发现写入**执行报告**，再由维护者定期沉淀到本知识库。
> topic：仓库管理 / 环境安装 / 编译 / 烧录 / 串口 / 代码调试

---

## Topic 0: 仓库管理

### 0-1. 子模块下载耗时长
- **现象**: `git submodule update --init --recursive` 需要 3-5 分钟，子模块较多
- **原因**: 仓库模块多，部分模块体量大
- **解决**: 超时设为 300s；若只需部分模块，可 `git submodule update --init <specific_module>`
- **次数**: 1（2026-02-25, 首次拉取）

### 0-2. 子模块重定向警告
- **现象**: `warning: 重定向到 https://...collections-c.git/`
- **原因**: `.gitmodules` 中 URL 末尾缺少 `.git`，服务器自动重定向
- **判定**: 不影响功能，属正常现象，无需处理
- **次数**: 1（2026-02-25, collections-c / ltlsf）

---

## Topic 1: 环境安装

### 1-1. 需要两个安装脚本
- **现象**: 只运行 `prepare_listenai_tools.sh` 后编译报找不到 gcc
- **原因**: 该脚本只安装构建工具（cmake/ninja）；GCC 交叉编译工具链需额外运行 `prepare_toolchain.sh`
- **解决**: 依次运行 `prepare_listenai_tools.sh` → `prepare_toolchain.sh`
- **次数**: 1（2026-02-25, 首次安装）

### 1-2. cskburn 缺少执行权限
- **现象**: `权限不够` / `Permission denied`
- **原因**: 下载解压后的二进制文件未保留执行权限
- **解决**: `chmod +x ./tools/burn/cskburn`
- **次数**: 1（2026-02-25）

### 1-3. 仓库中存在两个 cskburn
- **现象**: 使用 `listenai-dev-tools/listenai-tools/cskburn/cskburn` 烧录失败
- **原因**: 仓库中有两个不同版本的 cskburn：
  - `./tools/burn/cskburn` — 正确版本，支持 `-C arcs`，烧录前自动擦除
  - `./listenai-dev-tools/listenai-tools/cskburn/cskburn` — 通用版本，不支持 `-C`，烧录行为不正确
- **解决**: 始终使用 `./tools/burn/cskburn -C arcs`
- **次数**: 1（2026-02-25, lisa_wdt basic）

---

## Topic 2: 编译

（暂无记录）

---

## Topic 3: 烧录

### 3-1. 串口设备号变化
- **现象**: `/dev/ttyACM0` 变成 `/dev/ttyACM1` 或其他
- **原因**: USB 重新枚举（拔插、复位、烧录工具操作等）
- **解决**: 每次操作前扫描 `ls /dev/ttyACM* /dev/ttyUSB*`，不硬编码
- **次数**: 0（预防性记录）

### 3-2. 串口被占用 (EBUSY)
- **现象**: cskburn 报 `Failed opening device: EBUSY`
- **原因**: 其他进程未关闭（串口监视器/脚本等）
- **解决**: `fuser <设备>` 找到占用进程并结束 → 重试
- **次数**: 1（2026-02-25, lisa_wdt basic）

### 3-3. cskburn ETIMEDOUT
- **现象**: `Failed changing baud rate: ETIMEDOUT`，反复重试失败
- **原因**: 串口被占用或 USB 连接不稳定，设备无法进入更新模式
- **解决**: 先 `fuser` 释放占用 → 重新扫描设备号 → 重试
- **次数**: 1（2026-02-25, lisa_wdt basic）

---

## Topic 4: 串口

### 4-1. picocom/minicom 在非交互式环境不可用
- **现象**: 报 `STDIN is not a TTY`，立即退出
- **原因**: 某些执行环境无交互式 TTY
- **解决**: 使用 `stty -F <dev> ...` 配置后再用 `timeout cat <dev>` 读取（见 `SKILL.md` 操作 5）
- **次数**: 1（2026-02-25, lisa_wdt basic）

### 4-2. 串口乱码
- **现象**: 刚打开串口或复位瞬间读到乱码
- **原因**: bootloader 可能使用不同波特率；串口状态未稳定
- **解决**: 等 1-2 秒后再读；或先读 1 次丢弃，再读第 2 次作为有效日志
- **次数**: 2（2026-02-25, lisa_wdt basic）

### 4-3. USB CDC 设备断连
- **现象**: 读日志过程中设备消失/断连
- **原因**: USB 重新枚举或线材/供电不稳
- **解决**: 关闭连接 → 等 2-3 秒 → 扫描 `/dev/ttyACM*` → 用新路径重连
- **次数**: 1（2026-02-25, lisa_wdt basic）

---

## Topic 5: 代码调试

### 5-1. 双重启动 ≠ WDT 超时
- **现象**: 启动日志出现两次，易误判为看门狗超时复位
- **区分**:
  - WDT 超时 → 持续重启（每隔固定时间循环）
  - 信号/USB 枚举导致的复位 → 恰好两次，之后稳定
  - 不做任何操作仍持续重启 → 才是 WDT 问题
- **验证**: 第二次启动后监控 10-15 秒，0 次额外重启 → 排除 WDT
- **次数**: 1（2026-02-25, lisa_wdt basic）

