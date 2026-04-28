# 企业内网邮箱 SMTP 配置参考指南

> 本文档收录常见企业邮箱和自建邮件系统的 SMTP 配置参数，供首次配置时参考。

## 目录

1. [腾讯企业邮 (Exmail)](#腾讯企业邮-exmail)
2. [阿里企业邮 (Aliyun Mail)](#阿里企业邮-aliyun-mail)
3. [Microsoft Exchange Server](#microsoft-exchange-server)
4. [自建 Postfix/Dovecot](#自建-postfixdovecot)
5. [Coremail](#coremail)
6. [网易企业邮箱](#网易企业邮箱)
7. [Zimbra](#zimbra)
8. [通用排查清单](#通用排查清单)

---

## 腾讯企业邮 (Exmail)

| 参数 | 值 |
|------|-----|
| SMTP 地址 | `smtp.exmail.qq.com` |
| SSL 端口 | **465** |
| TLS/STARTTLS 端口 | 587 |
| 加密方式 | **SSL/TLS**（推荐） |
| 认证方式 | 账号 + 密码 |

### ⚠️ 重要提示

- **必须使用「客户端专用密码」**，而非登录密码
  - 登录 [腾讯企业邮管理端](https://exmail.qq.com) → 设置 → 客户端密码
  - 或在 Web 邮箱 → 设置 → 账户 → 开启 IMAP/SMTP 服务 → 生成新密码
- 默认情况下 SMTP 服务是开启的，如被禁用需联系管理员

### 配置示例

```json
{
  "smtp_host": "smtp.exmail.qq.com",
  "smtp_port": 465,
  "use_ssl": true,
  "use_tls": false,
  "username": "zhangsan@company.com",
  "password": "客户端专用密码",
  "sender_name": "张三",
  "sender_email": "zhangsan@company.com"
}
```

---

## 阿里企业邮 (Aliyun Mail)

| 参数 | 值 |
|------|-----|
| SMTP 地址 | `smtp.qiye.aliyun.com` |
| SSL 端口 | **465** |
| TLS 端口 | 587 |
| 加密方式 | **SSL/TLS**（推荐） |

### 注意事项

- 同样需要使用**应用专用密码**
- 在阿里云邮箱控制台 → 设置 → POP/SMTP服务 中开启并生成密码
- 单个账号每日发信量有限制，超限会触发风控

---

## Microsoft Exchange Server

Exchange 的 SMTP 配置因版本和网络环境差异较大：

| 参数 | 值 |
|------|-----|
| SMTP 地址 | 通常为 `mail.公司域名` 或 Exchange 服务器内网 IP |
| 常用端口 | **587** (STARTTLS) 或 25 (内部中继) |
| 加密方式 | **STARTTLS**（推荐）或无加密（纯内网） |

### 认证方式

| 场景 | 用户名格式 | 说明 |
|------|-----------|------|
| **域账号认证** | `DOMAIN\username` 或 `username@domain.local` | 最常见的内网场景 |
| **UPN 认证** | `user@company.com` | 需要正确配置 UPN 后缀 |
| **邮箱地址认证** | `user@company.com` | 需要 Exchange 允许基本身份验证 |

### 关键检查点

1. **确认 Exchange 接受中继**: Exchange 默认不允许匿名或普通用户通过 SMTP 发外部邮件。需要在「接收连接器」中添加允许的 IP/用户。
2. **检查发送限制**: 某些组织限制了单封大小（默认 10MB-25MB）或每日发送数量。
3. **TLS 证书问题**: 自签名证书可能导致 Python smtplib 报错，脚本已内置 `check_hostname=False` + `CERT_NONE` 来处理。

### 配置示例（内网）

```json
{
  "smtp_host": "192.168.10.50",
  "smtp_port": 587,
  "use_ssl": false,
  "use_tls": true,
  "username": "COMPANY\\zhangsan",
  "password": "Windows域密码",
  "sender_name": "张三",
  "sender_email": "zhangsan@company.com"
}
```

---

## 自建 Postfix/Dovecot

自建邮件服务器是最灵活的场景：

| 参数 | 建议值 |
|------|-------|
| SMTP 地址 | 邮件服务器 IP 或域名（如 mail.internal.company） |
| 端口 | **25**（内部）/ **587**（提交）/ **465**（SSL） |
| 加密方式 | 内网可不用加密；对外建议 STARTTLS |

### 常见配置要点

1. **Postfix 的 `mynetworks`**: 确保 WorkBuddy 所在机器的 IP 在 `mynetworks` 中，否则会被拒绝中继：
   ```
   # /etc/postfix/main.cf
   mynetworks = 127.0.0.0/8 10.0.0.0/8 192.168.0.0/16 [::1]/128
   ```

2. **SASL 认证**: 如果不在 mynetworks 内，需要配置 SASL 认证：
   ```bash
   # 安装 saslauthd 并配置
   # Postfix main.cf:
   smtpd_sasl_auth_enable = yes
   smtpd_sasl_security_options = noanonymous, noplaintext
   broken_sasl_auth_clients = yes
   ```

3. **防火墙**: 确保对应端口开放：
   ```bash
   # iptables 示例
   -A INPUT -p tcp --dport 25 -j ACCEPT    # SMTP
   -A INPUT -p tcp --dport 587 -j ACCEPT   # Submission
   -A INPUT -p tcp --dport 465 -j ACCEPT   # SMTPS
   ```

---

## Coremail

国内高校和大型政企常用 Coremail 系统：

| 参数 | 值 |
|------|-----|
| SMTP 地址 | `mail.学校域名` 或 `smtp.学校域名` |
| SSL 端口 | **465** 或 **994** |
| TLS 端口 | 587 |

### 注意

- 部分 Coremail 部署使用非标准端口，请咨询本单位 IT 部门
- 高校通常有外发邮件审批机制，首次发送可能需要管理员审核白名单
- 密码可能是统一身份认证密码

---

## 网易企业邮箱

| 参数 | 值 |
|------|-----|
| SMTP 地址 | `smtphz.qiye.163.com` |
| SSL 端口 | **465** |
| TLS 端点 | 587 |

### 设置步骤

1. 登录 [网易企业邮](https://qiye.163.com)
2. 进入「设置」→「POP/SMTP/IMAP」
3. 开启 SMTP 服务
4. 获取授权码（作为密码使用）

---

## Zimbra

| 参数 | 值 |
|------|-----|
| SMTP 地址 | Zimbra 服务器地址 |
| SSL 端口 | **465** |
| TLS 端口 | 587 |

Zimbra 使用完整邮箱地址作为登录名，密码与 Web 登录密码一致。

---

## 通用排查清单

当邮件发送失败时，按以下顺序排查：

### 1️⃣ 网络连通性

```bash
# 测试 TCP 连通性
nc -zv smtp.example.com 465
# 或
telnet smtp.example.com 465

# DNS 解析测试
nslookup smtp.example.com

# ping 测试
ping smtp.example.com
```

### 2️⃣ 账号权限

| 问题 | 检查方法 |
|------|---------|
| SMTP 未开启 | 登录 Web 邮箱查看设置页面 |
| 应用专用密码未生成 | 在安全设置中生成 |
| 发送频率受限 | 查看 IT 政策中的每日限额 |
| IP 白名单 | 联系 IT 确认当前 IP 是否在允许列表中 |
| 收件人被拒 | 检查是否需要先加入通讯录 |

### 3️⃣ 防火墙/代理

- 公司出口防火墙可能封锁了 25 端口（防垃圾邮件）
- 如果在公司内网，可能需要配置 HTTP/SOCKS 代理才能出网
- 某些安全软件可能拦截 SMTP 流量（杀毒软件邮件扫描模块）

### 4️⃣ 证书问题

对于使用自签名证书的内网 Exchange/Postfix 服务器，脚本已内置：
```python
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
```
如果仍然报 SSL 错误，可以尝试将 `use_ssl` 设为 `false`、`use_tls` 也设为 `false`（仅限完全可信的内网环境）。

### 5️⃣ 日志排查

如果以上均正常但仍失败，可以手动用 Python 测试：

```python
import smtplib, ssl

# 替换为你的配置
host = "mail.company.com"
port = 465
user = "test@company.com"
passwd = "your_password"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    server = smtplib.SMTP_SSL(host, port, context=ctx)
    server.ehlo()
    server.login(user, passwd)
    print("✅ 认证成功!")
    server.quit()
except Exception as e:
    print(f"❌ 错误: {e}")
```

---

*最后更新: 2026-04-28*
