# 示例执行报告: lisa_wdt basic

> 说明：这是一个“报告格式样例”，用于指导实际执行后生成的报告内容。

**日期**: 2026-02-25  
**项目**: `samples/drivers/devices/lisa_wdt/basic`  
**板型**: `arcs_evb`  
**串口设备**: `/dev/ttyACM0`

## 执行摘要

| 步骤 | 状态 |
|------|------|
| 拉取仓库 | ✅ 成功 |
| 安装工具链 | ✅ 成功 |
| 编译 | ✅ 成功 |
| 烧录 | ✅ 成功（用户手动使用 `./tools/burn/cskburn` 完成） |
| 运行验证 | ✅ 成功，日志与 README 预期完全匹配 |

## 编译信息

- **编译产物**: `build/arcs.bin` (131KB)
- **版本**: `v0.0.1-1003-g4e2145a2864e`
- **内存使用**: PSRAM 128KB/8MB (1.56%), FLASH 117KB/8176KB (1.41%), SRAM 41KB/256KB (16%)

## 遇到的问题

### 问题 1: 使用了错误的 cskburn（关键问题）
- **现象**: `listenai-dev-tools/listenai-tools/cskburn/cskburn` 烧录时每个奇数 block 需要 2 次重试，最终在 block 31 失败（`ERROR: Failed burning partition 1: 01`）；不支持 `-C arcs` 参数
- **是否偶发**: 否，稳定复现
- **根因**: 仓库中有两个 cskburn 工具：
  - `./tools/burn/cskburn` — **正确的**，支持 `-C arcs` 指定芯片类型，烧录前会自动擦除，烧录成功
  - `./listenai-dev-tools/listenai-tools/cskburn/cskburn` — **错误的**，通用版本，不支持 `-C` 参数，缺少擦除步骤导致写入失败
- **解决方案**: 始终使用 `./tools/burn/cskburn -C arcs -s <device> -b 3000000 0x0 <bin>`

### 问题 2: cskburn 权限不足
- **现象**: `权限不够` 错误
- **根因**: 下载解压后的二进制文件未保留执行权限
- **解决方案**: `chmod +x ./tools/burn/cskburn`

### 问题 3: 烧录时 Failed opening device
- **现象**: cskburn 报 `ERROR: Failed opening device`
- **根因**: 板子未进入烧录模式或设备未就绪
- **解决方案**: 确保设备连接正常，必要时按 BOOT+RESET 进入烧录模式后重试

### 问题 4: GCC 工具链需单独安装
- **现象**: `prepare_listenai_tools.sh` 只安装 cmake/ninja 等构建工具，不包含 GCC
- **根因**: GCC 工具链需要额外运行 `prepare_toolchain.sh`
- **解决方案**: 依次运行 `prepare_listenai_tools.sh` 和 `prepare_toolchain.sh`

## 串口日志验证

固件版本 `v0.0.1-1003-g4e2145a2864e` 与编译产物一致，输出与 README 预期完全匹配：

```
=== LISA WDT basic example ===
wdt0 device ready
WDT configured: int_timeout=300 ms, rst_timeout=200 ms (total=500 ms)
WDT started
WDT state: RUNNING
Feeding WDT every 300 ms
```

## SKILL 优化建议

1. **烧录命令路径修正（重要）**: 应使用 `./tools/burn/cskburn -C arcs`，而非 `listenai-dev-tools/listenai-tools/cskburn/cskburn`
2. **安装步骤补充**: 安装步骤应包含两个脚本：`prepare_listenai_tools.sh`（构建工具）+ `prepare_toolchain.sh`（GCC 工具链）
3. **cskburn 权限**: 安装后建议检查并 `chmod +x`

