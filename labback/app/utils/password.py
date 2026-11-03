import bcrypt

def hash_password(password: str) -> str:
    """哈希密码"""
    # 生成随机盐值
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    """解密密码"""
    # 将密码转换为字节
    password_bytes = password.encode("utf-8")
    # 将哈希密码转换为字节
    hashed_password_bytes = hashed_password.encode("utf-8")
    # 验证密码
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)
