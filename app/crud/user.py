from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



def get_password_hash(password: str):
    # Hash the password using bcrypt
    return pwd_context.hash(password)


def get_user(db: Session, user_id: int):
    # get user by id
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username:str):
    # get user by username
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email:str):
    # get user by email
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    # get all users with pagination
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate):
    # create a new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        role=user.role, 
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user: UserUpdate):
    # update existing user
    db_user = get_user(db, user_id)
    if db_user:
        update_data = user.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if key == "password":
                setattr(db_user, "password_hash", get_password_hash(value))
            else:
                setattr(db_user, key, value)

        db.commit()
        db.refresh(db_user)

    return db_user


def delete_user(db: Session, user_id: int):
    # delete a user
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()

    return db_user