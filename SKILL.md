---
name: intranet-email-sender
version: "1.0.0"
description: "内网邮件发送工具。当用户需要通过企业/组织内部邮箱发送邮件时触发此技能。支持发送带附件（图片、Word、PPT、PDF等任意文件）的邮件到指定收件人，并返回发送状态。适用场景：发送邮件、发邮件、send email、帮我发个邮件、把这个文件发给他、邮件发送、内网邮件、SMTP 发送"
---

# 内网邮件发送 Skill v1.0

通过企业内网 SMTP 服务器发送带附件的电子邮件，支持首次安装引导式配置。

## 功能概览

| 能力 | 说明 |
|------|------|
| **附件支持** | 图片（png/jpg/gif）、Word（docx）、PPT（pptx）、PDF 及任意格式文件 |
| **多收件人** | 支持多个收件人、抄送（CC）、密送（BCC） |
| **正文格式** | 纯文本 / HTML 双模式 |
| **加密方式** | SSL/TLS / STARTTLS / 无加密（适配各类内网环境） |
| **状态返回** | 详细的成功/失败信息，包含耗时、附件大小、被拒收地址等 |

---

## ⚠️ 首次使用：必须先完成配置

**检测逻辑：** 每次调用前，检查 `{skill_dir}/email_config.json` 是否存在。

- **如果不存在 → 进入「首次配置向导」**
- **如果存在 → 直接进入「邮件发送流程」**

### 首次配置向导

当用户首次使用或要求配置时，按以下步骤引导：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 内网邮件 — 首次配置向导
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

检测到尚未配置 SMTP 参数。
要发送内网邮件，请提供以下信息：

① SMTP 服务器地址：
   例如: mail.company.com / smtp.exmail.qq.com / 192.168.1.100
   
② SMTP 端口：
   常用值: 465 (SSL) / 587 (STARTTLS) / 25 (普通)
   默认: 465
   
③ 登录账号（完整邮箱地址）:
   例如: zhangsan@company.com
   
④ 密码或应用专用密码:
   （建议使用应用专用密码，更安全）
   
⑤ 发件显示名称（可选）:
   例如: 张三 / IT运维部
   
⑥ 发件人邮箱地址:
   收件人看到的发件地址
   
⑦ 加密方式:
   1) SSL/TLS (推荐)  ← 默认
   2) STARTTLS
   3) 无加密 (仅内网可信环境)

收集完毕后：
→ 调用 scripts/send_email.py --init-config 进入交互式配置
   或直接将用户输入写入 {skill_dir}/email_config.json

→ 配置保存后执行连接测试
→ 向用户报告测试结果
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 配置文件格式

配置保存在 `{skill_dir}/email_config.json`，格式如下：

```json
{
  "smtp_host": "mail.example.com",
  "smtp_port": 465,
  "use_ssl": true,
  "use_tls": false,
  "username": "zhangsan@example.com",
  "password": "your_password_or_app_token",
  "sender_name": "张三",
  "sender_email": "zhangsan@example.com",
  "timeout": 30,
  "_created_at": "2026-04-28T15:00:00"
}
```

⚠️ **安全提示**: `password` 字段存储的是明文密码或应用专用Token。
配置文件权限已设置为 600（仅所有者可读写）。

---

## 正常工作流：发送邮件

### Step 1: 收集发送要素

从用户请求中提取以下信息（缺少的项需主动询问）：

| 要素 | 必填 | 来源 | 示例 |
|------|------|------|------|
| **收件人** | ✅ | 用户指定 | `lisi@company.com` 或 `a@x.com, b@y.com` |
| **主题** | ✅ | 用户指定或根据内容生成 | `关于XX项目的报告` |
| **正文** | △ | 可选，有则使用 | `请查收附件中的报告...` |
| **附件文件** | △ | 用户提供的文档路径 | `/path/to/report.docx` |
| **抄送/密送** | 选填 | 用户指定 | `boss@company.com` |
| **HTML格式** | 选填 | 有附件图片时可启用 | 自动判断 |

### Step 2: 验证附件文件

对于每个附件路径：
1. 检查文件是否存在（`Path.exists()`）
2. 报告文件大小（人类可读格式）
3. 如果文件不存在 → 立即告知用户并等待修正
4. 如果文件过大（建议单封 25MB 以内）→ 警告用户

### Step 3: 构建并发送邮件

调用脚本执行发送：

```bash
python3 {skill_dir}/scripts/send_email.py \
  --to "收件人地址" \
  --subject "邮件主题" \
  [--body "邮件正文"] \
  [--attachments "附件1,附件2,..."] \
  [--config {skill_dir}/email_config.json] \
  [--html] \
  [--cc "抄送地址"] \
  [--bcc "密送地址"] \
  [--output-json]
```

**参数映射规则：**
- 多个收件人/附件 → 用英文逗号 `,` 分隔
- 中文文件名 → 脚本自动处理 RFC 2047 编码
- 图片附件 → 自动附带为 MIME 类型（image/png, image/jpeg 等）
- Word/PPT/PDF → 自动识别为 application 类型

### Step 4: 返回发送结果

将脚本输出解析后，以清晰的格式反馈给用户：

```
📧 邮件发送结果

状态: ✅ 发送成功 / ❌ 发送失败

详情:
  时间:    2026-04-28 15:30:00
  SMTP:    mail.company.com:465
  发件人:  张三 (zhangsan@company.com)
  收件人:  lisi@company.com
  附件数:  2 个
  📎 报告.docx (1.2 MB)
  📎 截图.png (245 KB)
  耗时:    2.3 秒

[如有错误会显示具体原因]
```

---

## 错误处理指南

| 错误类型 | 可能原因 | 解决方案 |
|----------|---------|---------|
| 认证失败 (AuthenticationError) | 密码错误 / 账号被锁定 / 需要用应用专用密码 | 引导用户重新配置密码；提示开启应用专用密码 |
| 连接被拒绝 (ConnectionRefused) | SMTP服务未启动 / 端口错误 / 防火墙拦截 | 检查端口和防火墙规则 |
| 连接超时 (timeout) | 网络不通 / DNS无法解析 | 检查网络连通性；尝试 ping smtp_host |
| 发件人被拒绝 (SenderRefused) | 发件域名不在白名单 / 未配置SPF/DKIM | 联系IT管理员添加发件域名 |
| 附件不存在 | 文件路径错误 | 让用户确认文件路径是否正确 |

---

## 常见企业邮箱配置参考

详见 `references/config-guide.md`，以下是最常见的几种：

| 邮箱系统 | SMTP地址 | 端口 | 加密方式 | 备注 |
|---------|---------|------|---------|------|
| **腾讯企业邮** | smtp.exmail.qq.com | 465 | SSL | 推荐用应用专用密码 |
| **阿里企业邮** | smtp.qiye.aliyun.com | 465 | SSL | 同上 |
| **Exchange Server** | mail.公司域名 | 587 | STARTTLS | 通常需域账号认证 |
| **自建Postfix** | 自定义IP/域名 | 25 或 587 | TLS/无 | 内网常不用加密 |
| **Coremail** | mail.公司域名 | 465/994 | SSL | 国内高校常用 |
| **网易企业邮** | smtphz.qiye.163.com | 465 | SSL | 同腾讯 |

---

## 安全注意事项

1. **绝不将密码写入 SKILL.md 或任何公开文件中** — 仅存放在 `email_config.json`
2. **推荐使用应用专用密码**而非登录密码 — 各大邮箱都支持生成
3. **配置文件权限设为 600** — 脚本在保存时自动设置
4. **分享此 Skill 时注意排除 `email_config.json`** — 该文件含个人凭证
5. **定期更换密码/Token**
