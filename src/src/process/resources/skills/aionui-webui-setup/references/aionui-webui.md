# BondClaw WebUI 配置指南

## 概述

BondClaw 支持 WebUI 模式，允许通过浏览器访问应用。这对于远程使用 OpenClaw 非常有用。AionUi 提供三种远程连接方式，满足不同场景的需求�?
**重要**：WebUI 配置应通过 BondClaw 设置界面完成，无需使用命令行。本指南将引导你如何在设置界面中完成配置�?

## 三种远程连接方式

| 连接方式                    | 使用场景                     | 描述                                           | 难度       |
| --------------------------- | ---------------------------- | ---------------------------------------------- | ---------- |
| **1. 局域网连接**           | 同一 WiFi/LAN 的设备访�?     | 手机和电脑在同一 WiFi，启�?允许远程访问"       | �?简�?     |
| **2. 远程软件 (Tailscale)** | 跨网络访问（如办公室到家庭） | 使用 VPN 软件�?Tailscale，无需公网 IP 或服务器 | �?非常简�? |
| \*_3. 服务器部�?_           | 多用户访问�?4/7 运行         | 部署在云服务器，通过公网 IP 直接访问           | ⭐⭐ 中等  |

### 如何选择�?

- **同一 WiFi 使用** �?选择 **局域网连接**
- **办公室访问家庭，或手机使用流�?\* �?选择 **远程软件 (Tailscale)\*\*
- **需要多用户访问�?24/7 运行** �?选择 \*_服务器部�?_

---

## 默认配置

- **默认端口**�?5808
- **本地访问地址**：`http://localhost:25808`
- **远程访问地址**：`http://<LAN_IP>:25808`（需要启�?允许远程访问"�?- \*_默认用户�?_：`admin`
- **初始密码**：首次启动时自动生成，在设置界面中显�?

---

## 快速开始：通过设置界面配置 WebUI

### 打开 WebUI 设置界面

**方式 1：通过设置按钮（推荐）**

1. �?BondClaw 主界面，点击左下角的**设置图标**（齿轮图标）
2. 在设置菜单中，点�?**"WebUI"** 选项
3. 进入 WebUI 配置界面

\*_方式 2：通过快捷�?_

- �?BondClaw 主界面，使用快捷键打开设置（具体快捷键请查�?BondClaw 帮助文档�? \*_方式 3：通过路由（WebUI 模式�?_

- 如果已在 WebUI 模式下，访问：`http://<服务器地址>:25808/#/settings/webui`

### 配置步骤

#### Step 1: 启用 WebUI

1. �?WebUI 设置界面中，找到 **"启用 WebUI"** 开�?2. 将开关切换到**开�?\*状�?3. 等待几秒钟，WebUI 服务启动后，会显�?**"�?运行�?\*\* 状�?

#### Step 2: 启用远程访问（如果需要）

1. �?**"允许远程访问"** 选项中，将开关切换到\**开�?*状�?2. 如果 WebUI 正在运行，系统会自动重启以应用新设置

#### Step 3: 获取访问信息

WebUI 启动后，设置界面会显示：

1. **访问地址**�? - **本地访问**：`http://localhost:25808`（仅本机访问�? - **网络访问**：`http://<局域网IP>:25808`（如果启用了远程访问�?
2. **登录信息**�? - **用户�?\*：`admin`（可点击复制�? - **密码\*\*：首次启动时会显示初始密码（可点击复制）
   - 如果密码已隐藏，点击密码旁边�?\*重置图标\*\*可以重置密码并显示新密码

3. \*_二维码登�?_（如果启用了远程访问）：
   - 使用手机扫描二维码，即可在手机浏览器中自动登�? - 二维码有效期 5 分钟，过期后点击"刷新二维�?获取新的二维�?

---

## 方式 1：局域网连接（LAN Connection�?

### 适用场景

- 手机和电脑在同一 WiFi
- 同一局域网内的设备访问
- 临时远程访问

### 配置步骤

#### Step 1: 打开 WebUI 设置界面

1. �?BondClaw 主界面，点击左下角的**设置图标**
2. 点击 **"WebUI"** 选项

#### Step 2: 启用 WebUI 和远程访�?

1. �?**"启用 WebUI"** 开关切换到**开�?\*状�?2. �?**"允许远程访问"** 开关切换到**开�?\*状�?3. 等待服务启动完成

#### Step 3: 复制访问地址

1. 在设置界面中，找�?**"访问地址"** 部分
2. 复制**网络访问地址**（格式：`http://<局域网IP>:25808`�?3. 如果看不到网络访问地址，说�?允许远程访问"未启用，请返�?Step 2

#### Step 4: 在远程设备上访问

1. 确保远程设备�?BondClaw 电脑在同一 WiFi 网络
2. 在远程设备的浏览器中，粘贴并访问复制的地址
3. 使用设置界面中显示的**用户�?*�?*密码**登录

---

## 方式 2：远程软�?(Tailscale) - 跨网络访�?

### 适用场景

- 从办公室访问家庭�?BondClaw
- 从手机（使用流量）访问家庭的 BondClaw
- 需要跨网络访问，但不想配置公网 IP

### 优势

- �?非常简单：安装软件，登录即�?- 🔒 安全：使�?VPN 加密连接
- 🚀 快速：无需配置防火墙或端口转发
- 📱 移动友好：支持手机、平板等设备

### 配置步骤

#### Step 1: �?BondClaw 电脑上配�?WebUI

1. **打开 WebUI 设置界面**�? - �?BondClaw 主界面，点击左下角的**设置图标**
   - 点击 **"WebUI"** 选项

2. **启用 WebUI**�? - �?**"启用 WebUI"** 开关切换到**开�?\*状�? - **注意**：使�?Tailscale 时，**不需�?\*启用"允许远程访问"（Tailscale 会处理网络）

3. **记录访问信息**�? - 记录显示�?*本地访问地址**（`http://localhost:25808`�? - 记录**用户�?*�?\*密码\*\*

#### Step 2: �?BondClaw 电脑上安装并登录 Tailscale

1. 访问 [Tailscale 官网](https://tailscale.com/) 下载并安�?2. 登录 Tailscale 账户（首次使用需要注册）
2. 确保 Tailscale 显示"Connected"状�?

#### Step 3: 获取 Tailscale IP

1. �?BondClaw 电脑上，打开 Tailscale 应用
2. 查看显示�?Tailscale IP 地址（例如：`100.x.x.x`�?3. 组合访问 URL：`http://<Tailscale_IP>:25808`

#### Step 4: 在远程设备上安装并登�?Tailscale

1. 在手机或其他远程设备上安�?Tailscale
2. 使用相同�?Tailscale 账户登录
3. 确保显示"Connected"状�?

#### Step 5: 在远程设备浏览器中访�?

1. 打开浏览�?2. 访问 `http://<Tailscale_IP>:25808`（使�?Step 3 中的地址�?3. 使用设置界面中显示的**用户�?*�?*密码**登录

### 常见命令

```bash
# 查看 Tailscale 状�?tailscale status

# 查看 Tailscale IP
tailscale ip

# 查看所有设�?tailscale status --json
```

---

## 方式 3：服务器部署（Server Deployment�?

### 适用场景

- 需要多用户访问
- 需�?24/7 运行
- 部署在云服务器上
- 通过公网 IP 或域名访�?

### 前置要求

- 云服务器（Linux/macOS�?- 公网 IP 或域�?- 防火墙配置权�?

---

### Linux 服务器部署（推荐�?

#### Step 1: 在服务器上安�?BondClaw

按照 BondClaw 安装指南在服务器上安�?BondClaw 应用�?

#### Step 2: 通过设置界面配置 WebUI

1. **打开 WebUI 设置界面**�? - 如果服务器有图形界面，直接打开 BondClaw 应用
   - 如果服务器无图形界面，需要通过 SSH 端口转发�?VNC 访问图形界面

2. **配置 WebUI**�? - 点击左下角的**设置图标**
   - 点击 **"WebUI"** 选项
   - �?**"启用 WebUI"** 开关切换到**开�?\*状�? - �?**"允许远程访问"** 开关切换到**开�?\*状�?
3. **记录访问信息**�? - 记录显示�?*网络访问地址**（`http://<服务器IP>:25808`�? - 记录**用户�?*�?\*密码\*\*

#### Step 3: 配置防火�?

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 25808/tcp
sudo ufw reload

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=25808/tcp
sudo firewall-cmd --reload

# 或使�?iptables
sudo iptables -A INPUT -p tcp --dport 25808 -j ACCEPT
```

#### Step 4: 配置开机自启（可选）

如果需�?BondClaw 开机自启，可以配置 systemd 服务。但建议通过 BondClaw 设置界面管理 WebUI，而不是通过命令行�?

#### Step 5: 获取访问地址

1. 获取服务器公�?IP�?

   ```bash
   curl ifconfig.me
   # �?   curl ipinfo.io/ip
   ```

2. 访问地址：`http://<公网IP>:25808`

3. 如果配置了域名，可以使用：`http://<域名>:25808`

---

### macOS 服务器部�?

#### Step 1: 在服务器上安�?BondClaw

按照 BondClaw 安装指南�?macOS 服务器上安装 BondClaw 应用�?

#### Step 2: 通过设置界面配置 WebUI

1. 打开 BondClaw 应用
2. 点击左下角的**设置图标**
3. 点击 **"WebUI"** 选项
4. �?**"启用 WebUI"** �?**"允许远程访问"** 开关切换到\**开�?*状�?

#### Step 3: 配置防火�?

```bash
# 允许端口 25808
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/BondClaw.app/Contents/MacOS/BondClaw
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /Applications/BondClaw.app/Contents/MacOS/BondClaw
```

---

## 设置界面功能说明

### WebUI 服务配置

- **启用 WebUI**：启�?停止 WebUI 服务
- **允许远程访问**：启用后，允许局域网内的其他设备访问
- **访问地址**：显示本地和网络访问地址（可点击复制�?

### 登录信息

- **用户�?\*：默�?`admin`（可点击复制�?- **密码\*\*�? - 首次启动时显示初始密码（可点击复制）
  - 如果密码已隐藏，点击**重置图标**可以重置密码并显示新密码
  - 点击**修改密码**可以设置自定义密�?

### 二维码登�?

- 仅在启用远程访问时显�?- 使用手机扫描二维码，即可在手机浏览器中自动登�?- 二维码有效期 5 分钟，过期后点击"刷新二维�?

### Channels 配置

- 配置 Telegram、Lark 等聊天平台的 Bot Token
- 实现通过 IM 应用访问 BondClaw

---

## 故障排查

### WebUI 无法启动

1. **检查端口是否被占用**�? - 在设置界面中，如果启动失败，通常会显示错误信�? - 如果端口被占用，可以修改配置文件中的端口（见下方"自定义端�?�?
2. **检查防火墙设置**�? - Linux: `sudo ufw status` �?`sudo firewall-cmd --list-all`
   - macOS: 系统偏好设置 > 安全性与隐私 > 防火�? - Windows: 控制面板 > Windows Defender 防火�?

### 无法远程访问

1. **确认已启�?允许远程访问"**�? - �?WebUI 设置界面中，检�?允许远程访问"开关是否已开�?
2. **检查防火墙设置**（见上方�?
3. **确认设备在同一局域网**（局域网连接方式�?
4. **检�?IP 地址是否正确**�? - 在设置界面中查看显示�?网络访问地址"

5. **检查云服务器安全组规则**（服务器部署方式�?

### 忘记密码

1. **在设置界面中重置**�? - �?WebUI 设置界面中，找到"登录信息"部分
   - 点击密码旁边�?\*重置图标\*\*
   - 新密码会显示在界面上，可以点击复�?

### Tailscale 相关问题

**Q: Tailscale 显示未连接？**

- 检查网络连�?- 确认 Tailscale 账户已登�?- 重启 Tailscale 服务

\*_Q: 无法通过 Tailscale IP 访问�?_

- 确认两端设备都已登录 Tailscale
- 检�?Tailscale 状态：`tailscale status`
- 确认 BondClaw WebUI 已在设置界面中启�?

---

## 自定义端�?

如果需要使用非默认端口�?5808），可以通过配置文件设置�?

### 配置文件位置

| 平台    | 配置文件位置                                               |
| ------- | ---------------------------------------------------------- |
| Windows | `%APPDATA%/BondClaw/webui.config.json`                     |
| macOS   | `~/Library/Application Support/BondClaw/webui.config.json` |
| Linux   | `~/.config/BondClaw/webui.config.json`                     |

### 配置示例

```json
{
  "port": 8080,
  "allowRemote": true
}
```

## **注意**：修改配置文件后，需要在设置界面中重�?WebUI 服务才能生效�?

## 安全建议

### 基本安全

1. **修改初始密码**：首次启动后，在设置界面中立即修改密�?2. \*_使用强密�?_：密码至�?8 位，包含字母、数字和特殊字符
2. **定期更新密码**：建议定期更换密�?

### 远程访问安全

1. \*_仅在受信任的网络中使用远程访�?_
2. **使用 Tailscale**：跨网络访问时，Tailscale 提供加密连接，更安全
3. \*_配置防火�?_：仅允许必要�?IP 地址访问
4. **使用 HTTPS**：生产环境建议配�?HTTPS（需要反向代理如 Nginx�?

### 服务器部署安�?

1. **配置防火墙规�?\*：仅开放必要端�?2. **使用强密�?\*：避免使用默认或弱密�?3. **定期更新**：保�?BondClaw 和系统更�?4. **监控日志**：定期检查访问日�?5. **考虑使用反向代理**：使�?Nginx 等反向代理，配置 SSL/TLS

### Tailscale 的优�?

- 🔒 **加密连接**：所有流量都经过加密
- 🛡�?**零信任网�?\*：只有授权设备可以访�?- 🚀 **无需配置\*\*：无需配置防火墙或端口转发
- 📱 \*_跨平�?_：支�?Windows、macOS、Linux、iOS、Android

---

## �?OpenClaw 集成

启动 WebUI 后，可以通过浏览器访�?BondClaw，然后：

1. **在首页找�?OpenClaw 入口**（ACP 代理列表�?2. **直接�?OpenClaw 对话**
2. **享受完整�?BondClaw 界面功能**�? - 文件预览和管�? - 多对话管�? - 完整的工具和技能支�?

---

## 相关资源

- [BondClaw Wiki - Remote Internet Access Guide](https://github.com/timyefi/bondclaw/wiki/Remote-Internet-Access-Guide)
- [BondClaw Wiki - WebUI Configuration Guide](https://github.com/timyefi/bondclaw/wiki/WebUI-Configuration-Guide)
- [Tailscale 官方文档](https://tailscale.com/kb/)

---

## 快速参�?

### 设置界面操作

1. **打开设置**：点�?BondClaw 左下角的**设置图标** �?点击 **"WebUI"**
2. **启用 WebUI**：将"启用 WebUI"开关切换到**开�?\*状�?3. **启用远程访问**：将"允许远程访问"开关切换到**开�?\*状态（如果需要）
3. **复制访问地址**：点击访问地址旁边�?\*复制图标\*\*
4. **复制密码**：点击密码旁边的**复制图标**（如果可见）
5. **重置密码**：点击密码旁边的**重置图标**

### 常用检查命令（仅用于故障排查）

```bash
# 检查端�?lsof -i :25808

# 检查进�?ps aux | grep BondClaw

# 获取 IP 地址
ifconfig | grep "inet " | grep -v 127.0.0.1

# 测试连接
curl http://localhost:25808
```
