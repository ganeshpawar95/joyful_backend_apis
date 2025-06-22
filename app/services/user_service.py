from sqlalchemy.orm import Session
from app.db.models.user import User
from app.schemas.request import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email_phone(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password=hashed_password,
        status=1,
        phone="",
    )
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
        db_user.phone = user.phone

    if user.grade:
        db_user.grade = user.grade

    if user.student_board:
        db_user.student_board = user.student_board

    if user.country:
        db_user.country = user.country
    db.commit()
    db.refresh(db_user)
    return db_user


# login


def admin_user_login(*, session: Session, email: str, password: str) -> User:
    db_user = get_user_by_email_phone(db=session, email=email)
    if not db_user:
        return None
    if not db_user or not verify_password(password, db_user.password):
        raise ValueError("Invalid credentials")
    return db_user
