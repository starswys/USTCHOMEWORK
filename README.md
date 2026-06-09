# 基于国密算法的简易安全即时通讯系统

## 项目简介

本项目实现了一个基于国密算法（SM2/SM3/SM4）的简易安全即时通讯系统，支持：
- 基于SM2的密钥协商
- 消息的数字签名与验证
- 消息的加解密（SM4）

## 项目结构

```
HOMEWORK/
├── src/
│   ├── sm3.py          # SM3哈希算法实现
│   ├── sm4.py          # SM4分组密码算法实现
│   ├── sm2.py          # SM2数字签名算法实现
│   ├── protocol.py     # 安全通信协议
│   └── main.py         # 主程序入口
├── tests/
│   ├── test_sm3.py     # SM3单元测试
│   ├── test_sm4.py     # SM4单元测试
│   └── test_protocol.py # 协议测试
└── docs/
    └── report.md       # 实验报告
```

## 运行说明

```bash
# 运行演示程序
python src/main.py

# 运行单元测试
python -m pytest tests/
```

## 算法说明

- **SM3**: 国密哈希算法，输出256位摘要
- **SM4**: 国密分组密码算法，分组长度128位，密钥长度128位
- **SM2**: 国密公钥密码算法，基于椭圆曲线密码学
