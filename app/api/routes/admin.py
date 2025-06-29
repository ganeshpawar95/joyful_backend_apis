from datetime import datetime, timedelta, timezone
import json
import os
import shutil
from typing import Optional
from app.db.models.banner import Banners, Category
from app.db.models.orders import (
    Order_details,
    Orders,
    Orders_status,
    Payment_details,
    order_selected_tags,
)
from app.db.models.product import *
from app.db.models.user import SettingsModel, User, User_shipping_address
from app.schemas.request import SettingsSchema, UpdateProductPayload
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
from typing import List
from sqlalchemy.exc import SQLAlchemyError


router = APIRouter()
setting = Settings()


# 1.banner list api
@router.post("/upload-banner/")
async def upload_banner(
    file: UploadFile = File(...),
    file_mobile: UploadFile = File(...),
    banner_priority: int = 0,
    db: Session = Depends(get_db),
):
    try:
        file_path = os.path.join(setting.BANNER_DIR, file.filename)
        # Save File to Disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_path_mobile = os.path.join(setting.BANNER_DIR, file_mobile.filename)
        # Save File to Disk
        with open(file_path_mobile, "wb") as buffer:
            shutil.copyfileobj(file_mobile.file, buffer)

        # Save Metadata to DB
        create_record(
            db,
            Banners,
            banner_name=setting.BANNER_DIR + "/" + file.filename,
            banner_mobile=setting.BANNER_DIR + "/" + file_mobile.filename,
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


# Delete banner
@router.delete("/banners/{banner_id}")
def delete_banner(banner_id: int, db: Session = Depends(get_db)):
    try:
        banner = db.query(Banners).filter(Banners.id == banner_id).first()
        if not banner:
            raise HTTPException(status_code=404, detail="Banner not found")

        # Delete the banner from the database
        db.delete(banner)
        db.commit()

        # Optionally, delete the file from the filesystem
        if os.path.exists(banner.banner_name):
            os.remove(banner.banner_name)

        return {"message": "Banner deleted successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# category list api
@router.get("/category/list/")
def get_category_list(db: Session = Depends(get_db)):
    try:
        categories = db.query(Category).all()
        return categories
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# create category api
@router.post("/category/add/")
async def create_category(
    cat_name: str = Form(...),
    cat_priority: int = Form(...),
    cat_img: UploadFile = File(...),  # Image file input
    cat_mobile_img: UploadFile = File(...),  # Image file input
    db: Session = Depends(get_db),
):
    try:
        # Save the image
        file_path = os.path.join(setting.CATEGORY_DIR, cat_img.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(cat_img.file, buffer)

        file_path_mobile = os.path.join(setting.CATEGORY_DIR, cat_mobile_img.filename)

        with open(file_path_mobile, "wb") as buffer:
            shutil.copyfileobj(cat_mobile_img.file, buffer)

        # Create DB entry
        create_record(
            db,
            Category,
            cat_name=cat_name,
            cat_priority=cat_priority,
            cat_img=setting.CATEGORY_DIR + "/" + cat_img.filename,
            cat_mobile_img=setting.CATEGORY_DIR
            + "/"
            + cat_mobile_img.filename,  # Store image path
        )
        return {"message": "Category created successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# create api for update category
@router.put("/category/update/{category_id}/")
async def update_category(
    category_id: int,
    cat_name: str = Form(...),
    cat_priority: int = Form(...),
    cat_img: Optional[UploadFile] = File(None),
    cat_mobile_img: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    try:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        cat_img_path = category.cat_img
        cat_mobile_img_path = category.cat_mobile_img

        # Update cat_img if new file is provided
        if cat_img:
            if cat_img_path and os.path.exists(cat_img_path):
                os.remove(cat_img_path)
            cat_img_path = os.path.join(setting.CATEGORY_DIR, cat_img.filename)
            with open(cat_img_path, "wb") as buffer:
                shutil.copyfileobj(cat_img.file, buffer)

        # Update cat_mobile_img if new file is provided
        if cat_mobile_img:
            if cat_mobile_img_path and os.path.exists(cat_mobile_img_path):
                os.remove(cat_mobile_img_path)
            cat_mobile_img_path = os.path.join(
                setting.CATEGORY_DIR, cat_mobile_img.filename
            )
            with open(cat_mobile_img_path, "wb") as buffer:
                shutil.copyfileobj(cat_mobile_img.file, buffer)

        update_record(
            db,
            Category,
            filters={"id": category_id},
            updates={
                "cat_name": cat_name,
                "cat_priority": cat_priority,
                "cat_img": cat_img_path,
                "cat_mobile_img": cat_mobile_img_path,
            },
        )
        return {"message": "Category updated successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# category delete api
@router.delete("/category/delete/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    try:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Delete the category from the database
        db.delete(category)
        db.commit()

        # Optionally, delete the file from the filesystem
        if os.path.exists(category.cat_img):
            os.remove(category.cat_img)

        return {"message": "Category deleted successfully"}
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
    product_status: bool = Form(True),
    priority: int = Form(...),
    product_type: Optional[str] = Form(None),
    product_category: Optional[str] = Form(None),
    product_trading_type: Optional[str] = Form(None),
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
            product_trading_type=product_trading_type,
        )
        return {"message": "Product created successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


#
@router.put("/products/update/{product_id}/")
async def update_product(
    product_id: int,
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
    priority: int = Form(...),
    product_type: Optional[str] = Form(None),
    product_category: Optional[str] = Form(None),
    product_trading_type: Optional[str] = Form(None),
    is_digital: Optional[bool] = Form(False),
    product_status: Optional[bool] = Form(True),
    product_images: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    try:
        product = db.query(Products).filter(Products.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        thumbnail_path = product.thumbnail
        if product_images:
            # Remove old image if exists
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            # Save new image
            thumbnail_path = os.path.join(setting.product_DIR, product_images.filename)
            with open(thumbnail_path, "wb") as buffer:
                shutil.copyfileobj(product_images.file, buffer)

        update_record(
            db,
            Products,
            filters={"id": product_id},
            updates={
                "product_name": product_name,
                "url_name": url_name,
                "offer_price": offer_price,
                "price": price,
                "thumbnail": thumbnail_path,
                "description": description,
                "care_instructions": care_instructions,
                "delivery_info": delivery_info,
                "meta_title": meta_title,
                "meta_keywords": meta_keywords,
                "meta_desc": meta_desc,
                "priority": priority,
                "product_type": product_type,
                "is_digital": is_digital,
                "status": product_status,
                "product_category": product_category,
                "product_trading_type": product_trading_type,
            },
        )
        return {"message": "Product updated successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/products/list/")
def get_product_list(db: Session = Depends(get_db)):
    try:
        products = db.query(Products).all()
        return products
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# create for get product details by id
@router.get("/product/details/{product_id}")
def get_product_details(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(Products).filter(Products.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        product_dict = product.__dict__.copy()
        product_dict.pop("_sa_instance_state", None)
        # Optionally, add related images
        images = (
            db.query(Product_images)
            .filter(Product_images.product_id == product_id)
            .all()
        )
        product_dict["images"] = [img.images for img in images]
        # Optionally, add product reviews
        reviews = (
            db.query(Product_rating)
            .filter(Product_rating.product_id == product_id)
            .all()
        )
        product_dict["reviews"] = []
        for review in reviews:
            review_dict = review.__dict__.copy()
            review_dict.pop("_sa_instance_state", None)
            review_images = (
                db.query(Product_Review_images)
                .filter(Product_Review_images.product_rating_id == review.id)
                .all()
            )
            review_dict["images"] = [img.images for img in review_images]
            product_dict["reviews"].append(review_dict)
        return product_dict
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# create api for products delete


@router.delete("/products/delete/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(Products).filter(Products.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Optionally, delete product images from filesystem
        images = (
            db.query(Product_images)
            .filter(Product_images.product_id == product_id)
            .all()
        )
        for img in images:
            if os.path.exists(img.images):
                os.remove(img.images)
            db.delete(img)

        # Optionally, delete product reviews and their images
        reviews = (
            db.query(Product_rating)
            .filter(Product_rating.product_id == product_id)
            .all()
        )
        for review in reviews:
            review_images = (
                db.query(Product_Review_images)
                .filter(Product_Review_images.product_rating_id == review.id)
                .all()
            )
            for rimg in review_images:
                if os.path.exists(rimg.images):
                    os.remove(rimg.images)
                db.delete(rimg)
            db.delete(review)

        # add delete options certificate color,frame size,color,thickness
        # Delete certificate colors associated with this product
        certificate_colors = (
            db.query(Certificate_colors)
            .filter(Certificate_colors.product_id == product_id)
            .all()
        )
        for color in certificate_colors:
            db.delete(color)

        # Delete frame colors associated with this product
        frame_colors = (
            db.query(Frame_colors).filter(Frame_colors.product_id == product_id).all()
        )
        for color in frame_colors:
            db.delete(color)

        # Delete frame sizes associated with this product
        frame_sizes = (
            db.query(Frame_size).filter(Frame_size.product_id == product_id).all()
        )
        for size in frame_sizes:
            db.delete(size)

        # Delete frame thicknesses associated with this product
        frame_thicknesses = (
            db.query(Frame_Thickness)
            .filter(Frame_Thickness.product_id == product_id)
            .all()
        )
        for thickness in frame_thicknesses:
            db.delete(thickness)
        # Optionally, delete the product thumbnail from filesystem
        if product.thumbnail and os.path.exists(product.thumbnail):
            os.remove(product.thumbnail)

        # Delete product_tag_options associated with this product
        product_tags = (
            db.query(Product_tag_options)
            .filter(Product_tag_options.product_id == product_id)
            .all()
        )
        for tag in product_tags:
            db.delete(tag)

        db.delete(product)
        db.commit()
        return {"message": "Product deleted successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# 2.product list according filter type(best selling product,trending product,search)

# 3.Customer reviews api

# create api for product images delete and list


@router.get("/product/images/list/")
def list_product_images(db: Session = Depends(get_db)):
    try:
        images = db.query(Product_images).order_by(Product_images.id.desc()).all()
        result = []
        for img in images:
            img_dict = img.__dict__.copy()
            product = db.query(Products).filter(Products.id == img.product_id).first()
            if product:
                img_dict["product_details"] = {
                    "product_name": product.product_name,
                    "url_name": product.url_name,
                    "thumbnail": product.thumbnail,
                }
            else:
                img_dict["product_details"] = None
                img_dict.pop("_sa_instance_state", None)
            result.append(img_dict)
        return result
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.delete("/product/images/delete/{image_id}")
def delete_product_image(image_id: int, db: Session = Depends(get_db)):
    try:
        image = db.query(Product_images).filter(Product_images.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Product image not found")
        # Optionally, delete the file from the filesystem
        if os.path.exists(image.images):
            os.remove(image.images)
        db.delete(image)
        db.commit()
        return {"message": "Product image deleted successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


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
        image_path = os.path.join(setting.PRODUCT_IMG_DIR, image.filename)
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


# create list and delete products reviews api


@router.get("/products/reviews/list/")
def list_product_reviews(db: Session = Depends(get_db)):
    try:
        reviews = db.query(Product_rating).all()
        result = []
        for review in reviews:
            review_dict = review.__dict__.copy()
            review_dict.pop("_sa_instance_state", None)
            # Fetch review images
            images = (
                db.query(Product_Review_images)
                .filter(Product_Review_images.product_rating_id == review.id)
                .all()
            )
            review_dict["images"] = [img.images for img in images]
            product = (
                db.query(Products).filter(Products.id == review.product_id).first()
            )
            if product:
                review_dict["product_details"] = {
                    "product_name": product.product_name,
                    "url_name": product.url_name,
                    "thumbnail": product.thumbnail,
                }
            else:
                review_dict["product_details"] = None
                review_dict.pop("_sa_instance_state", None)
            result.append(review_dict)
        return result
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.delete("/products/reviews/delete/{review_id}")
def delete_product_review(review_id: int, db: Session = Depends(get_db)):
    try:
        review = db.query(Product_rating).filter(Product_rating.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        # Delete associated images
        images = (
            db.query(Product_Review_images)
            .filter(Product_Review_images.product_rating_id == review_id)
            .all()
        )
        for img in images:
            if os.path.exists(img.images):
                os.remove(img.images)
            db.delete(img)
        db.delete(review)
        db.commit()
        return {"message": "Product review deleted successfully"}
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
            file_path = os.path.join(setting.PRODUCT_REVIEW_DIR, file.filename)
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


# create list and delete certificate color api
@router.get("/certificate/color/list/")
def list_certificate_colors(db: Session = Depends(get_db)):
    try:
        colors = db.query(Certificate_colors).all()
        ## add product details to each Certificate_colors
        result = []
        print("colors", colors)
        for color in colors:
            color_dict = color.__dict__.copy()
            product = db.query(Products).filter(Products.id == color.product_id).first()
            if product:
                color_dict["product_details"] = {
                    "product_name": product.product_name,
                    "url_name": product.url_name,
                    "thumbnail": product.thumbnail,
                }
            else:
                color_dict["product_details"] = None
                color_dict.pop("_sa_instance_state", None)
            result.append(color_dict)
        return result

    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.delete("/certificate/color/delete/{color_id}")
def delete_certificate_color(color_id: int, db: Session = Depends(get_db)):
    try:
        color = (
            db.query(Certificate_colors)
            .filter(Certificate_colors.id == color_id)
            .first()
        )
        if not color:
            raise HTTPException(status_code=404, detail="Certificate color not found")
        db.delete(color)
        db.commit()
        return {"message": "Certificate color deleted successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/certificate/color/add/")
def add_certificate_color(
    payload: list[ProductFrameCreate], db: Session = Depends(get_db)
):
    try:
        for color_data in payload:
            create_record(
                db,
                Certificate_colors,
                name=color_data.name,
                status=color_data.status,
                priority=color_data.priority,
                product_id=color_data.product_id,
            )
        return {"message": "Certificate colors added successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# create list and delete frame color api


@router.get("/frame/color/list/")
def list_frame_colors(db: Session = Depends(get_db)):
    try:
        colors = db.query(Frame_colors).all()
        # add product details to each color
        result = []
        for color in colors:
            color_dict = color.__dict__.copy()
            product = db.query(Products).filter(Products.id == color.product_id).first()
            if product:
                color_dict["product_details"] = {
                    "product_name": product.product_name,
                    "url_name": product.url_name,
                    "thumbnail": product.thumbnail,
                }
            else:
                color_dict["product_details"] = None
                color_dict.pop("_sa_instance_state", None)
            result.append(color_dict)
        return result
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.delete("/frame/color/delete/{color_id}")
def delete_frame_color(color_id: int, db: Session = Depends(get_db)):
    try:
        color = db.query(Frame_colors).filter(Frame_colors.id == color_id).first()
        if not color:
            raise HTTPException(status_code=404, detail="Frame color not found")
        db.delete(color)
        db.commit()
        return {"message": "Frame color deleted successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/frame/color/add/")
def add_frame_color(payload: List[ProductFrameCreate], db: Session = Depends(get_db)):
    try:
        # Create new certificate color
        for data_obj in payload:
            create_record(
                db,
                Frame_colors,
                name=data_obj.name,
                status=data_obj.status,
                priority=data_obj.priority,
                product_id=data_obj.product_id,
            )
        return {"message": "Frame color added successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# create list and delete frame size api


@router.get("/frame/size/list/")
def list_frame_sizes(db: Session = Depends(get_db)):
    try:
        sizes = db.query(Frame_size).all()
        # add product details to each size
        result = []
        for size in sizes:
            size_dict = size.__dict__.copy()
            product = db.query(Products).filter(Products.id == size.product_id).first()
            if product:
                size_dict["product_details"] = {
                    "product_name": product.product_name,
                    "url_name": product.url_name,
                    "thumbnail": product.thumbnail,
                }
            else:
                size_dict["product_details"] = None
                size_dict.pop("_sa_instance_state", None)
            result.append(size_dict)
        return result
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.delete("/frame/size/delete/{size_id}")
def delete_frame_size(size_id: int, db: Session = Depends(get_db)):
    try:
        size = db.query(Frame_size).filter(Frame_size.id == size_id).first()
        if not size:
            raise HTTPException(status_code=404, detail="Frame size not found")
        db.delete(size)
        db.commit()
        return {"message": "Frame size deleted successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/frame/size/add/")
def add_frame_color(payload: List[ProductFrameCreate], db: Session = Depends(get_db)):
    try:
        # Create new frame size
        for data_obj in payload:
            create_record(
                db,
                Frame_size,
                name=data_obj.name,
                status=data_obj.status,
                priority=data_obj.priority,
                product_id=data_obj.product_id,
            )
        return {"message": "Frame size added successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# create list and delete frame thickness api


@router.get("/frame/thickness/list/")
def list_frame_thicknesses(db: Session = Depends(get_db)):
    try:
        thicknesses = db.query(Frame_Thickness).all()
        # add product details to each thickness
        result = []
        for thickness in thicknesses:
            thickness_dict = thickness.__dict__.copy()
            product = (
                db.query(Products).filter(Products.id == thickness.product_id).first()
            )
            if product:
                thickness_dict["product_details"] = {
                    "product_name": product.product_name,
                    "url_name": product.url_name,
                    "thumbnail": product.thumbnail,
                }
            else:
                thickness_dict["product_details"] = None
                thickness_dict.pop("_sa_instance_state", None)
            result.append(thickness_dict)
        return result
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.delete("/frame/thickness/delete/{thickness_id}")
def delete_frame_thickness(thickness_id: int, db: Session = Depends(get_db)):
    try:
        thickness = (
            db.query(Frame_Thickness).filter(Frame_Thickness.id == thickness_id).first()
        )
        if not thickness:
            raise HTTPException(status_code=404, detail="Frame thickness not found")
        db.delete(thickness)
        db.commit()
        return {"message": "Frame thickness deleted successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/frame/thickness/add/")
def add_frame_color(payload: List[ProductFrameCreate], db: Session = Depends(get_db)):
    try:
        # Create new frame size
        for data_obj in payload:
            create_record(
                db,
                Frame_Thickness,
                name=data_obj.name,
                status=data_obj.status,
                priority=data_obj.priority,
                product_id=data_obj.product_id,
            )
        return {"message": "Frame thickness added successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# Product_tag_options


@router.post("/product/tag_option/add/")
def add_product_tag_options(
    payload: List[ProductTagCreate], db: Session = Depends(get_db)
):
    try:
        for tag_data in payload:
            create_record(
                db,
                Product_tag_options,
                product_id=tag_data.product_id,
                name=tag_data.name,
                tag=tag_data.tag,
                validation_img=tag_data.validation_img,
                priority=tag_data.priority,
                tag_optional=(
                    json.dumps(tag_data.tag_optional) if tag_data.tag_optional else None
                ),
            )
        return {"message": "Product tags added successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# create api for update product tag options
@router.put("/product/tag_option/update/")
def update_product_tag_options(
    tag_id: int,
    payload: ProductTagCreate,
    db: Session = Depends(get_db),
):
    try:
        # Ensure product_id is not None
        if payload.product_id is None:
            raise HTTPException(status_code=400, detail="product_id cannot be None")
        # Update product tag
        update_record(
            db,
            Product_tag_options,
            filters={"id": tag_id},
            updates={
                "product_id": payload.product_id,
                "name": payload.name,
                "tag": payload.tag,
                "priority": payload.priority,
                "tag_optional": (
                    json.dumps(payload.tag_optional) if payload.tag_optional else None
                ),
            },
        )
        return {"message": "Product tag updated successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# product list api
@router.get("/product/list/")
def get_product_list(db: Session = Depends(get_db)):
    try:
        result = []
        products = db.query(Products).all()
        for product in products:
            product_dict = product.__dict__.copy()
            product_dict.pop(
                "_sa_instance_state", None
            )  # remove SQLAlchemy internal attribute
            result.append(product_dict)
        return result
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# product tag list api
@router.get("/product/tag/list/")
def get_product_tag_list(db: Session = Depends(get_db)):
    try:
        result = []
        product_tags = db.query(Product_tag_options).all()
        # add product details to each tag
        for tag in product_tags:
            tag_dict = tag.__dict__.copy()
            product = db.query(Products).filter(Products.id == tag.product_id).first()
            if product:
                tag_dict["product_details"] = {
                    "product_name": product.product_name,
                    "url_name": product.url_name,
                    "thumbnail": product.thumbnail,
                }
            else:
                tag_dict["product_details"] = None

            tag_dict.pop("_sa_instance_state", None)
            result.append(tag_dict)

        return result
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# product tag delete api
@router.delete("/product/tag/delete/{tag_id}")
def delete_product_tag(tag_id: int, db: Session = Depends(get_db)):
    try:
        tag = (
            db.query(Product_tag_options)
            .filter(Product_tag_options.id == tag_id)
            .first()
        )
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")

        # Delete the tag from the database
        db.delete(tag)
        db.commit()

        return {"message": "Tag deleted successfully"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# order list
@router.get("/order/list/")
def get_order_list(db: Session = Depends(get_db)):
    try:
        orders = db.query(Orders).order_by(Orders.created_at.desc()).all()
        order_res = []
        for order in orders:
            shipping_address = (
                db.query(User_shipping_address)
                .filter(User_shipping_address.id == order.shipping_address)
                .first()
            )

            user = db.query(User).filter(User.id == order.user_id).first()
            payments = (
                db.query(Payment_details)
                .filter(Payment_details.order_id == order.id)
                .first()
            )

            order_details = (
                db.query(Order_details).filter(Order_details.order_id == order.id).all()
            )

            order_status = (
                db.query(Orders_status)
                .filter(Orders_status.order_id == order.id)
                .order_by(Orders_status.created_at.desc())
                .first()
            )

            order_data = order.__dict__.copy()
            order_data["shipping_address"] = shipping_address
            order_data["order_details"] = order_details
            order_data["payments"] = payments
            order_data["order_status"] = order_status
            order_data["user"] = user
            order_data.pop(
                "_sa_instance_state", None
            )  # remove SQLAlchemy internal attribute
            order_res.append(order_data)

        return order_res
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# make api for get order details by id ,update order status by id


@router.get("/order/details/{order_id}")
def get_order_details(order_id: int, db: Session = Depends(get_db)):
    try:
        order = db.query(Orders).filter(Orders.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        shipping_address = (
            db.query(User_shipping_address)
            .filter(User_shipping_address.id == order.shipping_address)
            .first()
        )
        user = db.query(User).filter(User.id == order.user_id).first()
        payments = (
            db.query(Payment_details)
            .filter(Payment_details.order_id == order.id)
            .first()
        )
        order_details = (
            db.query(Order_details).filter(Order_details.order_id == order.id).all()
        )
        order_details_json = []
        # Add product details to each order_detail
        for detail in order_details:
            detail = detail.__dict__.copy()

            product = (
                db.query(Products).filter(Products.id == detail["product_id"]).first()
            )

            product_selected_tag = (
                db.query(order_selected_tags)
                .filter(
                    order_selected_tags.order_id == order_id,
                    order_selected_tags.product_id == product.id,
                )
                .all()
            )

            #
            if product:
                detail["product_details"] = {
                    "product_name": product.product_name,
                    "url_name": product.url_name,
                    "thumbnail": product.thumbnail,
                    "price": product.price,
                    "product_selected_tag": product_selected_tag,
                }
            else:
                detail["product_details"] = None
            order_details_json.append(detail)
        order_statuses = (
            db.query(Orders_status)
            .filter(Orders_status.order_id == order.id)
            .order_by(Orders_status.created_at.desc())
            .all()
        )

        order_data = order.__dict__.copy()
        order_data["shipping_address"] = shipping_address
        order_data["order_details"] = order_details_json
        order_data["payments"] = payments
        order_data["order_statuses"] = order_statuses
        order_data["user"] = user
        order_data.pop("_sa_instance_state", None)
        return order_data
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.put("/order/status/update/{order_id}")
def update_order_status(
    order_id: int, order_status: str, db: Session = Depends(get_db)
):
    try:
        order = db.query(Orders).filter(Orders.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Add new status entry
        new_status = create_record(
            db,
            Orders_status,
            user_id=order.user_id,
            order_id=order_id,
            order_status=order_status,
        )
        return {
            "message": "Order status updated successfully",
            "order_status_id": new_status.id,
        }
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# settings
@router.post("/settings/add-or-update/")
def add_or_update_settings(payload: SettingsSchema, db: Session = Depends(get_db)):
    try:
        settings = db.query(SettingsModel).first()
        if settings:
            # Update existing settings
            settings.pricesWithTax = payload.pricesWithTax
            settings.pricesWithShipping = payload.pricesWithShipping
            settings.taxRate = payload.taxRate
            settings.shippingCharges = payload.shippingCharges
            db.commit()
            db.refresh(settings)
            return {"message": "Settings updated successfully"}
        else:
            # Create new settings
            new_settings = SettingsModel(
                pricesWithTax=payload.pricesWithTax,
                pricesWithShipping=payload.pricesWithShipping,
                taxRate=payload.taxRate,
                shippingCharges=payload.shippingCharges,
            )
            db.add(new_settings)
            db.commit()
            db.refresh(new_settings)
            return {"message": "Settings created successfully"}
    except SQLAlchemyError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/settings/list/")
def list_settings(db: Session = Depends(get_db)):
    try:
        settings = db.query(SettingsModel).first()
        return settings
    except SQLAlchemyError as error:
        raise HTTPException(status_code=400, detail=str(error))
