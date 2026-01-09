"""
测试 JWT 解析功能

运行方式：
python examples/jwt_example.py
"""

from app.utils.jwt_helper import jwt_helper

# 示例 token（这是一个未加密的示例 token，仅用于测试）
# Payload: {"sub": "user_123456", "email": "user@example.com", "name": "张三"}
sample_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMzQ1NiIsImVtYWlsIjoidXNlckBleGFtcGxlLmNvbSIsIm5hbWUiOiLlvKDkuIkifQ.xyz"

print("=" * 50)
print("JWT Token 解析测试")
print("=" * 50)

try:
    # 1. 解码 token
    print("\n1. 解码 Token...")
    print(f"Token: {sample_token[:50]}...")

    payload = jwt_helper.decode_token(sample_token)
    print(f"✅ Payload: {payload}")

    # 2. 提取用户 ID
    print("\n2. 提取用户 ID...")
    user_id = jwt_helper.get_user_id(sample_token)
    print(f"✅ 用户 ID: {user_id}")

    # 3. 获取其他字段
    print("\n3. 获取其他字段...")
    email = jwt_helper.get_payload_field(sample_token, "email", "未找到")
    name = jwt_helper.get_payload_field(sample_token, "name", "未找到")
    print(f"✅ 邮箱: {email}")
    print(f"✅ 姓名: {name}")

    print("\n" + "=" * 50)
    print("🎉 所有测试通过！")
    print("=" * 50)

    print("\n💡 提示：")
    print("1. 将你的真实 JWT token 替换 sample_token 变量")
    print("2. 运行: python examples/jwt_example.py")
    print("3. 查看 token 中包含的所有字段")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    print("\n💡 如果出错，请检查：")
    print("1. Token 格式是否正确")
    print("2. 是否安装了 pyjwt: pip install pyjwt")
