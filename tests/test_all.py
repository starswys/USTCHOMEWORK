"""
国密算法单元测试
"""

import os
import sys
import io
import unittest

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sm3 import sm3_hash, sm3_hash_hex
from sm4 import (
    sm4_ecb_encrypt, sm4_ecb_decrypt,
    sm4_cbc_encrypt, sm4_cbc_decrypt,
    _encrypt_block, _decrypt_block, _key_expand
)
from sm2 import (
    generate_keypair, ec_mul, ec_add, sign, verify,
    encrypt as sm2_encrypt, decrypt as sm2_decrypt,
    Gx, Gy, N, P, INFINITY
)
from protocol import SecureMessenger


class TestSM3(unittest.TestCase):
    """SM3哈希算法测试"""
    
    def test_empty_string(self):
        """测试空字符串哈希"""
        result = sm3_hash_hex(b"")
        expected = "1ab21d8355cfa17f8e61194831e81a8f22bec8c728fefb747ed035eb5082aa2b"
        self.assertEqual(result, expected)
    
    def test_abc(self):
        """测试字符串'abc'哈希"""
        result = sm3_hash_hex(b"abc")
        expected = "66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7a2297da02b8f4ba8e0"
        self.assertEqual(result, expected)
    
    def test_hash_length(self):
        """测试哈希值长度"""
        result = sm3_hash(b"test")
        self.assertEqual(len(result), 32)  # 256位 = 32字节
    
    def test_avalanche_effect(self):
        """测试雪崩效应"""
        hash1 = sm3_hash(b"Hello, World!")
        hash2 = sm3_hash(b"Hello, World?")
        self.assertNotEqual(hash1, hash2)
    
    def test_deterministic(self):
        """测试确定性"""
        msg = b"test message"
        hash1 = sm3_hash(msg)
        hash2 = sm3_hash(msg)
        self.assertEqual(hash1, hash2)


class TestSM4(unittest.TestCase):
    """SM4分组密码算法测试"""
    
    def setUp(self):
        """测试初始化"""
        self.key = bytes([0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF,
                         0xFE, 0xDC, 0xBA, 0x98, 0x76, 0x54, 0x32, 0x10])
        self.plaintext = bytes([0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF,
                               0xFE, 0xDC, 0xBA, 0x98, 0x76, 0x54, 0x32, 0x10])
        self.expected = bytes([0x68, 0x1E, 0xDF, 0x34, 0xD2, 0x06, 0x96, 0x5E,
                              0x86, 0xB3, 0xE9, 0x4F, 0x53, 0x6E, 0x42, 0x46])
    
    def test_single_block_encrypt(self):
        """测试单块加密"""
        rk = _key_expand(self.key)
        result = _encrypt_block(self.plaintext, rk)
        self.assertEqual(result, self.expected)
    
    def test_single_block_decrypt(self):
        """测试单块解密"""
        rk = _key_expand(self.key)
        result = _decrypt_block(self.expected, rk)
        self.assertEqual(result, self.plaintext)
    
    def test_ecb_encrypt_decrypt(self):
        """测试ECB模式加解密"""
        plaintext = b"SM4 ECB Test!"
        ciphertext = sm4_ecb_encrypt(plaintext, self.key)
        decrypted = sm4_ecb_decrypt(ciphertext, self.key)
        self.assertEqual(decrypted, plaintext)
    
    def test_cbc_encrypt_decrypt(self):
        """测试CBC模式加解密"""
        iv = os.urandom(16)
        plaintext = b"SM4 CBC Test!"
        ciphertext = sm4_cbc_encrypt(plaintext, self.key, iv)
        decrypted = sm4_cbc_decrypt(ciphertext, self.key, iv)
        self.assertEqual(decrypted, plaintext)
    
    def test_pkcs7_padding(self):
        """测试PKCS7填充"""
        from sm4 import _pkcs7_pad, _pkcs7_unpad
        
        # 测试不同长度
        for length in [1, 15, 16, 17, 31, 32]:
            data = os.urandom(length)
            padded = _pkcs7_pad(data)
            self.assertEqual(len(padded) % 16, 0)
            unpadded = _pkcs7_unpad(padded)
            self.assertEqual(unpadded, data)


class TestSM2(unittest.TestCase):
    """SM2椭圆曲线密码算法测试"""
    
    def test_point_addition(self):
        """测试椭圆曲线点加法"""
        # 测试 P + O = P
        P_point = (Gx, Gy)
        result = ec_add(P_point, INFINITY)
        self.assertEqual(result, P_point)
        
        # 测试 O + P = P
        result = ec_add(INFINITY, P_point)
        self.assertEqual(result, P_point)
    
    def test_scalar_multiplication(self):
        """测试标量乘法"""
        # 测试 1*G = G
        result = ec_mul(1, (Gx, Gy))
        self.assertEqual(result, (Gx, Gy))
        
        # 测试 0*G = O
        result = ec_mul(0, (Gx, Gy))
        self.assertEqual(result, INFINITY)
    
    def test_key_generation(self):
        """测试密钥生成"""
        private_key, public_key = generate_keypair()
        self.assertGreater(private_key, 0)
        self.assertLess(private_key, N)
        self.assertIsNotNone(public_key)
        self.assertEqual(len(public_key), 2)
    
    def test_signature_verify(self):
        """测试签名验证"""
        private_key, public_key = generate_keypair()
        message = b"Test message"
        
        sig = sign(message, private_key)
        valid = verify(message, sig, public_key)
        self.assertTrue(valid)
    
    def test_signature_tamper_detection(self):
        """测试篡改检测"""
        private_key, public_key = generate_keypair()
        message = b"Test message"
        
        sig = sign(message, private_key)
        
        # 篡改消息
        tampered = b"Tampered message"
        valid = verify(tampered, sig, public_key)
        self.assertFalse(valid)
    
    def test_encrypt_decrypt(self):
        """测试加解密"""
        private_key, public_key = generate_keypair()
        plaintext = b"Hello, SM2!"
        
        ciphertext = sm2_encrypt(plaintext, public_key)
        decrypted = sm2_decrypt(ciphertext, private_key)
        self.assertEqual(decrypted, plaintext)


class TestProtocol(unittest.TestCase):
    """安全通信协议测试"""
    
    def setUp(self):
        """测试初始化"""
        self.messenger = SecureMessenger()
        self.alice = self.messenger.register_user("Alice")
        self.bob = self.messenger.register_user("Bob")
    
    def test_user_registration(self):
        """测试用户注册"""
        self.assertIsNotNone(self.alice)
        self.assertIsNotNone(self.bob)
        self.assertEqual(self.alice.user_id, "Alice")
        self.assertEqual(self.bob.user_id, "Bob")
    
    def test_key_exchange(self):
        """测试密钥协商"""
        key_ab = self.messenger.compute_shared_key("Alice", "Bob")
        key_ba = self.messenger.compute_shared_key("Bob", "Alice")
        
        # 共享密钥应该相同
        self.assertEqual(key_ab, key_ba)
    
    def test_message_encryption_decryption(self):
        """测试消息加解密"""
        message = b"Secret message"
        
        ciphertext, iv, signature = self.messenger.encrypt_message(
            "Alice", "Bob", message
        )
        
        decrypted = self.messenger.decrypt_message(
            "Alice", "Bob", ciphertext, iv, signature
        )
        
        self.assertEqual(decrypted, message)
    
    def test_signature_verification(self):
        """测试签名验证"""
        message = b"Test message"
        
        signature = self.messenger.sign_message("Alice", message)
        valid = self.messenger.verify_signature("Alice", message, signature)
        self.assertTrue(valid)
    
    def test_send_receive(self):
        """测试发送接收"""
        msg = self.messenger.send_message("Alice", "Bob", "Hello!")
        result = self.messenger.receive_message(msg)
        self.assertEqual(result, "Hello!")
    
    def test_authentication(self):
        """测试用户认证"""
        challenge = os.urandom(32)
        response = self.messenger.authenticate_user("Alice", challenge)
        
        valid = self.messenger.verify_authentication("Alice", challenge, response)
        self.assertTrue(valid)
    
    def test_tamper_detection(self):
        """测试篡改检测"""
        msg = self.messenger.send_message("Alice", "Bob", "Secret")
        
        # 篡改密文
        msg.ciphertext = os.urandom(len(msg.ciphertext))
        
        result = self.messenger.receive_message(msg)
        self.assertIsNone(result)  # 应该失败


if __name__ == "__main__":
    unittest.main(verbosity=2)
