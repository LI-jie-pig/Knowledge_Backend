from passlib.context import CryptContext
#创建密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
#加密密码上下文
def get_password_hash(password: str):
    return pwd_context.hash(password)
