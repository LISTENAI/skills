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

## picocom (推荐)

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
