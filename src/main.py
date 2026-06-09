"""
基于国密算法的简易安全即时通讯系统
主程序入口和完整演示
"""

import os
import sys
import io
import time
import hashlib

# 设置UTF-8编码（解决Windows终端乱码问题）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sm3 import sm3_hash, sm3_hash_hex
from sm4 import sm4_ecb_encrypt, sm4_ecb_decrypt, sm4_cbc_encrypt, sm4_cbc_decrypt
from sm2 import (
    generate_keypair, ec_mul, sign, verify, 
    encrypt as sm2_encrypt, decrypt as sm2_decrypt,
    Gx, Gy, N, P
)
from protocol import SecureMessenger, Message


def demo_sm3():
    """SM3哈希算法演示"""
    print("=" * 60)
    print("SM3哈希算法演示")
    print("=" * 60)
    
    test_cases = [
        (b"", "空字符串"),
        (b"abc", "字符串'abc'"),
        (b"SM3 Hash Algorithm", "字符串'SM3 Hash Algorithm'"),
        (b"Hello, World!", "字符串'Hello, World!'"),
    ]
    
    for msg, desc in test_cases:
        hash_value = sm3_hash_hex(msg)
        print(f"\n输入: {desc}")
        print(f"哈希: {hash_value}")
    
    # 演示雪崩效应
    print("\n--- 雪崩效应测试 ---")
    msg1 = b"Hello, World!"
    msg2 = b"Hello, World?"  # 仅一个字符不同
    hash1 = sm3_hash_hex(msg1)
    hash2 = sm3_hash_hex(msg2)
    print(f"消息1: {msg1.decode()}")
    print(f"哈希1: {hash1}")
    print(f"消息2: {msg2.decode()}")
    print(f"哈希2: {hash2}")
    
    # 统计不同位数
    diff_bits = sum(bin(a ^ b).count('1') for a, b in zip(bytes.fromhex(hash1), bytes.fromhex(hash2)))
    print(f"不同位数: {diff_bits}/256")


def demo_sm4():
    """SM4分组密码算法演示"""
    print("\n" + "=" * 60)
    print("SM4分组密码算法演示")
    print("=" * 60)
    
    # 密钥和明文
    key = bytes([0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF,
                 0xFE, 0xDC, 0xBA, 0x98, 0x76, 0x54, 0x32, 0x10])
    
    print(f"密钥: {key.hex()}")
    
    # ECB模式测试
    print("\n--- ECB模式 ---")
    plaintext = b"SM4 ECB Mode Test!"
    print(f"明文: {plaintext.decode()}")
    print(f"明文长度: {len(plaintext)} 字节")
    
    ciphertext = sm4_ecb_encrypt(plaintext, key)
    print(f"密文: {ciphertext.hex()}")
    
    decrypted = sm4_ecb_decrypt(ciphertext, key)
    print(f"解密: {decrypted.decode()}")
    print(f"验证: {decrypted == plaintext}")
    
    # CBC模式测试
    print("\n--- CBC模式 ---")
    iv = os.urandom(16)
    print(f"IV: {iv.hex()}")
    
    plaintext = b"SM4 CBC Mode Test with IV!"
    print(f"明文: {plaintext.decode()}")
    
    ciphertext = sm4_cbc_encrypt(plaintext, key, iv)
    print(f"密文: {ciphertext.hex()}")
    
    decrypted = sm4_cbc_decrypt(ciphertext, key, iv)
    print(f"解密: {decrypted.decode()}")
    print(f"验证: {decrypted == plaintext}")
    
    # 加密效率测试
    print("\n--- 加密效率测试 ---")
    test_data = os.urandom(1024 * 1024)  # 1MB数据
    
    start_time = time.time()
    for _ in range(10):
        ct = sm4_ecb_encrypt(test_data, key)
    ecb_time = time.time() - start_time
    
    start_time = time.time()
    for _ in range(10):
        ct = sm4_cbc_encrypt(test_data, key, iv)
    cbc_time = time.time() - start_time
    
    print(f"ECB模式加密10次1MB数据: {ecb_time:.3f}秒")
    print(f"CBC模式加密10次1MB数据: {cbc_time:.3f}秒")
    print(f"ECB速度: {10 * 1024 / ecb_time:.2f} MB/s")
    print(f"CBC速度: {10 * 1024 / cbc_time:.2f} MB/s")


def demo_sm2():
    """SM2椭圆曲线密码算法演示"""
    print("\n" + "=" * 60)
    print("SM2椭圆曲线密码算法演示")
    print("=" * 60)
    
    # 生成密钥对
    print("\n--- 密钥生成 ---")
    private_key, public_key = generate_keypair()
    print(f"私钥: {hex(private_key)}")
    print(f"公钥X: {hex(public_key[0])}")
    print(f"公钥Y: {hex(public_key[1])}")
    
    # 数字签名
    print("\n--- 数字签名 ---")
    message = b"This is a test message for SM2 signature!"
    print(f"消息: {message.decode()}")
    
    signature = sign(message, private_key)
    print(f"签名r: {hex(signature[0])}")
    print(f"签名s: {hex(signature[1])}")
    
    # 签名验证
    print("\n--- 签名验证 ---")
    valid = verify(message, signature, public_key)
    print(f"验证结果: {'成功' if valid else '失败'}")
    
    # 篡改检测
    tampered = b"This is a tampered message!"
    valid_tampered = verify(tampered, signature, public_key)
    print(f"篡改验证: {'成功' if valid_tampered else '失败（预期）'}")
    
    # 加密解密
    print("\n--- 加密解密 ---")
    plaintext = b"Hello, SM2 Encryption!"
    print(f"明文: {plaintext.decode()}")
    
    ciphertext = sm2_encrypt(plaintext, public_key)
    print(f"密文长度: {len(ciphertext)} 字节")
    
    decrypted = sm2_decrypt(ciphertext, private_key)
    print(f"解密: {decrypted.decode()}")
    print(f"验证: {decrypted == plaintext}")


def demo_protocol():
    """安全通信协议演示"""
    print("\n" + "=" * 60)
    print("安全通信协议演示")
    print("=" * 60)
    
    # 创建通讯系统
    messenger = SecureMessenger()
    
    # 用户注册
    print("\n--- 用户注册 ---")
    alice = messenger.register_user("Alice")
    bob = messenger.register_user("Bob")
    charlie = messenger.register_user("Charlie")
    
    # 密钥协商
    print("\n--- 密钥协商 ---")
    key_ab = messenger.compute_shared_key("Alice", "Bob")
    key_ac = messenger.compute_shared_key("Alice", "Charlie")
    print(f"Alice-Bob共享密钥: {sm3_hash_hex(key_ab)[:32]}...")
    print(f"Alice-Charlie共享密钥: {sm3_hash_hex(key_ac)[:32]}...")
    
    # 安全通信
    print("\n--- 安全通信 ---")
    
    # Alice发送消息给Bob
    msg1 = messenger.send_message("Alice", "Bob", "你好Bob！这是Alice发送的加密消息。")
    decrypted1 = messenger.receive_message(msg1)
    print(f"  解密结果: {decrypted1}")
    
    # Bob回复Alice
    msg2 = messenger.send_message("Bob", "Alice", "收到Alice！这是Bob的回复。")
    decrypted2 = messenger.receive_message(msg2)
    print(f"  解密结果: {decrypted2}")
    
    # Alice发送消息给Charlie
    msg3 = messenger.send_message("Alice", "Charlie", "你好Charlie，这是私密消息。")
    decrypted3 = messenger.receive_message(msg3)
    print(f"  解密结果: {decrypted3}")
    
    # 消息完整性验证
    print("\n--- 消息完整性 ---")
    msg_hash = messenger.get_message_hash(msg1)
    print(f"消息哈希: {msg_hash}")
    
    # 用户认证
    print("\n--- 用户认证 ---")
    challenge = os.urandom(32)
    print(f"挑战值: {challenge.hex()[:32]}...")
    
    # Alice认证
    response = messenger.authenticate_user("Alice", challenge)
    if response:
        valid = messenger.verify_authentication("Alice", challenge, response)
        print(f"Alice认证: {'成功' if valid else '失败'}")
    
    # 尝试伪造认证
    fake_response = os.urandom(64)
    valid_fake = messenger.verify_authentication("Alice", challenge, fake_response)
    print(f"伪造认证: {'成功' if valid_fake else '失败（预期）'}")
    
    # 多轮对话
    print("\n--- 多轮对话 ---")
    for i in range(3):
        msg = messenger.send_message("Alice", "Bob", f"第{i+1}条消息")
        messenger.receive_message(msg)


def main():
    """主函数"""
    print("=" * 60)
    print("基于国密算法的简易安全即时通讯系统")
    print("SM2 + SM3 + SM4")
    print("=" * 60)
    
    try:
        # SM3演示
        demo_sm3()
        
        # SM4演示
        demo_sm4()
        
        # SM2演示
        demo_sm2()
        
        # 协议演示
        demo_protocol()
        
        print("\n" + "=" * 60)
        print("所有演示完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
