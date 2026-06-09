"""
SM3哈希算法实现（修正版）
中国国家密码管理局发布的密码杂凑算法标准
输出256位（32字节）哈希值
"""

# 初始值IV
IV = [
    0x7380166F, 0x4914B2B9, 0x172442D7, 0xDA8A0600,
    0xA96F30BC, 0x163138AA, 0xE38DEE4D, 0xB0FB0E4E
]

# 常量T
T_JO = 0x79CC4519  # 0 <= j <= 15
T_JN = 0x7A879D8A  # 16 <= j <= 63


def _rotl32(x, n):
    """32位循环左移"""
    n = n % 32
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def _ff(x, y, z, j):
    """FF置换函数"""
    if 0 <= j <= 15:
        return x ^ y ^ z
    else:
        return (x & y) | (x & z) | (y & z)


def _gg(x, y, z, j):
    """GG置换函数"""
    if 0 <= j <= 15:
        return x ^ y ^ z
    else:
        return (x & y) | (~x & z) & 0xFFFFFFFF


def _p0(x):
    """P0置换函数"""
    return x ^ _rotl32(x, 9) ^ _rotl32(x, 17)


def _p1(x):
    """P1置换函数"""
    return x ^ _rotl32(x, 15) ^ _rotl32(x, 23)


def _cf(v, b):
    """压缩函数CF"""
    # 消息扩展
    w = [0] * 68
    w1 = [0] * 64

    # 将消息分组转换为16个32位字
    for i in range(16):
        w[i] = int.from_bytes(b[i*4:(i+1)*4], 'big')

    # 扩展生成w[16]到w[67]
    for j in range(16, 68):
        w[j] = (_p1(w[j-16] ^ w[j-9] ^ _rotl32(w[j-3], 15)) ^ 
                _rotl32(w[j-13], 7) ^ w[j-6]) & 0xFFFFFFFF

    # 生成w'[0]到w'[63]
    for j in range(64):
        w1[j] = (w[j] ^ w[j+4]) & 0xFFFFFFFF

    # 压缩
    a, b_, c, d, e, f, g, h = v

    for j in range(64):
        # 计算T值
        t = T_JO if j < 16 else T_JN
        
        ss1 = _rotl32((_rotl32(a, 12) + e + _rotl32(t, j)) & 0xFFFFFFFF, 7)
        ss2 = (ss1 ^ _rotl32(a, 12)) & 0xFFFFFFFF
        tt1 = (_ff(a, b_, c, j) + d + ss2 + w1[j]) & 0xFFFFFFFF
        tt2 = (_gg(e, f, g, j) + h + ss1 + w[j]) & 0xFFFFFFFF
        d = c
        c = _rotl32(b_, 9)
        b_ = a
        a = tt1
        h = g
        g = _rotl32(f, 19)
        f = e
        e = _p0(tt2)

    # 计算中间哈希值
    return [(a ^ v[0]) & 0xFFFFFFFF, (b_ ^ v[1]) & 0xFFFFFFFF, 
            (c ^ v[2]) & 0xFFFFFFFF, (d ^ v[3]) & 0xFFFFFFFF,
            (e ^ v[4]) & 0xFFFFFFFF, (f ^ v[5]) & 0xFFFFFFFF, 
            (g ^ v[6]) & 0xFFFFFFFF, (h ^ v[7]) & 0xFFFFFFFF]


def sm3_hash(message):
    """
    计算消息的SM3哈希值
    
    Args:
        message: bytes类型的消息
    
    Returns:
        32字节的哈希值
    """
    if not isinstance(message, bytes):
        raise TypeError("消息必须是bytes类型")
    
    msg = bytearray(message)
    msg_len = len(msg)
    
    # 消息填充
    # 先添加0x80
    msg.append(0x80)
    
    # 填充0直到长度模512等于448（56字节）
    while (len(msg) % 64) != 56:
        msg.append(0x00)
    
    # 添加64位消息长度（单位：位）
    msg_len_bits = msg_len * 8
    msg.extend(msg_len_bits.to_bytes(8, 'big'))
    
    # 初始化
    v = IV.copy()
    
    # 处理每个512位（64字节）分组
    for i in range(0, len(msg), 64):
        block = bytes(msg[i:i+64])
        v = _cf(v, block)
    
    # 输出结果：连接所有32位字
    result = bytearray()
    for x in v:
        result.extend(x.to_bytes(4, 'big'))
    
    return bytes(result)


def sm3_hash_hex(message):
    """返回十六进制字符串格式的哈希值"""
    return sm3_hash(message).hex()


# 测试
if __name__ == "__main__":
    # 标准测试向量1：空字符串
    test_msg = b""
    expected1 = "1ab21d8355cfa17f8e61194831e81a8f22bec8c728fefb747ed035eb5082aa2b"
    result1 = sm3_hash_hex(test_msg)
    print(f"测试1 - 空字符串:")
    print(f"  期望: {expected1}")
    print(f"  结果: {result1}")
    print(f"  通过: {result1 == expected1}")
    
    # 标准测试向量2："abc"
    test_msg = b"abc"
    expected2 = "66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7a2297da02b8f4ba8e0"
    result2 = sm3_hash_hex(test_msg)
    print(f"\n测试2 - 'abc':")
    print(f"  期望: {expected2}")
    print(f"  结果: {result2}")
    print(f"  通过: {result2 == expected2}")
