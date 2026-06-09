"""
SM2椭圆曲线公钥密码算法实现
中国国家密码管理局发布的基于椭圆曲线密码学的公钥密码算法
支持数字签名、加密和密钥交换
"""

import random
import hashlib
from typing import Tuple, Optional

# SM2椭圆曲线参数（256位素数域）
P = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF
A = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC
B = 0x28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93
N = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123
Gx = 0x32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7
Gy = 0xBC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0

# 椭圆曲线上的无穷远点
INFINITY = (None, None)


def _modinv(a: int, m: int) -> int:
    """计算模逆元（扩展欧几里得算法）"""
    if a < 0:
        a = a % m
    g, x, _ = _extended_gcd(a, m)
    if g != 1:
        raise ValueError("模逆不存在")
    return x % m


def _extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    """扩展欧几里得算法"""
    if a == 0:
        return b, 0, 1
    g, x, y = _extended_gcd(b % a, a)
    return g, y - (b // a) * x, x


def ec_add(p1: Tuple, p2: Tuple) -> Tuple:
    """
    椭圆曲线点加法
    P + Q = R
    """
    if p1 == INFINITY:
        return p2
    if p2 == INFINITY:
        return p1
    
    x1, y1 = p1
    x2, y2 = p2
    
    if x1 == x2:
        if y1 != y2 or y1 == 0:
            return INFINITY
        # 点倍运算
        lam = (3 * x1 * x1 + A) * _modinv(2 * y1, P) % P
    else:
        lam = (y2 - y1) * _modinv(x2 - x1, P) % P
    
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    
    return (x3, y3)


def ec_mul(k: int, point: Tuple) -> Tuple:
    """
    椭圆曲线标量乘法
    k * P
    使用双倍-加法算法
    """
    if k == 0:
        return INFINITY
    if k < 0:
        k = -k
        point = (point[0], (-point[1]) % P)
    
    result = INFINITY
    addend = point
    
    while k:
        if k & 1:
            result = ec_add(result, addend)
        addend = ec_add(addend, addend)
        k >>= 1
    
    return result


def generate_keypair() -> Tuple[int, Tuple]:
    """
    生成SM2密钥对
    
    Returns:
        (private_key, public_key)
    """
    private_key = random.randint(1, N - 1)
    public_key = ec_mul(private_key, (Gx, Gy))
    return private_key, public_key


def _sm3_hash(message: bytes) -> int:
    """使用SM3计算哈希值，返回整数"""
    from sm3 import sm3_hash
    return int.from_bytes(sm3_hash(message), 'big')


def _kdf(z: bytes, klen: int) -> bytes:
    """
    密钥派生函数KDF（基于SM3）
    用于SM2加密
    """
    from sm3 import sm3_hash
    ct = 1
    result = b''
    for i in range((klen + 31) // 32):
        result += sm3_hash(z + ct.to_bytes(4, 'big'))
        ct += 1
    return result[:klen]


def sign(message: bytes, private_key: int, id_a: bytes = b'1234567812345678') -> Tuple[int, int]:
    """
    SM2数字签名
    
    Args:
        message: 待签名消息
        private_key: 私钥
        id_a: 签名者ID（默认128位全1）
    
    Returns:
        (r, s) 签名值
    """
    from sm3 import sm3_hash
    
    # 计算公钥
    public_key = ec_mul(private_key, (Gx, Gy))
    
    # 计算Z值（包含公钥）
    z_data = compute_z_with_key(id_a, public_key)
    z = sm3_hash(z_data)
    
    # 计算M = Z || M
    m = z + message
    
    # 计算哈希值e
    e = _sm3_hash(m)
    
    while True:
        # 生成随机数k
        k = random.randint(1, N - 1)
        
        # 计算椭圆曲线点(x1, y1) = k*G
        x1, y1 = ec_mul(k, (Gx, Gy))
        
        # 计算r = (e + x1) mod n
        r = (e + x1) % N
        if r == 0 or r + k == N:
            continue
        
        # 计算s = (1 + dA)^(-1) * (k - r*dA) mod n
        s = (_modinv(1 + private_key, N) * (k - r * private_key)) % N
        if s == 0:
            continue
        
        return (r, s)


def verify(message: bytes, signature: Tuple[int, int], public_key: Tuple, 
           id_a: bytes = b'1234567812345678') -> bool:
    """
    SM2签名验证
    
    Args:
        message: 原消息
        signature: (r, s) 签名值
        public_key: 公钥
        id_a: 签名者ID
    
    Returns:
        验证结果
    """
    from sm3 import sm3_hash
    
    r, s = signature
    
    # 检查范围
    if not (1 <= r <= N - 1 and 1 <= s <= N - 1):
        return False
    
    # 计算Z值（包含公钥）
    z_data = compute_z_with_key(id_a, public_key)
    z = sm3_hash(z_data)
    
    # 计算M = Z || M
    m = z + message
    
    # 计算哈希值e
    e = _sm3_hash(m)
    
    # 计算t = (r + s) mod n
    t = (r + s) % N
    if t == 0:
        return False
    
    # 计算椭圆曲线点(x1, y1) = s*G + t*PA
    point = ec_add(ec_mul(s, (Gx, Gy)), ec_mul(t, public_key))
    
    if point == INFINITY:
        return False
    
    x1, _ = point
    
    # 验证R = (e + x1) mod n == r
    R = (e + x1) % N
    return R == r


def _compute_z(id_a: bytes) -> bytes:
    """
    计算Z值
    Z = SM3(ENTL || ID || a || b || xG || yG || xA || yA)
    """
    from sm3 import sm3_hash
    
    # ENTLA（ID比特长度，2字节）
    entla = len(id_a) * 8
    
    # 椭圆曲线参数
    a_bytes = A.to_bytes(32, 'big')
    b_bytes = B.to_bytes(32, 'big')
    xg_bytes = Gx.to_bytes(32, 'big')
    yg_bytes = Gy.to_bytes(32, 'big')
    
    # 计算Z值（公钥作为参数时需要传入）
    z_data = entla.to_bytes(2, 'big') + id_a + a_bytes + b_bytes + xg_bytes + yg_bytes
    
    return z_data


def compute_z_with_key(id_a: bytes, public_key: Tuple) -> bytes:
    """计算包含公钥的Z值"""
    from sm3 import sm3_hash
    
    entla = len(id_a) * 8
    
    a_bytes = A.to_bytes(32, 'big')
    b_bytes = B.to_bytes(32, 'big')
    xg_bytes = Gx.to_bytes(32, 'big')
    yg_bytes = Gy.to_bytes(32, 'big')
    
    xa, ya = public_key
    xa_bytes = xa.to_bytes(32, 'big')
    ya_bytes = ya.to_bytes(32, 'big')
    
    z_data = (entla.to_bytes(2, 'big') + id_a + a_bytes + b_bytes + 
              xg_bytes + yg_bytes + xa_bytes + ya_bytes)
    
    return sm3_hash(z_data)


def encrypt(message: bytes, public_key: Tuple) -> bytes:
    """
    SM2加密
    
    Args:
        message: 待加密消息
        public_key: 公钥
    
    Returns:
        密文（C1 || C2 || C3格式）
    """
    from sm3 import sm3_hash
    
    klen = len(message)
    
    while True:
        # 生成随机数k
        k = random.randint(1, N - 1)
        
        # 计算C1 = k * G = (x1, y1)
        x1, y1 = ec_mul(k, (Gx, Gy))
        
        # 计算椭圆曲线点S = k * PB
        sx, sy = ec_mul(k, public_key)
        
        # 计算t = KDF(x2 || y2, klen)
        t = _kdf(sx.to_bytes(32, 'big') + sy.to_bytes(32, 'big'), klen)
        
        # 检查t是否全0
        if all(b == 0 for b in t):
            continue
        
        # 计算C2 = M ⊕ t
        c2 = bytes(m ^ t[i] for i, m in enumerate(message))
        
        # 计算C3 = SM3(x2 || M || y2)
        c3 = sm3_hash(sx.to_bytes(32, 'big') + message + sy.to_bytes(32, 'big'))
        
        # 输出密文 C1 || C2 || C3
        c1 = b'\x04' + x1.to_bytes(32, 'big') + y1.to_bytes(32, 'big')
        return c1 + c2 + c3


def decrypt(ciphertext: bytes, private_key: int) -> bytes:
    """
    SM2解密
    
    Args:
        ciphertext: 密文（C1 || C2 || C3格式）
        private_key: 私钥
    
    Returns:
        明文
    """
    from sm3 import sm3_hash
    
    # 解析密文
    if ciphertext[0] != 0x04:
        raise ValueError("无效的密文格式")
    
    x1 = int.from_bytes(ciphertext[1:33], 'big')
    y1 = int.from_bytes(ciphertext[33:65], 'big')
    
    # C3是最后32字节
    c3 = ciphertext[-32:]
    c2 = ciphertext[65:-32]
    klen = len(c2)
    
    # 计算椭圆曲线点(x2, y2) = dB * C1
    sx, sy = ec_mul(private_key, (x1, y1))
    
    # 计算t = KDF(x2 || y2, klen)
    t = _kdf(sx.to_bytes(32, 'big') + sy.to_bytes(32, 'big'), klen)
    
    # 计算M = C2 ⊕ t
    message = bytes(c ^ t[i] for i, c in enumerate(c2))
    
    # 验证C3
    c3_check = sm3_hash(sx.to_bytes(32, 'big') + message + sy.to_bytes(32, 'big'))
    if c3 != c3_check:
        raise ValueError("解密失败：完整性校验错误")
    
    return message


# 测试
if __name__ == "__main__":
    print("SM2算法测试\n")
    
    # 生成密钥对
    print("1. 生成密钥对...")
    private_key, public_key = generate_keypair()
    print(f"   私钥: {hex(private_key)}")
    print(f"   公钥: ({hex(public_key[0])[:20]}..., {hex(public_key[1])[:20]}...)")
    
    # 签名测试
    print("\n2. 数字签名测试...")
    message = b"Hello, SM2 Signature!"
    sig = sign(message, private_key)
    print(f"   消息: {message.decode()}")
    print(f"   签名: (r={hex(sig[0])[:20]}..., s={hex(sig[1])[:20]}...)")
    
    # 验证测试
    print("\n3. 签名验证测试...")
    valid = verify(message, sig, public_key)
    print(f"   验证结果: {'成功' if valid else '失败'}")
    
    # 篡改测试
    tampered = b"Hello, SM2 Signature? (tampered)"
    valid_tampered = verify(tampered, sig, public_key)
    print(f"   篡改验证: {'成功' if valid_tampered else '失败（预期）'}")
    
    # 加密测试
    print("\n4. 加密解密测试...")
    enc_message = b"Hello, SM2 Encryption!"
    ciphertext = encrypt(enc_message, public_key)
    print(f"   明文: {enc_message.decode()}")
    print(f"   密文长度: {len(ciphertext)} 字节")
    
    decrypted = decrypt(ciphertext, private_key)
    print(f"   解密: {decrypted.decode()}")
    print(f"   正确: {decrypted == enc_message}")
