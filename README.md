[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/0xAbolfazl/PyroConfig/blob/main/README.md)
[![fa](https://img.shields.io/badge/lang-fa-blue.svg)](https://github.com/0xAbolfazl/PyroConfig/blob/main/README.fa.md)
# PyroConfig
This project **automatically** collects and publishes V2Ray configurations from Telegram channels **without any human supervision or verification**.


![GitHub last commit](https://img.shields.io/github/last-commit/0xAbolfazl/PyroConfig)
![GitHub license](https://img.shields.io/github/license/0xAbolfazl/PyroConfig)
![GitHub issues](https://img.shields.io/github/issues/0xAbolfazl/PyroConfig)

## Configs 

| Protocol      | Link                           |
|---------------|--------------------------------|
| VLESS         | [`Config/vless.txt`](Configs/vless.txt)         |
| VMess         | [`Config/vmess.txt`](Configs/vmess.txt)         |
| Shadowsocks   | [`Config/shadowsocks.txt`](Configs/shadowsocks.txt) |


## 🚀 Features

- ✅ Automatic configuration collection from multiple sources
- ✅ Update every 6 hours
- ✅ Support for various V2Ray protocols

##  Running Project

### Installing
  1. Clone repository
  ```bash
  git clone https://github.com/0xAbolfazl/PyroConfig.git
  cd PyroConfig
  ```
  2. Install dependencies
  ```bash
  pip install -r requirements.txt
  ```
  
### Configuration
  
   1. Setting environment variables:
  ```env
    API_ID=your_api_id
    API_HASH=your_api_hash
    SESSION_STRING=your_session_string
    CHANNEL_ID=your_channel_id_for_posting_configs
  ```
  - If you dont have SESSION_STRING, generate it using session_generator.py
  
  2. Add your target channels to channels.json for fetching configs from them in this format:
  ```json
  {
      "all_channels" : ["@ch1", "@ch2", "@ch3", "@ch4"]
  }
  ```
### Running

```python
python main.py
```
---
> 🚨 Using this project implies your full acceptance of all potential risks.

