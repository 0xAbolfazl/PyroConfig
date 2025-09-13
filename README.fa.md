[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/0xAbolfazl/PyroConfig/blob/main/README.md)
[![fa](https://img.shields.io/badge/lang-fa-blue.svg)](https://github.com/0xAbolfazl/PyroConfig/blob/main/README.fa.md)
# PyroConfig
این پروژه **به طور خودکار** پیکربندی‌های V2Ray را از کانال‌های تلگرام **بدون هیچ گونه نظارت یا تأیید انسانی** جمع‌آوری و منتشر می‌کند.

![آخرین کامیت گیت‌هاب](https://img.shields.io/github/last-commit/0xAbolfazl/PyroConfig)
![مجوز گیت‌هاب](https://img.shields.io/github/license/0xAbolfazl/PyroConfig)
![مشکلات گیت‌هاب](https://img.shields.io/github/issues/0xAbolfazl/PyroConfig)

## پیکربندی‌ها
| Protocol      | Link                           |
|---------------|--------------------------------|
| VLESS         | [`Config/vless.txt`](Configs/vless.txt)         |
| VMess         | [`Config/vmess.txt`](Configs/vmess.txt)         |
| Shadowsocks   | [`Config/shadowsocks.txt`](Configs/shadowsocks.txt) |

## 🚀 ویژگی‌ها

- ✅ جمع‌آوری خودکار پیکربندی از منابع مختلف
- ✅ به‌روزرسانی هر ۶ ساعت
- ✅ پشتیبانی از پروتکل‌های مختلف V2Ray

## اجرای پروژه

### نصب
۱. کلون کردن مخزن
```bash
git clone https://github.com/0xAbolfazl/PyroConfig.git
cd PyroConfig
```
۲. نصب وابستگی‌ها
```bash
pip install -r requirements.txt
```

### پیکربندی

۱. تنظیم متغیرهای محیطی:
```env
API_ID=your_api_id
API_HASH=your_api_hash
SESSION_STRING=your_session_string
CHANNEL_ID=your_channel_id_for_posting_configs
```
- اگر SESSION_STRING ندارید، با استفاده از session_generator.py بسازید 

۲. کانال‌های هدف خود را برای دریافت پیکربندی‌ها از آنها با این فرمت به channels.json اضافه کنید:

```json
{
"all_channels" : ["@ch1", "@ch2", "@ch3", "@ch4"]
}
```
### اجرا کردن کد

```python
python main.py
```
---
> 🚨 استفاده از این پروژه به منزله پذیرش کامل تمام خطرات احتمالی توسط شماست.