from datetime import datetime, timedelta, timezone
import json
import os
import shutil
from typing import Optional
from app.db.models.banner import Banners
from app.db.models.product import *
from app.schemas.request import UpdateProductPayload
from app.schemas.response import (
    ProductFrameCreate,
    ProductReviewCreate,
    ProductTagCreate,
)
from app.services.modal_services import create_record, update_record
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.config import Settings
from app.core import security
from app.db.session import get_db
from fastapi import HTTPException, status


router = APIRouter()
setting = Settings()


# 1.banner list api
@router.post("/upload-banner/")
async def upload_banner(
    file: UploadFile = File(...),
    banner_priority: int = 0,
    db: Session = Depends(get_db),
):
    try:
        file_path = os.path.join(setting.BANNER_DIR, file.filename)
        # Save File to Disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # Save Metadata to DB
        create_record(
            db,
            Banners,
            banner_name=setting.BANNER_DIR + "/" + file.filename,
            banner_priority=banner_priority,
        )
        return {"message": "Banner uploaded successfully", "filename": file.filename}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# API to Get All Banners
@router.get("/banners/")
def get_banners_all(db: Session = Depends(get_db)):
    try:
        banners = db.query(Banners).all()
        return banners
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# 2. add product
@router.post("/products/add/")
async def create_product(
    product_name: str = Form(...),
    url_name: str = Form(...),
    offer_price: str = Form(...),
    price: str = Form(...),
    description: str = Form(...),
    care_instructions: Optional[str] = Form(None),
    delivery_info: Optional[str] = Form(None),
    meta_title: Optional[str] = Form(None),
    meta_keywords: Optional[str] = Form(None),
    meta_desc: Optional[str] = Form(None),
    product_status: bool = Form(...),
    priority: int = Form(...),
    product_type: Optional[str] = Form(None),
    product_category: Optional[str] = Form(None),
    is_digital: Optional[bool] = Form(False),
    product_images: UploadFile = File(...),  # Image file input
    db: Session = Depends(get_db),
):
    try:
        # Save the image
        file_path = os.path.join(setting.product_DIR, product_images.filename)

        # image_path = f"images/products/{product_images.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(product_images.file, buffer)

        # Create DB entry
        create_record(
            db,
            Products,
            product_name=product_name,
            url_name=url_name,
            offer_price=offer_price,
            price=price,
            thumbnail=file_path,  # Store image path
            description=description,
            care_instructions=care_instructions,
            delivery_info=delivery_info,
            meta_title=meta_title,
            meta_keywords=meta_keywords,
            meta_desc=meta_desc,
            status=product_status,
            priority=priority,
            product_type=product_type,
            is_digital=is_digital,
            product_category=product_category,
        )
        return {"message": "Product created successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.put("/product/update/")
async def update_product_details(
    product_id: int,
    description: Optional[str] = None,
    delivery_info: Optional[str] = None,
    care_instructions: Optional[str] = None,
    offer_price: Optional[int] = None,
    price: Optional[int] = None,
    db: Session = Depends(get_db),
):
    try:
        # Save Metadata to DB
        update_record(
            db,
            Products,
            filters={"id": product_id},
            updates={
                "price": price,
                "offer_price": offer_price,
                "description": description,
                "delivery_info": delivery_info,
                "care_instructions": care_instructions,
            },
        )
        return {"message": "Product details updated successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/products/list/")
def get_product_list(db: Session = Depends(get_db)):
    try:
        products = db.query(Products).all()
        return products
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# 2.product list according filter type(best selling product,trending product,search)

# 3.Customer reviews api


# 4product images updated
@router.post("/product/images/add/")
async def upload_product_images(
    image: UploadFile = File(...),
    product_id: str = Form(...),
    priority: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        # Save the image
        image_path = os.path.join(
            setting.BASE_IMG_DIR + "products/banners/", image.filename
        )
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        # Save Metadata to DB
        create_record(
            db,
            Product_images,
            images=image_path,
            product_id=product_id,
            status="active",
            priority=priority,
        )
        return {"message": "Product banner uploaded successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/products/reviews/")
def add_product_review(
    files: List[UploadFile] = File(...),
    product_id: int = Form(...),
    user_name: str = Form(...),
    title: str = Form(...),
    review: str = Form(...),
    rating: int = Form(...),
    db: Session = Depends(get_db),
):
    try:
        # Check if product exists
        product = db.query(Products).filter(Products.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        file_paths = []
        for file in files:
            file_path = os.path.join(setting.BASE_IMG_DIR + "reviews/", file.filename)
            # Save file to the upload directory
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(file_path)

        # Create new review
        query = create_record(
            db,
            Product_rating,
            product_id=product_id,
            user_name=user_name,
            title=title,
            review=review,
            rating=rating,
            status="approved",
        )

        # save images in db
        for img in file_paths:
            create_record(
                db,
                Product_Review_images,
                product_rating_id=query.id,
                images=img,
            )
        return {"message": "Review added successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/certificate/color/add/")
def add_certificate_color(payload: ProductFrameCreate, db: Session = Depends(get_db)):
    try:
        # Create new certificate color
        create_record(
            db,
            Certificate_colors,
            name=payload.name,
            status=payload.status,
            priority=payload.priority,
            product_id=payload.product_id,
        )
        return {"message": "Certificate color added successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/frame/color/add/")
def add_frame_color(payload: ProductFrameCreate, db: Session = Depends(get_db)):
    try:
        # Create new certificate color
        create_record(
            db,
            Frame_colors,
            name=payload.name,
            status=payload.status,
            priority=payload.priority,
            product_id=payload.product_id,
        )
        return {"message": "Frame color added successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/frame/size/add/")
def add_frame_color(payload: ProductFrameCreate, db: Session = Depends(get_db)):
    try:
        # Create new frame size
        create_record(
            db,
            Frame_size,
            name=payload.name,
            status=payload.status,
            priority=payload.priority,
            product_id=payload.product_id,
        )
        return {"message": "Frame size added successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/frame/thickness/add/")
def add_frame_color(payload: ProductFrameCreate, db: Session = Depends(get_db)):
    try:
        # Create new frame size
        create_record(
            db,
            Frame_Thickness,
            name=payload.name,
            status=payload.status,
            priority=payload.priority,
            product_id=payload.product_id,
        )
        return {"message": "Frame thickness added successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# Product_tag_options


@router.post("/product/tag_option/add/")
def add_product_tag_options(payload: ProductTagCreate, db: Session = Depends(get_db)):
    try:
        # Create new product tag
        create_record(
            db,
            Product_tag_options,
            product_id=payload.product_id,
            name=payload.name,
            tag=payload.tag,
            priority=payload.priority,
            tag_optional=(
                json.dumps(payload.tag_optional) if payload.tag_optional else None
            ),
        )
        return {"message": "Product tag added successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
