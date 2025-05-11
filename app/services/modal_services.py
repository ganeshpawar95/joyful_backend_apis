
from typing import Type, TypeVar, List, Optional, Dict, Any
from app.schemas.response import  MessageResponse
from sqlalchemy.orm import Session
from app.db.models.user import *
from fastapi import BackgroundTasks
from sqlalchemy import and_


#----------------------------------------dynamic function---------------------------------

# Define a generic type for models
T = TypeVar("T")

# Generic function to get records by user ID
def get_records_by_user_id(
    db: Session, model: Type[T], user_id: int
) -> list[T]:
    return db.query(model).filter(model.user_id == user_id).all()

# Generic function to create a record
def create_record(
    db: Session, model: Type[T],background_tasks: Optional[BackgroundTasks] = None, **kwargs
) -> MessageResponse:
    try:
        record = model(**kwargs)
        db.add(record)
        db.commit()
        db.refresh(record)
        # Schedule related tasks in the background
        return record
    except Exception as error:
        db.rollback()
        raise ValueError(f"Something went wrong. Please contact support: {str(error)}")


# Generic function to get a record by filters
def get_record_by_filters(
    db: Session, model: Type[T], **filters
) -> Optional[T]:
    return db.query(model).filter_by(**filters).first()


def get_record_by_filters_all(db: Session, model: Type[T], **filters) -> Optional[T]:
    return db.query(model).filter(and_(*(getattr(model, key) == value for key, value in filters.items()))).all()



def get_record_by_filters_with_desc(
    db: Session, model: Type[T], **filters
) -> Optional[T]:
    return db.query(model).filter_by(**filters).order_by(model.id.desc()).first()

# Generic function to update a record
def update_record(
    db: Session, model: Type[T], filters: dict, updates: dict
) -> MessageResponse:
    try:
        # Fetch the record based on filters
        record = get_record_by_filters(db, model, **filters)
        if not record:
            raise ValueError("Record not found")

        # Apply updates
        for key, value in updates.items():
            if hasattr(record, key) and value is not None:
                setattr(record, key, value)

        # Commit changes to the database
        db.commit()
        db.refresh(record)
        return record
    except Exception as error:
        db.rollback()
        raise ValueError(f"Something went wrong. Please contact support: {str(error)}")


