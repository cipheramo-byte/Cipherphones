import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cipher_secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET")
    PAYSTACK_PUBLIC = os.environ.get("PAYSTACK_PUBLIC")