import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 注意：bcrypt 要求传入 bytes 类型，所以需要 encode
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )
#加码密码
def get_password_hash(password: str) -> str:
    # 生成盐并哈希
    salt = bcrypt.gensalt()
    # hashpw 返回的是 bytes，需要 decode 成字符串再存入数据库
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')