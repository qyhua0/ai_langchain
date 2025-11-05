# Linux磁盘空间告急？快速揪出"空间怪兽"的终极指南

## 1 引言：当Linux磁盘亮起红灯

你是否曾经遇到过这样的恐怖场景：正在部署关键应用时，系统突然提示"No space left on device"？或是服务器监控突然告警，磁盘使用率超过90%？在Linux系统中，磁盘空间不足是一个常见但令人头疼的问题。本文将为你揭示快速定位和清理磁盘空间的终极技巧，让你在磁盘危机面前游刃有余。

### 1.1 为什么需要快速定位大文件？

在生产环境中，磁盘空间不足可能导致：
- 应用程序崩溃或无法启动
- 数据库写入失败，造成数据丢失
- 系统日志无法记录，影响故障排查
- 邮件系统瘫痪，影响业务通信

快速找出占用空间大的目录和文件，成为每个Linux系统管理员的必备技能。

## 2 准备工作：安全第一

在开始清理之前，请务必注意：

### 2.1 备份重要数据
```bash
# 使用tar备份关键目录
tar -czf backup-$(date +%Y%m%d).tar.gz /path/to/important/data
```

### 2.2 识别系统关键目录
避免误删系统文件，特别是：
- `/boot/`：引导文件
- `/etc/`：配置文件
- `/dev/`：设备文件
- 运行中的日志和临时文件

## 3 核心武器：磁盘分析工具详解

### 3.1 du命令：磁盘使用分析的瑞士军刀

`du`（disk usage）命令是Linux中最基本的磁盘空间分析工具。

#### 3.1.1 基础用法：快速查看目录大小
```bash
# 查看当前目录下各子目录的大小
du -h --max-depth=1

# 查看指定目录的大小
du -sh /var/log/
```

参数解释：
- `-h`：以人类可读的格式显示（KB、MB、GB）
- `-s`：只显示总大小，不显示子目录
- `--max-depth=N`：指定显示的目录层级深度

#### 3.1.2 高级技巧：排序和过滤
```bash
# 找出/var目录下最大的5个目录
du -h --max-depth=1 /var/ | sort -hr | head -n 5

# 详细分析，显示所有子目录并排序
du -ah /path/to/directory | sort -hr | head -n 20
```

#### 3.1.3 实战案例：分析日志目录
```bash
# 分析/var/log目录，找出日志占用最大的服务
sudo du -h --max-depth=1 /var/log/ | sort -hr

# 输出示例：
# 4.5G    /var/log/nginx
# 2.1G    /var/log/mysql
# 1.2G    /var/log/audit
```

### 3.2 ncdu：交互式磁盘分析神器

`ncdu`（NCurses Disk Usage）是一个交互式磁盘使用分析工具，比`du`更直观易用。

#### 3.2.1 安装ncdu
```bash
# Ubuntu/Debian
sudo apt-get install ncdu

# CentOS/RHEL
sudo yum install ncdu

# Fedora
sudo dnf install ncdu
```

#### 3.2.2 基本使用方法
```bash
# 扫描当前目录
ncdu

# 扫描指定目录
ncdu /var/log

# 扫描整个系统（需要root权限）
sudo ncdu /
```

#### 3.2.3 ncdu操作指南
在ncdu界面中：
- `↑↓` 键：选择目录或文件
- `Enter` 键：进入选中的目录
- `d` 键：删除选中的文件或目录（谨慎使用）
- `n` 键：按文件名排序
- `s` 键：按文件大小排序
- `q` 键：退出ncdu

#### 3.2.4 高级扫描技巧
```bash
# 排除某些目录（如proc、sys等虚拟文件系统）
sudo ncdu / --exclude /proc --exclude /sys --exclude /dev

# 将扫描结果导出到文件
ncdu -o scan_result.txt /path/to/scan
```

### 3.3 find命令：精准定位大文件

当你知道要找的是大文件而不是目录时，`find`命令是最佳选择。

#### 3.3.1 按大小查找文件
```bash
# 查找当前目录下大于100MB的文件
find . -type f -size +100M

# 查找整个系统中大于1GB的文件
sudo find / -type f -size +1G 2>/dev/null

# 查找指定类型的大文件
find /var/log -name "*.log" -type f -size +50M
```

#### 3.3.2 结合ls显示详细信息
```bash
# 查找并显示文件的详细信息
find /var/log -type f -size +100M -exec ls -lh {} \;

# 更高效的写法（使用xargs）
find /var/log -type f -size +100M -print0 | xargs -0 ls -lh
```

#### 3.3.3 查找并清理旧文件
```bash
# 查找30天前且大于100MB的日志文件
find /var/log -type f -name "*.log" -mtime +30 -size +100M

# 查找并删除（谨慎使用！）
find /var/log -type f -name "*.log.old" -mtime +30 -exec rm -f {} \;
```

### 3.4 其他实用工具

#### 3.4.1 df命令：磁盘空间概览
```bash
# 查看所有文件系统的磁盘使用情况
df -h

# 查看inode使用情况
df -i

# 只显示特定文件系统类型（如ext4）
df -h -t ext4
```

#### 3.4.2 ls命令的排序功能
```bash
# 按文件大小排序显示
ls -lhS

# 按修改时间倒序排列（最近修改的在前）
ls -lht

# 显示隐藏文件并按大小排序
ls -laSh
```

#### 3.4.3 tree命令：目录树状展示
```bash
# 安装tree
sudo apt-get install tree

# 显示目录结构及大小
tree -h --du /path/to/directory

# 只显示前3级目录
tree -L 3 -h --du /var/log
```

## 4 实战演练：系统磁盘清理全流程

### 4.1 案例背景
假设服务器 `/` 分区使用率达到95%，需要紧急清理。

### 4.2 排查步骤

#### 4.2.1 第一步：快速定位问题分区
```bash
df -h
```
输出示例：
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   47G  1.2G  98% /
/dev/sda2       100G   30G   65G  32% /home
```

#### 4.2.2 第二步：分析根目录占用情况
```bash
sudo du -h --max-depth=1 / | sort -hr | head -n 10
```
输出示例：
```
45G     /
25G     /var
10G     /usr
5G      /home
3G      /opt
```

#### 4.2.3 第三步：深入分析/var目录
```bash
sudo du -h --max-depth=1 /var | sort -hr | head -n 10
```

#### 4.2.4 第四步：使用ncdu进行交互式分析
```bash
sudo ncdu /var
```

### 4.3 常见清理目标及处理方法

#### 4.3.1 日志文件清理
```bash
# 检查日志轮转配置
ls -lh /var/log/*.log

# 清空日志文件（而不是删除，避免影响正在写入的程序）
sudo truncate -s 0 /var/log/some-large-log.log

# 使用logrotate管理日志
sudo logrotate -f /etc/logrotate.conf
```

#### 4.3.2 缓存清理
```bash
# 清理包管理器缓存
sudo apt-get clean          # Debian/Ubuntu
sudo yum clean all          # CentOS/RHEL
sudo dnf clean all          # Fedora

# 清理系统临时文件
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*

# 清理用户缓存
rm -rf ~/.cache/*
```

#### 4.3.3 查找并删除核心转储文件
```bash
# 查找core dump文件
find / -name "core" -type f 2>/dev/null
find / -name "*.core" -type f 2>/dev/null

# 确认后删除
sudo find / -name "core" -type f -delete 2>/dev/null
```

## 5 高级技巧与自动化方案

### 5.1 编写磁盘监控脚本

```bash
#!/bin/bash
# disk_monitor.sh - 磁盘空间监控脚本

THRESHOLD=90
CURRENT_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

if [ $CURRENT_USAGE -gt $THRESHOLD ]; then
    echo "警告：根分区使用率超过 ${THRESHOLD}%"
    echo "当前使用率：${CURRENT_USAGE}%"
    echo "大文件列表："
    find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null | head -n 10
fi
```

### 5.2 定期清理计划

将以下内容添加到crontab中实现自动清理：

```bash
# 每周日凌晨3点清理日志和缓存
0 3 * * 0 /usr/bin/apt-get clean
0 3 * * 0 /usr/bin/find /var/log -name "*.log.*" -mtime +30 -delete
0 3 * * 0 /usr/bin/find /tmp -type f -mtime +7 -delete
```

### 5.3 使用系统工具自动化管理

#### 5.3.1 配置logrotate
编辑 `/etc/logrotate.conf` 确保日志得到合理轮转：

```bash
# 示例配置
/var/log/nginx/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 www-data adm
}
```

## 6 预防措施与最佳实践

### 6.1 磁盘空间规划建议

- 为不同用途分配独立分区：`/`、`/home`、`/var`、`/tmp`
- 为日志目录（如`/var/log`）分配足够空间
- 使用LVM以便后续扩展分区

### 6.2 监控告警设置

- 配置磁盘使用率监控（如使用Prometheus + Grafana）
- 设置多级阈值告警（80%警告，90%严重）
- 定期审核日志轮转策略

### 6.3 定期维护任务

- 每月执行一次磁盘使用分析
- 每季度审查和更新清理策略
- 建立文件保留策略文档

## 7 总结

通过本文介绍的工具和技巧，你现在应该能够：

✅ 快速定位磁盘空间占用大的目录和文件
✅ 使用合适的工具进行深入分析
✅ 安全有效地清理不必要的文件
✅ 建立预防机制避免磁盘空间问题

记住，在处理生产环境时，始终遵循"先备份，再操作"的原则。熟练掌握这些磁盘空间管理技能，将使你在面对磁盘危机时更加从容自信。

> **温馨提示**：磁盘空间管理是一个持续的过程，建议将本文中的技巧纳入日常维护流程，防患于未然。