from sqlalchemy.orm import Session
from app.db.models.user import User
from app.schemas.request import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email_phone(db: Session, email: str,phone:str):
    return db.query(User).filter((User.email == email)| (User.phone==phone)).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username,phone=user.phone, email=user.email, grade=user.grade,status=1,student_board=user.student_board,  password=hashed_password,country=user.country)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user: UserUpdate):
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    if user.username:
        db_user.username = user.username
    if user.email:
        db_user.email = user.email
    # if user.password:
    #     db_user.password = get_password_hash(user.password)
    if user.phone:
        db_user.phone =user.phone
        
    if user.grade:
        db_user.grade = user.grade
        
    if user.student_board:
        db_user.student_board =user.student_board
    
    if user.country:
        db_user.country =user.country
    db.commit()
    db.refresh(db_user)
    return db_user


# login

def b2b_user_login(*, session: Session, email: str, phone: str) -> User:
    db_user = get_user_by_email_phone(db=session, email=email,phone=phone)
    if not db_user:
        return None
    return db_user
