# JLink ARCS 环境检测与部署

本文档指导 Claude Code 完成 ARCS 芯片的 JLink 调试环境检测与自动部署。

## 接线说明

ARCS 使用 **cJTAG (2-pin)** 接口连接 JLink：

| JLink Pin | ARCS Pin | 功能 |
|-----------|----------|------|
| SWDIO     | PA01     | cJTAG 数据线 |
| SWCLK     | PA00     | cJTAG 时钟线 |
| GND       | GND      | 地线 |
| VTref     | 3.3V     | 参考电压（必须接） |

> **VTref 必须接**，JLink 依赖此引脚检测目标电压。未接会导致无法识别目标。

## 步骤 1：检测 JLink 软件

### 1.1 检测核心工具

```bash
which JLinkExe && which JLinkGDBServerCLExe
```

- **全部存在** → 已安装，获取版本：
  ```bash
  JLinkExe -? 2>&1 | head -2
  ```
- **缺失** → 提示用户安装

### 1.2 安装指引

| 发行版 | 安装方式 |
|--------|---------|
| Arch Linux | `yay -S jlink` 或 `paru -S jlink` |
| Ubuntu/Debian | 从 SEGGER 官网下载 `.deb` 包安装 |
| 其他 Linux | 从 SEGGER 官网下载通用安装包 |

官网下载地址：https://www.segger.com/downloads/jlink/

> **不要使用 JFlashExe 进行连接测试**。JFlashExe 是 GUI 程序，会弹出图形界面。
> 连接测试和 flash 读取统一使用 `JLinkExe`（纯 CLI，无 GUI 依赖）。

## 步骤 2：检测并部署 JLinkDevices 配置

JLink 需要设备描述文件才能识别 ARCS 芯片。

### 2.1 检测逻辑

按顺序检查以下三项：

```bash
# 1. Listenai.xml 是否存在
test -f ~/.config/SEGGER/JLinkDevices/Listenai.xml

# 2. 是否包含 ARCS 条目
grep -q 'Name="ARCS"' ~/.config/SEGGER/JLinkDevices/Listenai.xml

# 3. Flashloader.elf 是否存在
test -f ~/.config/SEGGER/JLinkDevices/ListenAI/Arcs/Flashloader.elf
```

三项全部通过 → 跳过部署。任一失败 → 执行部署。

### 2.2 部署流程

**第一步：创建目录并复制 Flashloader**

```bash
mkdir -p ~/.config/SEGGER/JLinkDevices/ListenAI/Arcs/
cp <skill_dir>/assets/jlink/Flashloader.elf ~/.config/SEGGER/JLinkDevices/ListenAI/Arcs/
```

**第二步：处理 Listenai.xml**

情况 A — 文件不存在，创建新文件：

```xml
<DataBase>
	<Device>
		<ChipInfo Vendor="ListenAI" Name="ARCS" Core="JLINK_CORE_RISC_V"
			WorkRAMAddr="0x20040000"
			WorkRAMSize="0x00020000" />
		<FlashBankInfo Name="QSPI Flash" BaseAddr="0x30000000" MaxSize="0x400000"
			Loader="ListenAI/Arcs/Flashloader.elf" LoaderType="FLASH_ALGO_TYPE_OPEN"
			AlwaysPresent="1" />
	</Device>
</DataBase>
```

情况 B — 文件存在但缺少 ARCS 条目，在 `</DataBase>` 前插入：

```xml
	<Device>
		<ChipInfo Vendor="ListenAI" Name="ARCS" Core="JLINK_CORE_RISC_V"
			WorkRAMAddr="0x20040000"
			WorkRAMSize="0x00020000" />
		<FlashBankInfo Name="QSPI Flash" BaseAddr="0x30000000" MaxSize="0x400000"
			Loader="ListenAI/Arcs/Flashloader.elf" LoaderType="FLASH_ALGO_TYPE_OPEN"
			AlwaysPresent="1" />
	</Device>
```

使用 `sed` 插入示例：
```bash
sed -i '/<\/DataBase>/i\\t<Device>\n\t\t<ChipInfo Vendor="ListenAI" Name="ARCS" Core="JLINK_CORE_RISC_V"\n\t\t\tWorkRAMAddr="0x20040000"\n\t\t\tWorkRAMSize="0x00020000" />\n\t\t<FlashBankInfo Name="QSPI Flash" BaseAddr="0x30000000" MaxSize="0x400000"\n\t\t\tLoader="ListenAI/Arcs/Flashloader.elf" LoaderType="FLASH_ALGO_TYPE_OPEN"\n\t\t\tAlwaysPresent="1" />\n\t</Device>' ~/.config/SEGGER/JLinkDevices/Listenai.xml
```

## 步骤 3：确定目标核心（AP/CP）并选择 JLink Script

ARCS 是双核芯片（AP + CP），不同核心使用不同的 JTAG TAP 位置，**必须选择正确的 JLink Script**。

### 3.1 JLink Script 选择规则

| 操作 | JLink Script | 说明 |
|------|-------------|------|
| Debug AP 核心 | `jtagscan0.JLinkScript` | AP 在 JTAG chain 的 TAP0 位置 |
| Debug CP 核心 | `jtagscan1.JLinkScript` | CP 在 JTAG chain 的 TAP1 位置 |
| 烧录固件 | `jtagscan0.JLinkScript` | 始终通过 TAP0 |
| 读取 Flash | `jtagscan0.JLinkScript` | 始终通过 TAP0 |
| 读取寄存器 | `jtagscan0.JLinkScript` | 始终通过 TAP0 |

> **简单记忆**：只有 debug CP 核心时用 `jtagscan1`，其他一律用 `jtagscan0`。

### 3.2 自动检测目标核心

从 build 目录的 `.config` 文件自动判断当前编译的是哪个核心：

```bash
# 检测 build 目录中的 .config
grep -E "CONFIG_ARCS_(AP|CP)_CORE=y" <build_dir>/.config
```

| .config 内容 | 目标核心 | Debug 用 JLink Script |
|-------------|---------|----------------------|
| `CONFIG_ARCS_AP_CORE=y` | AP | `jtagscan0.JLinkScript` |
| `CONFIG_ARCS_CP_CORE=y` | CP | `jtagscan1.JLinkScript` |

**检测失败时**（.config 不存在或无匹配项）→ **询问用户**：当前要调试的是 AP 核心还是 CP 核心？

### 3.3 提示用户确认

检测到目标核心后，**必须告知用户当前调试的核心**：

- AP 核心 → "当前编译目标为 **AP 核心**，将使用 jtagscan0.JLinkScript"
- CP 核心 → "当前编译目标为 **CP 核心**，debug 将使用 jtagscan1.JLinkScript"

> 烧录/读 Flash 等非 debug 操作始终使用 `jtagscan0.JLinkScript`，无需区分核心。

## 步骤 4：准备 JFlash 项目文件

arcs.jflash 模板位于 `<skill_dir>/assets/jlink/arcs.jflash`，包含两个占位符：

| 占位符 | 说明 | 替换示例 |
|--------|------|---------|
| `{{SKILL_DIR}}` | 技能安装目录的绝对路径 | `/home/user/.claude/skills/arcs-dev-tools` |
| `{{FIRMWARE_PATH}}` | 固件文件的绝对路径 | `/home/user/arcs-sdk/build/arcs.bin` |

**生成运行时 jflash 文件**：

```bash
# 从模板生成运行时文件（一次性替换所有占位符）
sed \
    -e "s|{{SKILL_DIR}}|<skill_dir 的绝对路径>|g" \
    -e "s|{{FIRMWARE_PATH}}|<固件文件绝对路径>|g" \
    <skill_dir>/assets/jlink/arcs.jflash > /tmp/arcs_runtime.jflash
```

> arcs.jflash 模板中 ScriptFile 默认为 `jtagscan0.JLinkScript`（适用于烧录/读 Flash）。
> 每次使用前都从模板重新生成，避免残留上次的路径。

## 步骤 5：动态检测 JLink 序列号

```bash
echo "ShowEmuList" | JLinkExe -NoGui 1 2>/dev/null | grep -oP 'Serial number: \K[0-9]+'
```

- **找到 1 个** → 自动使用该序列号
- **找到多个** → 列出所有序列号，询问用户选择
- **找不到** → 提示用户：
  1. 确认 JLink 硬件已通过 USB 连接
  2. 检查 `lsusb | grep -i segger`
  3. 检查 udev 权限（用户是否在 `plugdev` 组）

## 步骤 6：连接测试

使用 **JLinkExe**（纯 CLI，无 GUI）读取 flash 的一小段数据验证连接通畅：

```bash
echo -e "\n\n\nsavebin /tmp/arcs_flash_test.bin 0x30000000 0x64\nexit\n" | \
    timeout 25 JLinkExe \
    -USB <serial_number> \
    -NoGui 1 \
    -Device ARCS \
    -IF cJTAG \
    -Speed 4000 \
    -AutoConnect 1 \
    -JLinkScriptFile <skill_dir>/assets/jlink/jtagscan0.JLinkScript \
    2>&1
```

> **说明**：前面的 `\n\n\n` 用于跳过 JLinkExe 的交互式 prompt（IRPre/DRPre 位置确认），让它使用 JLinkScript 中配置的默认值。

### 判断标准

**成功**：
- 输出包含 `Reading 100 bytes from addr 0x30000000 into file...O.K.`
- `/tmp/arcs_flash_test.bin` 文件生成且大小为 100 字节

**失败处理**：

| 错误关键词 | 原因 | 解决方案 |
|-----------|------|---------|
| `Could not connect to target` | 接线问题或芯片未上电 | 检查 PA01-SWDIO、PA00-SWCLK、GND、VTref 接线 |
| `CPU-TAP not found in JTAG chain` | JLinkScript 未加载或路径错误 | 确认 `-JLinkScriptFile` 路径正确 |
| `No J-Link found` | JLink 未连接或驱动问题 | `lsusb \| grep SEGGER`，检查 USB 连接 |
| `VTref too low` | VTref 未接或目标未上电 | 确认 VTref 接到 3.3V，目标板已上电 |
| `Could not find device` | JLinkDevices 配置缺失 | 重新执行步骤 2 |
| `CPU could not be halted` | 芯片处于异常状态，不响应 halt 请求 | 按 RESET 或断电重上电后重试；检查接线信号质量 |
| `Timeout while waiting for core to halt` | 同上，halt 超时 | 同上；尝试加 `-AutoConnect 1` 参数 |

## 重要：设备名差异

不同 JLink 工具使用的设备名不同，**必须严格遵守**：

| 工具 | 设备名参数 | 正确值 |
|------|-----------|--------|
| JFlashExe | arcs.jflash 中 `ChipName` | `ListenAI ARCS` |
| JLinkGDBServerCLExe | `-device` 参数 | `ARCS` |
| JLinkExe | `device` 命令 | `ARCS` |

> **`JLinkGDBServerCLExe -device "ListenAI ARCS"` 会导致连接 Target 时无限卡死**。必须使用短名 `ARCS`。

## 完整流程摘要

```
1. 检测 JLinkExe / JLinkGDBServerCLExe
   ↓ 缺失则提示安装
2. 检测 JLinkDevices 配置（Listenai.xml + Flashloader.elf）
   ↓ 缺失则自动部署
3. 检测目标核心（AP/CP）→ 选择对应 JLink Script
   ↓ 告知用户当前调试的核心
4. 生成运行时 arcs.jflash（从模板替换占位符）
5. 检测 JLink 硬件序列号
   ↓ 未找到则提示连接硬件
6. 执行连接测试（JLinkExe 读取 flash，纯 CLI）
   ↓ 成功 → "JLink 连接 ARCS 成功"
   ↓ 失败 → 输出错误信息和排查建议
```
