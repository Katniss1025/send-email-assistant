#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内网邮件发送引擎 v1.0
功能：通过企业内网SMTP服务器发送带附件的邮件
支持：图片/Word/PPT/PDF/任意文件附件、HTML纯文本双格式、发送状态返回

用法：
  python3 send_email.py --to <收件人> --subject <主题> [--body <正文>] \
                        --attachments <文件1,文件2,...> [--config <配置路径>] \
                        [--html] [--cc <抄送>] [--bcc <密送>]

首次使用前请先运行 --init-config 进行交互式配置，或手动创建 config.json

作者：WorkBuddy Skill - intranet-email-sender
"""

import argparse
import json
import os
import sys
import smtplib
import mimetypes
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate, formataddr
from datetime import datetime
from pathlib import Path


# ============================================================
# 默认配置路径
# ============================================================
DEFAULT_CONFIG_NAME = "email_config.json"
SKILL_DIR = Path(__file__).resolve().parent.parent  # skill根目录
DEFAULT_CONFIG_PATH = SKILL_DIR / DEFAULT_CONFIG_NAME


# ============================================================
# 配置管理
# ============================================================

def get_default_config():
    """返回默认配置模板（空值）"""
    return {
        "smtp_host": "",
        "smtp_port": 465,
        "use_ssl": True,
        "use_tls": False,
        "username": "",       # 发件人邮箱地址
        "password": "",       # 邮箱密码或应用专用密码
        "sender_name": "",    # 显示名称
        "sender_email": "",   # 发件人地址（可与username不同）
        "timeout": 30,
        "_created_at": ""
    }


def load_config(config_path=None):
    """加载配置文件。如果不存在则返回None"""
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    
    config_file = Path(config_path)
    if not config_file.exists():
        return None
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config, config_path=None):
    """保存配置到文件"""
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    config["_created_at"] = config.get("_created_at") or datetime.now().isoformat()
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    # 设置文件权限为仅当前用户可读写（保护密码）
    os.chmod(config_path, 0o600)
    
    return str(config_path.resolve())


def validate_config(config):
    """验证配置完整性，返回 (is_valid, errors_list)"""
    errors = []
    required_fields = ["smtp_host", "username", "password", "sender_email"]
    
    for field in required_fields:
        val = config.get(field, "")
        if not val or val.strip() == "":
            errors.append(f"缺少必填字段: {field}")
    
    # 验证端口范围
    port = config.get("smtp_port", 0)
    if port <= 0 or port > 65535:
        errors.append(f"无效的SMTP端口号: {port}")
    
    return len(errors) == 0, errors


def init_config_interactive():
    """交互式引导用户完成SMTP配置"""
    print("\n" + "=" * 60)
    print("📧 内网邮件发送 — 首次配置向导")
    print("=" * 60)
    print()
    print("本向导将引导你配置企业内网邮箱的SMTP参数。")
    print("配置将保存在: {}".format(DEFAULT_CONFIG_PATH.resolve()))
    print()
    
    config = get_default_config()
    
    # 收集配置信息
    prompts = [
        ("smtp_host", "SMTP服务器地址", 
         "例如: mail.example.com / smtp.exmail.qq.com / 192.168.1.100"),
        ("smtp_port", "SMTP端口 (默认465)", 
         "常用: 465(SSL), 587(TLS/STARTTLS), 25(普通)"),
        ("username", "发件人登录账号", 
         "通常是完整的邮箱地址, 例如: zhangsan@company.com"),
        ("password", "密码或应用专用密码", 
         "建议使用应用专用密码而非登录密码（更安全）"),
        ("sender_name", "发件显示名称 (可选)", 
         "例如: 张三 / IT运维部 — 留空则不设置"),
        ("sender_email", "发件人邮箱地址", 
         "收件人看到的发件地址, 例如: zhangsan@company.com"),
    ]
    
    for key, label, hint in prompts:
        default_val = config.get(key, "")
        
        if key == "smtp_port":
            default_str = str(default_val) if default_val else "465"
            raw = input(f"  [{label}]\n    提示: {hint}\n    值 [{default_str}]: ").strip()
            value = raw if raw else default_str
            try:
                config[key] = int(value)
            except ValueError:
                print(f"    ⚠️ 端口必须是数字，已使用默认值: 465")
                config[key] = 465
        elif key == "password":
            # 密码输入：终端中直接输入（生产环境可考虑getpass）
            raw = input(f"  [{label}]\n    提示: {hint}\n    值: ").strip()
            config[key] = raw
        else:
            raw = input(f"  [{label}]\n    提示: {hint}\n    值 [{default_val}]: ").strip()
            config[key] = raw if raw else default_val
    
    # 加密方式选择
    print()
    print("  [加密方式]")
    print("    1) SSL/TLS (推荐，适用于465端口)")
    print("    2) STARTTLS (适用于587端口)")
    print("    3) 无加密 (不推荐，仅用于内网可信环境)")
    enc_choice = input("    选择 [1]: ").strip() or "1"
    if enc_choice == "2":
        config["use_ssl"] = False
        config["use_tls"] = True
    elif enc_choice == "3":
        config["use_ssl"] = False
        config["use_tls"] = False
    else:
        config["use_ssl"] = True
        config["use_tls"] = False
    
    print()
    
    # 验证并保存
    is_valid, errors = validate_config(config)
    if not is_valid:
        print("❌ 配置验证失败:")
        for err in errors:
            print(f"   - {err}")
        print("\n请重新运行此命令配置。")
        return False, None
    
    saved_path = save_config(config)
    print("✅ 配置已保存至:", saved_path)
    print()
    print("📋 配置摘要:")
    print(f"   SMTP: {config['smtp_host']}:{config['smtp_port']}")
    enc = "SSL/TLS" if config['use_ssl'] else ("STARTTLS" if config['use_tls'] else "无加密")
    print(f"   加密: {enc}")
    masked_user = config['username'][:3] + "***" + config['username'].split('@')[-1] if '@' in config['username'] else "***"
    print(f"   账号: {masked_user}")
    print(f"   发件人: {config.get('sender_name', '')} <{config['sender_email']}>")
    print()
    
    # 测试连接
    test = input("是否立即测试连接? [Y/n]: ").strip().lower()
    if test != 'n':
        success, msg = test_connection(config)
        if success:
            print(f"✅ 连接测试成功: {msg}")
        else:
            print(f"❌ 连接测试失败: {msg}")
            print("   请检查SMTP服务器地址、端口、账号密码是否正确。")
    
    return True, config


# ============================================================
# 连接测试
# ============================================================

def test_connection(config):
    """测试SMTP连接是否可用"""
    try:
        if config["use_ssl"]:
            ctx = ssl_context()
            server = smtplib.SMTP_SSL(
                config["smtp_host"], 
                config["smtp_port"],
                timeout=config.get("timeout", 30),
                context=ctx
            )
        else:
            server = smtplib.SMTP(
                config["smtp_host"],
                config["smtp_port"],
                timeout=config.get("timeout", 30)
            )
            if config["use_tls"]:
                server.starttls(context=ssl_context())
        
        server.ehlo()
        if config.get("username") and config.get("password"):
            server.login(config["username"], config["password"])
        server.quit()
        return True, "认证成功，连接正常"
    except smtplib.SMTPAuthenticationError as e:
        return False, f"认证失败: {e}"
    except smtplib.SMTPConnectError as e:
        return False, f"无法连接到SMTP服务器: {e}"
    except socket.timeout:
        return False, "连接超时，请检查网络和防火墙"
    except Exception as e:
        return False, f"未知错误: {type(e).__name__}: {e}"


def ssl_context():
    """创建SSL上下文"""
    import ssl
    ctx = ssl.create_default_context()
    # 对于自签名证书的内网环境，允许不严格验证
    # 如需更安全，可注释掉下面两行
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


# ============================================================
# 邮件构建与发送
# ============================================================

def build_email(sender_name, sender_email, to_list, subject, body_text, 
                html_body=None, cc_list=None, bcc_list=None, attachment_paths=None):
    """
    构建邮件MIME对象
    
    Args:
        sender_name: 发件显示名称
        sender_email: 发件邮箱
        to_list: 收件人列表 [email, ...]
        subject: 邮件主题
        body_text: 纯文本正文
        html_body: HTML正文 (可选)
        cc_list: 抄送列表 (可选)
        bcc_list: 密送列表 (可选)
        attachment_paths: 附件路径列表 (可选)
    
    Returns:
        MIMEMultipart对象
    """
    msg = MIMEMultipart('mixed')
    
    # 发件人
    if sender_name:
        msg['From'] = formataddr((sender_name, sender_email))
    else:
        msg['From'] = sender_email
    
    # 收件人
    msg['To'] = ', '.join(to_list)
    
    # 抄送
    if cc_list:
        msg['Cc'] = ', '.join(cc_list)
    
    # 主题
    msg['Subject'] = subject
    
    # 日期
    msg['Date'] = formatdate(localtime=True)
    
    # 正文部分 (alternative: 纯文本 + HTML)
    msg_body = MIMEMultipart('alternative')
    
    text_part = MIMEText(body_text or '', 'plain', 'utf-8')
    msg_body.attach(text_part)
    
    if html_body:
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg_body.attach(html_part)
    
    msg.attach(msg_body)
    
    # 附件
    if attachment_paths:
        for filepath in attachment_paths:
            fpath = Path(filepath)
            if not fpath.exists():
                continue
            
            attach_file(msg, fpath)
    
    return msg


def attach_file(msg, filepath):
    """
    将文件作为附件添加到邮件
    
    Args:
        msg: MIMEMultipart对象
        filepath: 文件Path对象
    """
    filename = filepath.name
    mime_type, encoding = mimetypes.guess_type(str(filepath))
    
    if mime_type is None:
        mime_type = 'application/octet-stream'
    
    maintype, subtype = mime_type.split('/', 1)
    
    with open(filepath, 'rb') as f:
        part = MIMEBase(maintype, subtype)
        part.set_payload(f.read())
    
    encoders.encode_base64(part)
    
    # 处理中文文件名（RFC 2047编码）
    from email.header import Header
    part.add_header(
        'Content-Disposition',
        'attachment',
        filename=Header(filename, 'utf-8').encode()
    )
    
    msg.attach(part)


def send_email(config, to_emails, subject, body="", attachments=None,
              html=False, cc=None, bcc=None, html_template=None):
    """
    核心发送函数
    
    Args:
        config: SMTP配置字典
        to_emails: 收件人列表 ['a@b.com', 'c@d.com']
        subject: 邮件主题
        body: 邮件正文
        attachments: 附件路径列表 ['/path/to/file1.docx', '/path/to/img.png']
        html: 是否以HTML格式发送正文
        cc: 抄送列表
        bcc: 密送列表
        html_template: 自定义HTML模板内容（优先于body）
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'details': dict
        }
    """
    details = {
        'timestamp': datetime.now().isoformat(),
        'smtp_host': config['smtp_host'],
        'smtp_port': config['smtp_port'],
        'sender': config.get('sender_email', config.get('username', '')),
        'recipients': to_emails,
        'subject': subject,
        'attachment_count': len(attachments) if attachments else 0,
        'attachments': []
    }
    
    # 验证附件存在
    valid_attachments = []
    if attachments:
        for att_path in attachments:
            p = Path(att_path)
            if p.exists():
                valid_attachments.append(p)
                details['attachments'].append({
                    'name': p.name,
                    'size_bytes': p.stat().st_size,
                    'size_human': _human_size(p.stat().st_size)
                })
            else:
                return {
                    'success': False,
                    'message': f'附件文件不存在: {att_path}',
                    'details': details
                }
    
    try:
        # 构建邮件
        html_body = html_template if html_template else (f"<body><pre>{body}</pre></body>" if html else None)
        
        msg = build_email(
            sender_name=config.get('sender_name', ''),
            sender_email=config.get('sender_email', config.get('username', '')),
            to_list=to_emails,
            subject=subject,
            body_text=body or '',
            html_body=html_body,
            cc_list=cc,
            bcc_list=bcc,
            attachment_paths=valid_attachments
        )
        
        # 所有收件人（用于sendmail）
        all_recipients = list(to_emails)
        if cc:
            all_recipients.extend(cc)
        if bcc:
            all_recipients.extend(bcc)
        
        # 连接SMTP
        start_time = datetime.now()
        
        if config["use_ssl"]:
            ctx = ssl_context()
            server = smtplib.SMTP_SSL(
                config["smtp_host"],
                config["smtp_port"],
                timeout=config.get("timeout", 30),
                context=ctx
            )
        else:
            server = smtplib.SMTP(
                config["smtp_host"],
                config["smtp_port"],
                timeout=config.get("timeout", 30)
            )
            if config["use_tls"]:
                server.starttls(context=ssl_context())
        
        server.ehlo()
        
        # 认证
        if config.get("username") and config.get("password"):
            server.login(config["username"], config["password"])
        
        # 发送
        send_result = server.sendmail(
            config.get('sender_email', config.get('username', '')),
            all_recipients,
            msg.as_string()
        )
        
        server.quit()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # 检查是否有被拒收的地址
        rejected = {}
        if isinstance(send_result, dict):
            for addr, error in send_result.items():
                rejected[addr] = str(error)
        
        success = len(rejected) == 0
        
        details['elapsed_seconds'] = round(elapsed, 2)
        details['rejected_recipients'] = rejected if rejected else {}
        
        if success:
            return {
                'success': True,
                'message': f'✅ 邮件发送成功！共 {len(all_recipients)} 个收件人, {len(valid_attachments)} 个附件',
                'details': details
            }
        else:
            return {
                'success': False,
                'message': f'⚠️ 邮件部分发送成功，{len(rejected)} 个地址被拒绝',
                'details': details
            }
        
    except smtplib.SMTPAuthenticationError as e:
        return {
            'success': False,
            'message': f'❌ SMTP认证失败: 请检查用户名和密码是否正确',
            'details': {**details, 'error': str(e)}
        }
    except smtplib.SMTPRecipientsRefused as e:
        return {
            'success': False,
            'message': f'❌ 收件人被拒绝: 请检查收件人邮箱地址是否正确',
            'details': {**details, 'error': str(e)}
        }
    except smtplib.SMTPSenderRefused as e:
        return {
            'success': False,
            'message': f'❌ 发件人被拒绝: 请检查发件人邮箱是否有发送权限',
            'details': {**details, 'error': str(e)}
        }
    except smtplib.SMTPDataError as e:
        return {
            'success': False,
            'message': f'❌ 邮件数据异常: {e}',
            'details': {**details, 'error': str(e)}
        }
    except smtplib.SMTPConnectError as e:
        return {
            'success': False,
            'message': f'❌ 无法连接SMTP服务器: 请检查主机名和端口是否正确',
            'details': {**details, 'error': str(e)}
        }
    except socket.timeout:
        return {
            'success': False,
            'message': f'❌ 连接超时 ({config.get("timeout", 30)}秒): 请检查网络连通性和防火墙设置',
            'details': details
        }
    except ConnectionRefusedError:
        return {
            'success': False,
            'message': f'❌ 连接被拒绝: SMTP服务可能未启动或端口未开放',
            'details': details
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'❌ 发送异常: {type(e).__name__}: {e}',
            'details': {**details, 'error': str(e)}
        }


def _human_size(size_bytes):
    """将字节数转为人类可读大小"""
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='内网邮件发送工具 v1.0 — 通过SMTP发送带附件的企业邮件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 首次配置
  python3 send_email.py --init-config
  
  # 发送简单文本邮件
  python3 send_email.py --to user@company.com --subject "测试邮件" --body "你好"
  
  # 发送带附件的邮件
  python3 send_email.py --to user@company.com --subject "报告" \\
      --body "请查收附件" --attachments report.docx,data.png
  
  # HTML格式+多收件人+抄送
  python3 send_email.py --to a@b.com,c@d.com --cc e@f.com --subject "通知" \\
      --html --body "<h1>通知</h1><p>详情见附件</p>" --attach doc.pptx
  
  # 使用自定义配置文件
  python3 send_email.py --to user@x.com --subject "测试" --config /path/to/config.json
  
  # 仅测试连接
  python3 send_email.py --test-connection
"""
    )
    
    parser.add_argument('--to', '-t', help='收件人邮箱（多人用逗号分隔）')
    parser.add_argument('--subject', '-s', '-j', help='邮件主题')
    parser.add_argument('--body', '-b', '-m', default='', help='邮件正文')
    parser.add_argument('--attachments', '-a', '--files', '-f', 
                       help='附件文件路径（多个用逗号分隔）')
    parser.add_argument('--html', action='store_true', help='使用HTML格式发送正文')
    parser.add_argument('--cc', help='抄送地址（多人用逗号分隔）')
    parser.add_argument('--bcc', help='密送地址（多人用逗号分隔）')
    parser.add_argument('--config', '-c', help='指定配置文件路径（默认使用skill目录下的email_config.json）')
    parser.add_argument('--init-config', action='store_true', 
                       help='进入交互式配置向导（首次使用必须执行）')
    parser.add_argument('--test-connection', action='store_true', 
                       help='仅测试SMTP连接，不发邮件')
    parser.add_argument('--show-config', action='store_true', 
                       help='查看当前配置（隐藏敏感信息）')
    parser.add_argument('--output-json', action='store_true', 
                       help='以JSON格式输出结果（便于程序解析）')
    
    args = parser.parse_args()
    
    # ---- 初始化配置模式 ----
    if args.init_config:
        ok, cfg = init_config_interactive()
        sys.exit(0 if ok else 1)
    
    # ---- 查看配置模式 ----
    if args.show_config:
        config = load_config(args.config)
        if config is None:
            print("❌ 未找到配置文件。请先运行: python3 send_email.py --init-config")
            sys.exit(1)
        
        # 安全展示（隐藏密码）
        safe_config = dict(config)
        pwd = safe_config.get('password', '')
        if pwd:
            safe_config['password'] = '*' * min(len(pwd), 8) + f"({len(pwd)}字符)"
        
        print(json.dumps(safe_config, ensure_ascii=False, indent=2))
        sys.exit(0)
    
    # ---- 测试连接模式 ----
    if args.test_connection:
        config = load_config(args.config)
        if config is None:
            print("❌ 未找到配置文件。请先运行: python3 send_email.py --init-config")
            sys.exit(1)
        
        ok, msg = test_connection(config)
        print(msg)
        sys.exit(0 if ok else 1)
    
    # ---- 发送模式 ----
    if not args.to or not args.subject:
        parser.print_help()
        print("\n❌ 错误: 必须指定收件人(--to)和主题(--subject)")
        sys.exit(1)
    
    # 加载配置
    config = load_config(args.config)
    if config is None:
        print("❌ 未找到配置文件。")
        print("   请先运行: python3 send_email.py --init-config")
        print("   或指定配置文件: python3 send_email.py ... --config /path/to/config.json")
        sys.exit(1)
    
    # 验证配置
    is_valid, errors = validate_config(config)
    if not is_valid:
        print("❌ 配置无效:")
        for err in errors:
            print(f"   - {err}")
        print("   请运行: python3 send_email.py --init-config 重新配置")
        sys.exit(1)
    
    # 解析收件人和附件
    to_list = [addr.strip() for addr in args.to.split(',') if addr.strip()]
    cc_list = [addr.strip() for addr in args.cc.split(',') if args.cc and addr.strip()] or None
    bcc_list = [addr.strip() for addr in args.bcc.split(',') if args.bcc and addr.strip()] or None
    attach_list = [p.strip() for p in args.attachments.split(',') if args.attachments and p.strip()] or None
    
    # 执行发送
    result = send_email(
        config=config,
        to_emails=to_list,
        subject=args.subject,
        body=args.body,
        attachments=attach_list,
        html=args.html,
        cc=cc_list,
        bcc=bcc_list
    )
    
    # 输出结果
    if args.output_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print()
        print("=" * 50)
        print(result['message'])
        print("-" * 50)
        d = result['details']
        print(f"  时间: {d.get('timestamp', '')}")
        print(f"  SMTP: {d.get('smtp_host', '')}:{d.get('smtp_port', '')}")
        print(f"  发件人: {d.get('sender', '')}")
        print(f"  收件人: {', '.join(d.get('recipients', []))}")
        print(f"  附件数: {d.get('attachment_count', 0)}")
        for att in d.get('attachments', []):
            print(f"    📎 {att['name']} ({att['size_human']})")
        if d.get('elapsed_seconds'):
            print(f"  耗时: {d['elapsed_seconds']}s")
        if result.get('rejected_recipients'):
            print(f"  被拒收: {result['rejected_recipients']}")
        print("=" * 50)
    
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
