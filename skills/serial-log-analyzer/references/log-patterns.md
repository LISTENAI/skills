# Log Patterns & Severity Reference

## Severity Levels

| Priority | Keywords | Meaning |
|----------|----------|---------|
| CRITICAL | `HardFault`, `panic`, `assert`, `abort`, `FATAL` | System crash / unrecoverable |
| ERROR | `[E]`, `ERROR`, `error:`, `ERR`, `failed`, `FAILED` | Functional failure |
| WARNING | `[W]`, `WARN`, `warning:`, `deprecated` | Non-fatal issue |
| INFO | `[I]`, `INFO`, `info:` | Normal operation |
| DEBUG | `[D]`, `DEBUG`, `debug:` | Verbose tracing |

## Common Embedded Error Patterns

### Memory Issues
```
heap alloc failed
malloc failed
out of memory
memory corruption
stack overflow
```
→ 检查: 堆大小配置、内存泄漏、栈深度

### Crash / Fault
```
HardFault_Handler
UsageFault
BusFault
MemManage fault
PC = 0x...
LR = 0x...
```
→ 检查: 空指针、越界访问、未对齐访问

### Communication / Peripheral
```
timeout
retry
CRC error
NAK
NACK
i2c error
spi error
uart overflow
```
→ 检查: 硬件连接、波特率配置、时序

### RTOS Issues
```
task stack overflow
deadlock
semaphore timeout
queue full
queue empty
scheduler
```
→ 检查: 任务优先级、栈大小、资源竞争

### Boot / Init Failures
```
init failed
driver init
probe failed
device not found
```
→ 检查: 初始化顺序、依赖关系、硬件存在性

## LISTENAI/CSK Specific Patterns

### 音频
```
[AUDIO] codec init failed
[AUDIO] underrun
[AUDIO] overrun
```

### 蓝牙
```
[BT] connection failed
[BT] hci error
[BT] l2cap
```

### DSP
```
[DSP] load failed
[DSP] timeout
[ALG] init error
```

## Log → Source Code Mapping

### 步骤
1. 提取 log tag: `[MODULE]` 或 `TAG = "MODULE"`
2. 搜索 TAG 定义:
   ```bash
   grep -rn 'LOG_TAG\s*=\s*"MODULE"\|#define TAG.*"MODULE"' src/
   ```
3. 搜索日志字符串:
   ```bash
   grep -rn "error message fragment" src/
   ```
4. 确认调用点后，读取上下文（函数入参、条件分支、返回值）

### 常见日志宏
```c
LOG_ERR("message %d", val);      // Zephyr
ESP_LOGE(TAG, "message %d", val); // ESP-IDF
pr_err("message %d\n", val);      // Linux kernel
printk(KERN_ERR "message\n");     // Linux kernel
```

## Crash Dump Analysis

当看到 crash dump 时，提取关键字段：
```
PC (Program Counter)  → 崩溃位置
LR (Link Register)    → 调用来源
SP (Stack Pointer)    → 栈状态
Backtrace / Call Stack → 调用链
```

使用 addr2line 映射到源码：
```bash
arm-none-eabi-addr2line -e firmware.elf -f 0x<PC_value>
```
