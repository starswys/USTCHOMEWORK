"""
生成实验报告文档
"""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

doc = Document()

# 设置默认字体
style = doc.styles['Normal']
font = style.font
font.name = '宋体'
font.size = Pt(12)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

# ==================== 封面 ====================

# 标题
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.space_before = Pt(100)
run = title.add_run('作品设计报告')
run.font.size = Pt(26)
run.font.bold = True

# 副标题
subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
subtitle.space_before = Pt(20)
run = subtitle.add_run('基于国密算法的简易安全即时通讯系统')
run.font.size = Pt(18)

# 空行
doc.add_paragraph()
doc.add_paragraph()

# 基本信息表格
table = doc.add_table(rows=5, cols=2)
table.style = 'Table Grid'
table.alignment = WD_TABLE_ALIGNMENT.CENTER

info = [
    ('作品名称', '基于国密算法的简易安全即时通讯系统'),
    ('队伍名称', 'USTC安全通信'),
    ('队伍成员', '王延松'),
    ('指导教师', ''),
    ('完成日期', '2026年6月'),
]

for i, (key, value) in enumerate(info):
    table.rows[i].cells[0].text = key
    table.rows[i].cells[1].text = value
    # 设置第一列宽度
    table.rows[i].cells[0].width = Cm(3)

doc.add_page_break()

# ==================== 作品信息表 ====================

info_table = doc.add_table(rows=5, cols=1)
info_table.style = 'Table Grid'

info_data = [
    '作品信息',
    '作品名称：基于国密算法的简易安全即时通讯系统',
    '作品简介：本项目实现了一个基于中国国家密码管理局发布的国密算法（SM2/SM3/SM4）的简易安全即时通讯系统。系统支持基于SM2的ECDH密钥协商、消息的数字签名与验证、SM4-CBC模式的消息加密，以及基于SM3的HMAC完整性校验和挑战-响应身份认证。所有算法均为纯Python实现，不依赖第三方密码学库。',
    '关键词：国密算法、SM2、SM3、SM4、安全通信、数字签名、椭圆曲线密码学',
    '队伍成员：王延松（独立完成所有算法实现、协议设计、测试和文档编写）',
]

for i, text in enumerate(info_data):
    info_table.rows[i].cells[0].text = text

doc.add_page_break()

# ==================== 目录 ====================

doc.add_heading('目录', level=1)
toc_items = [
    '1. 作品功能简介说明',
    '2. 技术实现方案',
    '   2.1 实现原理',
    '   2.2 参考资料',
    '   2.3 开发环境',
    '   2.4 开发指南',
    '3. 系统设计与开发',
    '   3.1 需求分析',
    '   3.2 功能设计',
    '   3.3 功能测试',
    '   3.4 遇到的问题和解决',
    '4. 应用前景',
    '5. 总结',
    '附录：代码仓库链接',
]

for item in toc_items:
    p = doc.add_paragraph(item)
    p.paragraph_format.space_after = Pt(6)

doc.add_page_break()

# ==================== 1. 作品功能简介说明 ====================

doc.add_heading('1. 作品功能简介说明', level=1)

doc.add_paragraph(
    '本项目实现了一个基于中国国密算法的简易安全即时通讯系统，主要功能包括：'
)

features = [
    'SM3哈希算法：实现256位哈希值计算，支持消息完整性校验。',
    'SM4分组密码：实现128位分组加密，支持ECB和CBC两种工作模式，包含PKCS7填充。',
    'SM2椭圆曲线密码：实现密钥对生成、数字签名与验证、公钥加密与解密。',
    'ECDH密钥协商：基于SM2椭圆曲线实现安全的共享密钥交换。',
    '端到端加密通信：结合SM4和SM2实现消息的加密传输。',
    '消息完整性校验：使用SM3实现HMAC，确保消息未被篡改。',
    '挑战-响应认证：实现基于数字签名的用户身份认证。',
]

for feat in features:
    doc.add_paragraph(feat, style='List Bullet')

doc.add_paragraph(
    '\n系统架构清晰，代码结构模块化，每个算法独立实现并配有完整的单元测试。'
)

# ==================== 2. 技术实现方案 ====================

doc.add_heading('2. 技术实现方案', level=1)

doc.add_heading('2.1 实现原理', level=2)

doc.add_paragraph('本系统基于以下三种国密算法：')

doc.add_heading('SM3密码杂凑算法', level=3)
doc.add_paragraph(
    'SM3是中国国家密码管理局发布的密码杂凑算法标准，输出256位（32字节）哈希值。'
    '算法基于Merkle-Damgard结构，包含消息填充、消息扩展和压缩函数三个主要步骤。'
    '压缩函数使用64轮迭代，每轮包含FF/GG置换函数和P0/P1线性变换。'
)

doc.add_heading('SM4分组密码算法', level=3)
doc.add_paragraph(
    'SM4是中国发布的分组密码标准，分组长度和密钥长度均为128位，加密轮数为32轮。'
    '每轮包含S盒非线性替换、线性变换L和轮密钥异或。本项目实现了ECB和CBC两种工作模式，'
    '其中CBC模式使用随机IV增强安全性。'
)

doc.add_heading('SM2椭圆曲线密码算法', level=3)
doc.add_paragraph(
    'SM2是基于椭圆曲线密码学（ECC）的公钥密码算法，使用256位素数域椭圆曲线。'
    '本项目实现了SM2的核心功能：密钥生成（私钥随机生成，公钥=私钥×G点）、'
    '数字签名（基于Schnorr签名方案的变体）、公钥加密（使用KDF派生对称密钥）。'
)

doc.add_heading('2.2 参考资料', level=2)

refs = [
    '《SM2椭圆曲线公钥密码算法》（GB/T 32918-2016）',
    '《SM3密码杂凑算法》（GB/T 32905-2016）',
    '《SM4分组密码算法》（GB/T 32907-2016）',
    '中国国家密码管理局官方标准文档',
    '《密码学与网络安全》教材相关章节',
]

for ref in refs:
    doc.add_paragraph(ref, style='List Bullet')

doc.add_heading('2.3 开发环境', level=2)

env_table = doc.add_table(rows=4, cols=2)
env_table.style = 'Table Grid'

env_data = [
    ('项目', '说明'),
    ('操作系统', 'Windows 11'),
    ('编程语言', 'Python 3.14'),
    ('开发工具', 'VS Code'),
]

for i, (key, value) in enumerate(env_data):
    env_table.rows[i].cells[0].text = key
    env_table.rows[i].cells[1].text = value

doc.add_heading('2.4 开发指南', level=2)

doc.add_paragraph('项目运行方式：')
doc.add_paragraph('1. 运行演示程序：python src/main.py')
doc.add_paragraph('2. 运行单元测试：python -m unittest tests/test_all.py -v')

doc.add_paragraph('\n项目结构：')
structure = """
HOMEWORK/
├── README.md           # 项目说明文档
├── .gitignore          # Git忽略配置
├── src/
│   ├── sm3.py          # SM3哈希算法实现
│   ├── sm4.py          # SM4分组密码算法实现
│   ├── sm2.py          # SM2数字签名算法实现
│   ├── protocol.py     # 安全通信协议
│   └── main.py         # 主程序入口和演示
└── tests/
    └── test_all.py     # 单元测试（23个测试用例）
"""
doc.add_paragraph(structure)

# ==================== 3. 系统设计与开发 ====================

doc.add_heading('3. 系统设计与开发', level=1)

doc.add_heading('3.1 需求分析', level=2)

doc.add_paragraph('本项目需要实现以下功能需求：')

requirements = [
    '实现SM3哈希算法，能够计算任意长度消息的256位哈希值。',
    '实现SM4分组密码，支持ECB和CBC两种工作模式。',
    '实现SM2椭圆曲线密码，支持密钥生成、签名、验签、加密、解密。',
    '实现基于ECDH的密钥协商协议。',
    '实现端到端加密的安全通信协议。',
    '实现消息完整性校验（HMAC）。',
    '实现基于挑战-响应的用户身份认证。',
    '编写完整的单元测试，确保算法正确性。',
]

for req in requirements:
    doc.add_paragraph(req, style='List Number')

doc.add_heading('3.2 功能设计', level=2)

doc.add_heading('3.2.1 SM3哈希算法设计', level=3)
doc.add_paragraph(
    'SM3算法实现遵循国家标准，包含以下核心函数：\n'
    '- _rotl32：32位循环左移\n'
    '- _ff/_gg：FF/GG置换函数\n'
    '- _p0/_p1：P0/P1线性变换\n'
    '- _cf：压缩函数CF\n'
    '- sm3_hash：主哈希函数\n'
    '\n算法流程：消息填充 → 消息扩展 → 压缩运算 → 输出摘要'
)

doc.add_heading('3.2.2 SM4分组密码设计', level=3)
doc.add_paragraph(
    'SM4算法实现包含以下核心组件：\n'
    '- S盒（SBOX）：8位非线性替换表\n'
    '- 密钥扩展：将128位密钥扩展为32个轮密钥\n'
    '- 轮函数T：包含τ非线性变换和L线性变换\n'
    '- 工作模式：ECB（电子密码本）和CBC（密码块链接）\n'
    '- 填充方案：PKCS7标准填充'
)

doc.add_heading('3.2.3 SM2椭圆曲线密码设计', level=3)
doc.add_paragraph(
    'SM2算法基于256位素数域椭圆曲线，参数如下：\n'
    '- p：素数域模数\n'
    '- a, b：椭圆曲线方程系数\n'
    '- G：基点坐标\n'
    '- n：基点阶数\n'
    '\n核心运算：\n'
    '- 椭圆曲线点加法（ec_add）\n'
    '- 标量乘法（ec_mul）：双倍-加法算法\n'
    '- 模逆元计算：扩展欧几里得算法'
)

doc.add_heading('3.2.4 安全通信协议设计', level=3)
doc.add_paragraph(
    '安全通信协议流程：\n'
    '1. 密钥协商：Alice和Bob各自生成密钥对，交换公钥，计算共享密钥\n'
    '2. 消息加密：使用SM4-CBC加密消息，IV随机生成\n'
    '3. 完整性校验：计算HMAC = SM3(IV || Ciphertext || Key)\n'
    '4. 数字签名：对IV + Ciphertext + HMAC进行SM2签名\n'
    '5. 消息传输：发送IV + Ciphertext + Signature\n'
    '6. 接收验证：验证签名 → 解密消息 → 验证HMAC'
)

doc.add_heading('3.3 功能测试', level=2)

doc.add_paragraph('本项目编写了23个单元测试，覆盖所有核心功能：')

test_table = doc.add_table(rows=5, cols=3)
test_table.style = 'Table Grid'

test_data = [
    ('测试类别', '测试数量', '测试内容'),
    ('SM3测试', '5个', "空字符串、abc、哈希长度、雪崩效应、确定性"),
    ('SM4测试', '5个', '单块加解密、ECB模式、CBC模式、PKCS7填充'),
    ('SM2测试', '5个', '点加法、标量乘法、密钥生成、签名验证、篡改检测'),
    ('协议测试', '8个', '用户注册、密钥协商、消息加解密、签名验证、发送接收、认证、篡改检测'),
]

for i, row_data in enumerate(test_data):
    for j, cell_text in enumerate(row_data):
        test_table.rows[i].cells[j].text = cell_text

doc.add_paragraph('\n测试结果：所有23个测试用例均通过。')

doc.add_heading('3.4 遇到的问题和解决', level=2)

problems = [
    {
        'problem': 'SM3哈希值计算错误，测试向量不匹配',
        'solution': '检查并修正了消息扩展公式和压缩函数中的T值计算，确保与标准一致。'
    },
    {
        'problem': 'SM4 ECB加密结果与标准测试向量不一致',
        'solution': '修正了加密函数中的数组索引问题，确保32轮迭代的正确实现。'
    },
    {
        'problem': 'SM2签名验证失败',
        'solution': '修正了Z值计算函数，确保包含公钥信息，并在sign/verify函数中正确导入sm3_hash。'
    },
    {
        'problem': 'Windows终端中文输出乱码',
        'solution': '在main.py中添加UTF-8编码设置：sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=\'utf-8\')'
    },
    {
        'problem': 'Git推送时分支名称不匹配',
        'solution': '将本地master分支重命名为main，并解决合并冲突后推送。'
    },
]

for item in problems:
    doc.add_paragraph(f'问题：{item["problem"]}', style='List Bullet')
    doc.add_paragraph(f'解决：{item["solution"]}')
    doc.add_paragraph()

# ==================== 4. 应用前景 ====================

doc.add_heading('4. 应用前景', level=1)

doc.add_paragraph(
    '本项目实现的安全即时通讯系统具有以下应用前景：'
)

prospects = [
    '国密算法合规性：随着《密码法》的实施，国密算法在政府、金融、关键基础设施等领域的应用越来越广泛，本系统可作为国密算法应用的教学和演示工具。',
    '安全通信教学：代码结构清晰，适合作为密码学课程的实验项目，帮助学生理解对称加密、非对称加密、哈希函数、数字签名等概念。',
    '物联网安全：SM4算法的轻量级特性使其适合资源受限的物联网设备安全通信。',
    '区块链应用：SM2/SM3可应用于区块链中的数字签名和交易验证。',
    '即时通讯安全：端到端加密技术可应用于即时通讯应用，保护用户隐私。',
]

for prospect in prospects:
    doc.add_paragraph(prospect, style='List Number')

# ==================== 5. 总结 ====================

doc.add_heading('5. 总结', level=1)

doc.add_paragraph(
    '本项目成功实现了基于国密算法（SM2/SM3/SM4）的简易安全即时通讯系统。'
    '通过纯Python实现，不依赖第三方密码学库，深入理解了国密算法的原理和实现细节。'
)

doc.add_paragraph(
    '项目完成了以下工作：'
)

summary = [
    '完整实现了SM3哈希算法，通过标准测试向量验证。',
    '完整实现了SM4分组密码算法，支持ECB和CBC两种模式。',
    '完整实现了SM2椭圆曲线密码算法，支持签名、验签、加密、解密。',
    '设计并实现了基于ECDH的密钥协商协议。',
    '设计并实现了端到端加密的安全通信协议。',
    '编写了23个单元测试，确保代码质量。',
    '代码已上传至GitHub仓库，便于分享和协作。',
]

for item in summary:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph(
    '\n通过本项目，加深了对密码学原理的理解，提升了安全系统设计和实现能力。'
    '未来可进一步优化算法性能，添加更多安全特性（如前向保密、密钥轮换等）。'
)

# ==================== 附录 ====================

doc.add_page_break()
doc.add_heading('附录：代码仓库链接', level=1)

doc.add_paragraph('GitHub仓库地址：https://github.com/starswys/USTCHOMEWORK')

doc.add_paragraph('\n仓库结构：')
doc.add_paragraph('├── README.md           # 项目说明文档')
doc.add_paragraph('├── .gitignore          # Git忽略配置')
doc.add_paragraph('├── src/')
doc.add_paragraph('│   ├── sm3.py          # SM3哈希算法实现')
doc.add_paragraph('│   ├── sm4.py          # SM4分组密码算法实现')
doc.add_paragraph('│   ├── sm2.py          # SM2数字签名算法实现')
doc.add_paragraph('│   ├── protocol.py     # 安全通信协议')
doc.add_paragraph('│   └── main.py         # 主程序入口和演示')
doc.add_paragraph('└── tests/')
doc.add_paragraph('    └── test_all.py     # 单元测试')

doc.add_paragraph('\n作者：starswys (王延松)')
doc.add_paragraph('联系邮箱：wangyansong@mail.ustc.edu.cn')

# 保存文档
output_path = r'C:\Users\20659\Desktop\HOMEWORK\docs\作品设计报告.docx'
doc.save(output_path)
print(f'报告已保存到: {output_path}')
