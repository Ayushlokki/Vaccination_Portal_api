import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1234@localhost/Vaccination_Portal"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
