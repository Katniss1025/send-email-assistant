# 📧 内网邮件发送助手 (Intranet Email Sender)

> 通过企业内网 SMTP 发送带附件邮件的 WorkBuddy Skill —— 支持图片、Word、PPT、PDF 等任意文件

![Skill Type](https://img.shields.io/badge/Type-WorkBuddy_Skill-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.7%2B-yellow)

## ✨ 功能特性

| 特性 | 说明 |
|------|------|
| 📎 **多附件发送** | 支持图片、Word、PPT、PDF 等任意类型文件 |
| 🔒 **内网适配** | 支持 SSL / TLS / STARTTLS / 无加密四种模式 |
| 🌐 **中文友好** | 自动处理中文文件名编码（RFC 2047） |
| 🚀 **首次引导** | 首次使用自动进入交互式配置向导 |
| ✅ **连接测试** | 发送前可测试 SMTP 连通性 |
| 📊 **状态返回** | 支持纯文本和 JSON 两种输出格式 |
| 🔐 **安全存储** | 凭证本地保存，权限 600，仅所有者可读写 |

## 🚀 快速开始

### 前提条件

- [WorkBuddy](https://www.codebuddy.cn/) 客户端
- Python 3.7+（系统自带即可）
- 企业邮箱的 SMTP 服务信息（主机、端口、账号、密码或应用专用密码）

> 💡 **推荐使用应用专用密码**而非登录密码，更安全。腾讯企业邮、阿里企业邮、Exchange 等都支持生成应用专用密码。

### 安装

#### 方式一：Git 克隆（推荐）

```bash
# 进入 skills 目录
cd ~/.workbuddy/skills/

# 克隆仓库
git clone https://github.com/Katniss1025/send-email-assistant.git intranet-email-sender

# 完成！下次对话自动生效
```

#### 方式二：手动下载

1. 下载 [最新 Release](https://github.com/Katniss1025/send-email-assistant/releases) 的 zip 包
2. 解压到 `~/.workbuddy/skills/intranet-email-sender/` 目录
3. 重启 WorkBuddy 客户端

### 首次配置

安装后首次触发该技能时，会自动检测到尚未配置，并引导你完成 SMTP 设置：

```
你：帮我发个邮件
🤖 检测到尚未配置邮件发送服务，进入首次配置向导：

  请输入以下信息：
  1. SMTP 主机地址：smtp.company.com
  2. SMTP 端口：465
  3. 加密方式 (ssl/tls/starttls/none)：ssl
  4. 发件人邮箱：yourname@company.com
  5. 密码/应用专用密码：********
  6. 显示名称（可选）：张三

🔧 正在测试连接...
✅ 连接成功！配置已保存。
```

也可以手动运行配置命令：

```bash
python3 ~/.workbuddy/skills/intranet-email-sender/scripts/send_email.py --init-config
```

## 📖 使用方法

### 触发词

说以下任意一句话即可触发：

- "帮我发个邮件"
- "把这个文件发给 xxx@xxx.com"
- "发邮件给..."
- "send email"
- "把报告发送给他"
- "邮件发送"

### 使用示例

#### 示例 1：发送单个附件

```
你：把这个报告发给 lisi@company.com

🤖 已识别：
   收件人: lisi@company.com
   附件: 项目季度报告.docx
   
   正在发送... ✅ 发送成功！
```

#### 示例 2：发送多附件并指定主题

```
你：帮我把这些文件发给 wangwu@company.com，主题是"会议资料"

🤖 已识别：
   收件人: wangwu@company.com
   主题: 会议资料
   附件: 会议纪要.docx, 数据分析.xlsx, 封面图.png
   
   正在发送... ✅ 发送成功！
```

#### 示例 3：带抄送和正文

```
你：发送邮件给 a@company.com，抄送给 b@company.com，正文说"请查收附件"

🤖 正在发送...
✅ 发送成功！
```

### 命令行直接调用

你也可以直接通过命令行调用脚本：

```bash
python3 {skill_dir}/scripts/send_email.py \
  --to "recipient@company.com" \
  --subject "邮件主题" \
  --body "邮件正文内容" \
  --attachments "file1.pdf,file2.png" \
  --cc "cc@company.com" \
  --bcc "bcc@company.com" \
  --html \
  --output-json
```

**参数说明：**

| 参数 | 必填 | 说明 |
|------|------|------|
| `--to` | ✅ | 收件人地址（多个用逗号分隔） |
| `--subject` | ✅ | 邮件主题 |
| `--body` | ❌ | 邮件正文（默认自动生成） |
| `--attachments` | ❌ | 附件路径（多个用逗号分隔） |
| `--config` | ❌ | 配置文件路径（默认 `{skill_dir}/email_config.json`） |
| `--html` | ❌ | 以 HTML 格式发送正文 |
| `--cc` | ❌ | 抄送地址 |
| `--bcc` | ❌ | 密送地址 |
| `--output-json` | ❌ | 以 JSON 格式输出结果 |
| `--init-config` | ❌ | 启动交互式配置向导 |
| `--test-connection` | ❌ | 仅测试 SMTP 连通性 |

## 🔧 支持的企业邮箱系统

| 邮箱系统 | SMTP 主机 | 端口(SSL) | 端口(TLS) | 备注 |
|----------|-----------|-----------|-----------|------|
| **腾讯企业邮** | smtp.exmail.qq.com | 465 | 587 | 需开启客户端专用密码 |
| **阿里企业邮** | smtp.qiye.aliyun.com | 465 | 587 | 同上 |
| **Microsoft Exchange** | 自定义地址 | 465 / 25 | 587 | 通常需域账号 + 密码 |
| **Coremail** | 自定义地址 | 465 | 587 | 国内高校常用 |
| **网易企业邮** | smtpon.qiye.163.com | 465 / 994 | 587 | - |
| **Postfix** | 自定义地址 | 465 | 587 | 自建邮件服务器 |
| **Zimbra** | 自定义地址 | 465 | 587 | 开源方案 |

> 📋 更详细的配置说明请参考 [`references/config-guide.md`](references/config-guide.md)

## 📁 项目结构

```
intranet-email-sender/
├── README.md                      ← 你正在看的文档
├── SKILL.md                       ← WorkBuddy 技能定义文件
├── scripts/
│   └── send_email.py              ← 🔧 核心发送引擎（Python）
└── references/
    └── config-guide.md            ← 企业邮箱详细配置指南
```

## ⚠️ 注意事项

1. **附件大小**：建议单封邮件附件总大小不超过 25MB（大多数企业邮箱的限制）
2. **密码安全**：推荐使用应用专用密码而非登录密码；配置文件权限已设置为 600
3. **网络环境**：确保你的机器可以访问企业内网 SMTP 服务器（可能需要 VPN 或内网环境）
4. **自签名证书**：部分内网 SMTP 服务器使用自签名证书，本工具已自动兼容（`check_hostname=False`）

## 🛠️ 故障排查

| 问题 | 可能原因 | 解决方法 |
|------|----------|----------|
| 连接被拒绝 | SMTP 地址/端口错误 | 检查主机名和端口号 |
| 认证失败 | 账号或密码错误 | 确认账号密码是否正确，是否需要应用专用密码 |
| 超时 | 网络不通或防火墙拦截 | 检查是否在内网环境，确认防火墙规则 |
| 证书错误 | 自签名证书 | 工具已自动处理此情况 |
| 附件过大 | 超出邮件服务器限制 | 分批发送或压缩附件 |

## 📄 License

[MIT License](LICENSE) — 自由使用、修改和分发。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

** Made with ❤️ for WorkBuddy Users**
