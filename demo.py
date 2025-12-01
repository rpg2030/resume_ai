from database import SessionLocal
from models import User
from werkzeug.security import generate_password_hash

db = SessionLocal()
u = User(username="hr1", email="hr1@example.com", password_hash=generate_password_hash("hrpassword"), role="HR")
db.add(u)
db.commit()
print("created hr1")