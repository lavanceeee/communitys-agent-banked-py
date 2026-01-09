"""
JWT Token 解析工具
"""

import jwt
from typing import Optional, Dict
from fastapi import HTTPException, status


class JWTHelper:
    """JWT Token 处理工具类"""

    def __init__(self, secret_key: str = None, algorithm: str = "HS256"):
        """
        初始化 JWT Helper

        Args:
            secret_key: JWT 密钥（如果验证签名需要）
            algorithm: 加密算法
        """
        self.secret_key = secret_key
        self.algorithm = algorithm

    def decode_token(self, token: str, verify: bool = False) -> Dict:
        """
        解码 JWT Token

        Args:
            token: JWT token 字符串
            verify: 是否验证签名（需要 secret_key）

        Returns:
            解码后的 payload 字典

        Raises:
            HTTPException: Token 无效或过期
        """
        try:
            if verify and not self.secret_key:
                raise ValueError("验证签名需要提供 secret_key")

            # 解码 token
            options = {"verify_signature": verify}
            payload = jwt.decode(
                token,
                self.secret_key if verify else None,
                algorithms=[self.algorithm],
                options=options,
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 已过期"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"无效的 Token: {str(e)}",
            )

    def get_user_id(self, token: str, user_id_field: str = "sub") -> str:
        """
        从 Token 中提取用户 ID

        Args:
            token: JWT token 字符串
            user_id_field: 用户 ID 在 payload 中的字段名
                          常见值: "sub", "user_id", "id", "userId"

        Returns:
            用户 ID
        """
        payload = self.decode_token(token, verify=False)

        # 尝试多个可能的字段名
        possible_fields = [user_id_field, "sub", "user_id", "id", "userId"]

        for field in possible_fields:
            if field in payload:
                return str(payload[field])

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token 中未找到用户 ID（尝试的字段: {possible_fields}）",
        )

    def get_payload_field(self, token: str, field: str, default=None):
        """
        从 Token 中获取指定字段

        Args:
            token: JWT token 字符串
            field: 字段名
            default: 默认值

        Returns:
            字段值或默认值
        """
        payload = self.decode_token(token, verify=False)
        return payload.get(field, default)


# 创建全局实例（不验证签名）
jwt_helper = JWTHelper()
