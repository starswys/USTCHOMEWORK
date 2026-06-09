"""
基于国密算法的安全通信协议实现
支持密钥协商、数字签名、消息加密
"""

import os
import sys
import io
import time
import json
import hashlib
from typing import Tuple, Dict, Optional
from dataclasses import dataclass

# 导入国密算法模块
from sm2 import (
    generate_keypair, ec_mul, sign, verify, 
    encrypt, decrypt, Gx, Gy, N
)
from sm3 import sm3_hash, sm3_hash_hex
from sm4 import sm4_cbc_encrypt, sm4_cbc_decrypt


@dataclass
class User:
    """用户类"""
    user_id: str
    private_key: int
    public_key: Tuple[int, int]
    id_bytes: bytes  # SM2签名用的ID


@dataclass
class Message:
    """消息类"""
    sender_id: str
    receiver_id: str
    content: bytes
    timestamp: float
    signature: Optional[Tuple[int, int]] = None
    ciphertext: Optional[bytes] = None
    iv: Optional[bytes] = None
    mac: Optional[bytes] = None


class SecureMessenger:
    """安全即时通讯系统"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.shared_keys: Dict[Tuple[str, str], bytes] = {}  # 共享密钥
        self.message_log: list = []
    
    def register_user(self, user_id: str) -> User:
        """
        注册新用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            新创建的用户对象
        """
        private_key, public_key = generate_keypair()
        id_bytes = user_id.encode().ljust(16, b'\0')[:16]  # 128位ID
        
        user = User(
            user_id=user_id,
            private_key=private_key,
            public_key=public_key,
            id_bytes=id_bytes
        )
        
        self.users[user_id] = user
        print(f"[注册] 用户 {user_id} 注册成功")
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户信息"""
        return self.users.get(user_id)
    
    def get_public_key(self, user_id: str) -> Optional[Tuple[int, int]]:
        """获取用户公钥"""
        user = self.users.get(user_id)
        return user.public_key if user else None
    
    def compute_shared_key(self, sender_id: str, receiver_id: str) -> bytes:
        """
        计算共享密钥（基于ECDH密钥协商）
        
        Args:
            sender_id: 发送方ID
            receiver_id: 接收方ID
        
        Returns:
            共享密钥（16字节，用于SM4）
        """
        sender = self.users.get(sender_id)
        receiver = self.users.get(receiver_id)
        
        if not sender or not receiver:
            raise ValueError("用户不存在")
        
        # 检查缓存
        key_pair = tuple(sorted([sender_id, receiver_id]))
        if key_pair in self.shared_keys:
            return self.shared_keys[key_pair]
        
        # ECDH密钥协商
        # 共享密钥 = dA * PB = dB * PA
        shared_point = ec_mul(sender.private_key, receiver.public_key)
        
        # 使用SM3派生共享密钥（确保与调用顺序无关）
        # 使用排序后的用户ID确保一致性
        id1, id2 = key_pair
        shared_data = (shared_point[0].to_bytes(32, 'big') + 
                      shared_point[1].to_bytes(32, 'big') +
                      id1.encode() + id2.encode())
        
        # 派生出16字节用于SM4，32字节用于其他用途
        full_key = sm3_hash(shared_data)
        
        # 缓存共享密钥
        self.shared_keys[key_pair] = full_key
        
        return full_key
    
    def get_shared_key(self, user1_id: str, user2_id: str) -> bytes:
        """获取共享密钥"""
        key_pair = tuple(sorted([user1_id, user2_id]))
        if key_pair not in self.shared_keys:
            return self.compute_shared_key(user1_id, user2_id)
        return self.shared_keys[key_pair]
    
    def sign_message(self, sender_id: str, message: bytes) -> Tuple[int, int]:
        """
        对消息进行数字签名
        
        Args:
            sender_id: 发送方ID
            message: 待签名消息
        
        Returns:
            签名值(r, s)
        """
        user = self.users.get(sender_id)
        if not user:
            raise ValueError("用户不存在")
        
        signature = sign(message, user.private_key, user.id_bytes)
        return signature
    
    def verify_signature(self, sender_id: str, message: bytes, 
                        signature: Tuple[int, int]) -> bool:
        """
        验证数字签名
        
        Args:
            sender_id: 发送方ID
            message: 原消息
            signature: 签名值
        
        Returns:
            验证结果
        """
        user = self.users.get(sender_id)
        if not user:
            raise ValueError("用户不存在")
        
        return verify(message, signature, user.public_key, user.id_bytes)
    
    def encrypt_message(self, sender_id: str, receiver_id: str, 
                       message: bytes) -> Tuple[bytes, bytes, Tuple[int, int]]:
        """
        加密消息
        
        Args:
            sender_id: 发送方ID
            receiver_id: 接收方ID
            message: 明文消息
        
        Returns:
            (密文, IV, 签名)
        """
        # 获取共享密钥
        full_key = self.get_shared_key(sender_id, receiver_id)
        sm4_key = full_key[:16]  # SM4密钥
        
        # 生成随机IV
        iv = os.urandom(16)
        
        # 使用SM4-CBC加密
        ciphertext = sm4_cbc_encrypt(message, sm4_key, iv)
        
        # 计算消息认证码（HMAC）
        mac = sm3_hash(iv + ciphertext + full_key)
        
        # 对密文进行签名
        signature = self.sign_message(sender_id, iv + ciphertext + mac)
        
        return ciphertext, iv, signature
    
    def decrypt_message(self, sender_id: str, receiver_id: str,
                       ciphertext: bytes, iv: bytes, 
                       signature: Tuple[int, int]) -> Optional[bytes]:
        """
        解密消息并验证签名
        
        Args:
            sender_id: 发送方ID
            receiver_id: 接收方ID
            ciphertext: 密文
            iv: 初始化向量
            signature: 签名值
        
        Returns:
            解密后的明文，验证失败返回None
        """
        # 获取共享密钥
        full_key = self.get_shared_key(sender_id, receiver_id)
        sm4_key = full_key[:16]  # SM4密钥
        
        # 验证签名
        sign_data = iv + ciphertext + sm3_hash(iv + ciphertext + full_key)
        if not self.verify_signature(sender_id, sign_data, signature):
            print("[安全] 签名验证失败！消息可能被篡改")
            return None
        
        # 解密
        try:
            plaintext = sm4_cbc_decrypt(ciphertext, sm4_key, iv)
            return plaintext
        except Exception as e:
            print(f"[错误] 解密失败: {e}")
            return None
    
    def send_message(self, sender_id: str, receiver_id: str, 
                    message: str) -> Message:
        """
        发送安全消息
        
        Args:
            sender_id: 发送方ID
            receiver_id: 接收方ID
            message: 消息内容
        
        Returns:
            消息对象
        """
        # 加密消息
        ciphertext, iv, signature = self.encrypt_message(
            sender_id, receiver_id, message.encode()
        )
        
        # 计算MAC
        full_key = self.get_shared_key(sender_id, receiver_id)
        mac = sm3_hash(iv + ciphertext + full_key)
        
        # 创建消息对象
        msg = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=message.encode(),
            timestamp=time.time(),
            signature=signature,
            ciphertext=ciphertext,
            iv=iv,
            mac=mac
        )
        
        self.message_log.append(msg)
        print(f"[发送] {sender_id} -> {receiver_id}: {message[:30]}...")
        
        return msg
    
    def receive_message(self, msg: Message) -> Optional[str]:
        """
        接收并解密消息
        
        Args:
            msg: 消息对象
        
        Returns:
            解密后的消息内容，验证失败返回None
        """
        plaintext = self.decrypt_message(
            msg.sender_id,
            msg.receiver_id,
            msg.ciphertext,
            msg.iv,
            msg.signature
        )
        
        if plaintext:
            # 验证MAC
            full_key = self.get_shared_key(msg.sender_id, msg.receiver_id)
            expected_mac = sm3_hash(msg.iv + msg.ciphertext + full_key)
            
            if msg.mac != expected_mac:
                print("[安全] MAC验证失败！消息完整性被破坏")
                return None
            
            decoded = plaintext.decode('utf-8', errors='ignore')
            print(f"[接收] {msg.sender_id} -> {msg.receiver_id}: {decoded[:30]}...")
            return decoded
        
        return None
    
    def authenticate_user(self, user_id: str, challenge: bytes) -> Optional[bytes]:
        """
        用户认证（挑战-响应协议）
        
        Args:
            user_id: 用户ID
            challenge: 挑战值
        
        Returns:
            签名后的挑战值
        """
        user = self.users.get(user_id)
        if not user:
            return None
        
        # 对挑战值进行签名
        response = sign(challenge, user.private_key, user.id_bytes)
        
        # 将(r, s)转换为字节
        r_bytes = response[0].to_bytes(32, 'big')
        s_bytes = response[1].to_bytes(32, 'big')
        
        return r_bytes + s_bytes
    
    def verify_authentication(self, user_id: str, challenge: bytes, 
                            response: bytes) -> bool:
        """
        验证认证响应
        
        Args:
            user_id: 用户ID
            challenge: 挑战值
            response: 响应值
        
        Returns:
            认证结果
        """
        user = self.users.get(user_id)
        if not user:
            return False
        
        # 解析响应
        r = int.from_bytes(response[:32], 'big')
        s = int.from_bytes(response[32:], 'big')
        
        # 验证签名
        return verify(challenge, (r, s), user.public_key, user.id_bytes)
    
    def get_message_hash(self, msg: Message) -> str:
        """计算消息的哈希摘要"""
        hash_data = (msg.sender_id.encode() + msg.receiver_id.encode() +
                    msg.ciphertext + msg.iv + 
                    int(msg.timestamp).to_bytes(8, 'big'))
        return sm3_hash_hex(hash_data)


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("国密安全即时通讯系统演示")
    print("=" * 60)
    
    # 创建通讯系统
    messenger = SecureMessenger()
    
    # 注册用户
    print("\n[1] 用户注册")
    alice = messenger.register_user("Alice")
    bob = messenger.register_user("Bob")
    
    # 密钥协商
    print("\n[2] 密钥协商")
    shared_key = messenger.compute_shared_key("Alice", "Bob")
    print(f"  共享密钥: {sm3_hash_hex(shared_key)[:32]}...")
    
    # 发送加密消息
    print("\n[3] 安全通信")
    message = "你好Bob！这是通过国密算法加密的安全消息。"
    msg1 = messenger.send_message("Alice", "Bob", message)
    
    # 接收并解密消息
    decrypted = messenger.receive_message(msg1)
    if decrypted:
        print(f"  解密结果: {decrypted}")
    
    # 消息哈希
    print("\n[4] 消息完整性")
    msg_hash = messenger.get_message_hash(msg1)
    print(f"  消息哈希: {msg_hash[:32]}...")
    
    # 用户认证
    print("\n[5] 用户认证")
    challenge = os.urandom(32)
    print(f"  挑战值: {challenge.hex()[:32]}...")
    
    response = messenger.authenticate_user("Alice", challenge)
    if response:
        valid = messenger.verify_authentication("Alice", challenge, response)
        print(f"  认证结果: {'成功' if valid else '失败'}")
    
    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)
