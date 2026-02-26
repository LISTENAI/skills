# Serial Log Capture Tools

## 工具检测与安装

在捕获日志前，先检测工具是否已安装：

```bash
# 检测可用工具
for tool in picocom minicom screen ttylog; do
  command -v $tool &>/dev/null && echo "✅ $tool" || echo "❌ $tool (未安装)"
done
```

如果工具未安装，根据发行版提示安装：

| 工具 | Arch Linux | Ubuntu/Debian | RHEL/CentOS |
|------|-----------|---------------|-------------|
| picocom | `sudo pacman -S picocom` | `sudo apt install picocom` | `sudo dnf install picocom` |
| minicom | `sudo pacman -S minicom` | `sudo apt install minicom` | `sudo dnf install minicom` |
| screen | `sudo pacman -S screen` | `sudo apt install screen` | `sudo dnf install screen` |
| ttylog | AUR: `yay -S ttylog` | `sudo apt install ttylog` | — |

> 💡 **AI 代理行为**：若用户系统中工具均未安装，优先推荐安装 `picocom`（最轻量）；若用户有 sudo 权限，可直接执行安装命令；若无权限，告知用户手动安装或联系管理员。无论如何，`screen` 通常是最普遍预装的工具，可优先尝试。

---

## ⚠️ 交互式 vs 非交互式使用场景

**picocom / minicom / screen** 均为交互式 TTY 工具，**不能在非交互式 shell**（脚本、CI/CD、管道）中直接使用。

| 场景 | 推荐工具 |
|------|---------|
| 手动调试（终端直连） | picocom / minicom / screen |
| 脚本自动化 / CI | `stty` + `cat`、`python3 -m serial`、`socat` |
| 长时间无人值守采集 | `ttylog`、`socat` |

### 非交互式脚本捕获方案

```bash
# 方案1：stty + cat（无需额外依赖）
stty -F /dev/ttyUSB0 115200 raw -echo
cat /dev/ttyUSB0 > /tmp/serial.log &
# 采集完成后 kill $!

# 方案2：socat（更可控）
socat /dev/ttyUSB0,b115200,raw,echo=0 - | tee /tmp/serial.log

# 方案3：Python pyserial（跨平台，推荐 CI 场景）
python3 -c "
import serial, sys, time
with serial.Serial('/dev/ttyUSB0', 115200, timeout=1) as s:
    with open('/tmp/serial.log', 'wb') as f:
        end = time.time() + 30  # 采集 30 秒
        while time.time() < end:
            data = s.read(1024)
            if data:
                f.write(data)
                sys.stdout.buffer.write(data)
"
```

安装 pyserial：`pip install pyserial`

---

## ⚠️ DTR 拉低与日志丢失问题

> **重要**：打开串口时若不拉低 DTR，芯片不会重启，会错过启动阶段的关键日志。

大多数嵌入式开发板使用 DTR 信号触发复位：

```bash
# picocom：连接时自动控制 DTR（默认行为）
picocom --lower-dtr -b 115200 /dev/ttyUSB0

# Python pyserial：手动控制 DTR 触发复位
python3 -c "
import serial, time
s = serial.Serial('/dev/ttyUSB0', 115200)
s.dtr = False   # 拉低 DTR → 触发复位
time.sleep(0.1)
s.dtr = True    # 释放
# 现在开始读取完整启动日志
"

# stty：通过 -hupcl 选项控制
stty -F /dev/ttyUSB0 115200 -hupcl
```

> 💡 如果总是丢失启动日志，优先检查 DTR 控制是否正确。

---

## picocom (交互式推荐)

```bash
# 基本连接
picocom -b 115200 /dev/ttyUSB0

# 保存日志到文件
picocom -b 115200 /dev/ttyUSB0 | tee /tmp/serial.log

# 带时间戳
picocom -b 115200 /dev/ttyUSB0 | ts '[%Y-%m-%d %H:%M:%S]' | tee /tmp/serial.log

# 退出: Ctrl+A, Ctrl+X
```

常用波特率：`9600 / 115200 / 921600 / 1500000 / 2000000`

## minicom

```bash
# 连接
minicom -b 115200 -D /dev/ttyUSB0

# 开启日志捕获（连接后按 Ctrl+A, L）
# 日志保存到 ~/minicom.log
```

## screen

```bash
screen /dev/ttyUSB0 115200

# 开启日志: Ctrl+A, H  (写入 screenlog.0)
# 退出: Ctrl+A, K
```

## ttylog

```bash
ttylog -b 115200 -d /dev/ttyUSB0 -f /tmp/serial.log
```

## cat (只读)

```bash
# 快速查看已有数据
cat /dev/ttyUSB0

# 保存
cat /dev/ttyUSB0 > /tmp/serial.log
```

## 常见设备路径

| 场景 | 路径 |
|------|------|
| USB 转串口 | `/dev/ttyUSB0`, `/dev/ttyUSB1` |
| CH340/CP2102 | `/dev/ttyUSB0` |
| FTDI | `/dev/ttyUSB0` |
| 板载 UART | `/dev/ttyS0`, `/dev/ttyS1` |
| ACM 设备 | `/dev/ttyACM0` |

## 权限问题

```bash
# 将用户加入 dialout 组（重启后生效）
sudo usermod -aG dialout $USER

# 临时修改权限
sudo chmod 666 /dev/ttyUSB0
```

## 带时间戳捕获（推荐）

```bash
# 安装 moreutils
sudo pacman -S moreutils  # Arch
sudo apt install moreutils  # Debian/Ubuntu

# 捕获带时间戳的日志
picocom -b 115200 /dev/ttyUSB0 | ts '%.T' | tee /tmp/serial_$(date +%Y%m%d_%H%M%S).log
```
