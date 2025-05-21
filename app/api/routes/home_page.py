from datetime import datetime, timedelta, timezone
import json
import os
import shutil
from typing import List
from uuid import uuid4
from app.db.models.banner import Banners
from app.db.models.carts import Carts
from app.db.models.orders import (
    Order_details,
    Orders,
    Orders_status,
    Payment_details,
    order_selected_tags,
)
from app.db.models.product import *
from app.db.models.user import User, User_shipping_address
from app.schemas.request import AddToCartPayload, OrderCreatePayload
from app.schemas.response import CartDetailsResponse, ProductResponse, TagOptionResponse
from app.services.modal_services import (
    create_record,
    get_record_by_filters,
    get_record_by_filters_all,
)
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.config import Settings
from app.core.mail_conf import mail_conf
from app.db.session import get_db
from fastapi import HTTPException, status
from sqlalchemy.orm import joinedload, contains_eager
from sqlalchemy.sql import func

from app.utils.helpers import generate_order_id
from app.utils.task import generate_pdf_and_upload_to_s3, order_email_sent
from fastapi_mail import FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader

import razorpay

router = APIRouter()
settings = Settings()
razorpay_client = razorpay.Client(
    auth=("rzp_test_Km5OVlijd2UP0P", "CrIzUMqDpPNqsZzpqhhfM51A")
)


# 1.banner list api
# API to Get All Banners
@router.get("/banners/list/")
def get_banners(db: Session = Depends(get_db)):
    try:
        banners = db.query(Banners).all()
        return banners
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# 2.product list according filter type(best selling product,trending product,search)
@router.get("/products/list/")
def get_products(
    product_type: Optional[str] = "",
    search_name: Optional[str] = "",
    product_category_type: Optional[str] = "",
    db: Session = Depends(get_db),
):
    try:
        filters = {}
        if product_type:
            filters["product_type"] = product_type

        if search_name:
            filters["product_name"] = search_name

        if product_category_type:
            filters["product_category"] = product_category_type

        products = get_record_by_filters_all(db=db, model=Products, **filters)

        return products

    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/products/details/", response_model=ProductResponse)
def get_products_details(product_id: int, db: Session = Depends(get_db)):
    try:
        # Subquery to get only active product images
        active_images_subquery = (
            db.query(Product_images)
            .filter(Product_images.status == "approved")
            .subquery()
        )

        # Query to fetch product details with active images and ratings
        query = (
            db.query(Products)
            .outerjoin(
                active_images_subquery,
                Products.id == active_images_subquery.c.product_id,
            )  # Join only active images
            .outerjoin(
                Product_rating, Products.id == Product_rating.product_id
            )  # Join ratings
            .outerjoin(
                Certificate_colors, Products.id == Certificate_colors.product_id
            )  # Join ratings
            .outerjoin(
                Frame_colors, Products.id == Frame_colors.product_id
            )  # Join ratings
            .outerjoin(Frame_size, Products.id == Frame_size.product_id)  # Join ratings
            .outerjoin(
                Frame_Thickness, Products.id == Frame_Thickness.product_id
            )  # Join ratings
            .outerjoin(
                Product_tag_options, Products.id == Product_tag_options.product_id
            )  # Join ratings
            .filter(Products.id == product_id)
            .options(
                # contains_eager(Products.product_images, alias=active_images_subquery),  # Load only active images
                joinedload(Products.product_ratings),  # Load ratings
                joinedload(Products.certificate_colors),  # Load ratings
                joinedload(Products.frame_colors),  # Load ratings
                joinedload(Products.frame_size),  # Load ratings
                joinedload(Products.frame_thickness),  # Load ratings
                joinedload(Products.product_tag_options),  # Load ratings
            )
            .first()
        )

        # Deserialize tag_optional for each product_tag_option
        for tag_option in query.product_tag_options:
            if tag_option.tag_optional and isinstance(tag_option.tag_optional, str):
                try:
                    tag_option.tag_optional = json.loads(tag_option.tag_optional)
                except json.JSONDecodeError:
                    tag_option.tag_optional = {}

        return query
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# 3.Customer reviews api
@router.get("/products/reviews/")
def get_product_review_by_product_id(product_id: int, db: Session = Depends(get_db)):
    try:
        # Check if product exists
        product = db.query(Products).filter(Products.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Fetch product reviews
        product_reviews = (
            db.query(
                Product_rating.id,
                Product_rating.user_name,
                Product_rating.title,
                Product_rating.review,
                Product_rating.rating,
                Product_rating.created_at,
                func.group_concat(Product_Review_images.images).label(
                    "review_images"
                ),  # Group images
            )
            .outerjoin(
                Product_Review_images,
                Product_rating.id == Product_Review_images.product_rating_id,
            )
            .filter(Product_rating.product_id == product_id)
            .group_by(Product_rating.id)
            .all()
        )  # Fetch all matching results

        # Convert query result into a list of dictionaries
        formatted_reviews = [
            {
                "id": row.id,
                "user_name": row.user_name,
                "title": row.title,
                "review": row.review,
                "rating": row.rating,
                "created_at": (
                    row.created_at.strftime("%b %d, %Y") if row.created_at else None
                ),
                "review_images": (
                    row.review_images.split(",") if row.review_images else []
                ),  # Convert CSV to list
            }
            for row in product_reviews
        ]

        return formatted_reviews

    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/products/reviews/all/")
def get_product_review_by_product_all(db: Session = Depends(get_db)):
    try:
        # Check if product exists
        query = (
            db.query(
                Product_rating.id,
                Product_rating.user_name,
                Product_rating.title,
                Product_rating.review,
                Product_rating.rating,
                Product_rating.created_at,
                func.group_concat(Product_Review_images.images).label(
                    "review_images"
                ),  # Group all images
            )
            .outerjoin(
                Product_Review_images,
                Product_rating.id == Product_Review_images.product_rating_id,
            )  # Outer join to include ratings without images
            .group_by(Product_rating.id)  # Group by product rating ID
            .all()
        )
        # Convert query result into a list of dictionaries
        formatted_ratings = [
            {
                "id": row.id,
                "rating": row.rating,
                "user_name": row.user_name,
                "title": row.title,
                "review": row.review,
                "created_at": (
                    row.created_at.strftime("%b %d, %Y") if row.created_at else None
                ),
                "review_images": (
                    row.review_images.split(",") if row.review_images else []
                ),  # Convert CSV to list
            }
            for row in query
        ]
        return formatted_ratings
        # Create new review
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/products/certificate/color/list")
def get_product_certificate_color_list(db: Session = Depends(get_db)):
    try:
        instance = get_record_by_filters_all(db=db, model=Certificate_colors)
        return instance
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/products/frame/color/list")
def get_product_frame_color_list(db: Session = Depends(get_db)):
    try:
        instance = get_record_by_filters_all(db=db, model=Frame_colors)
        return instance
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/products/frame/size/list")
def get_product_frame_size_list(db: Session = Depends(get_db)):
    try:
        instance = get_record_by_filters_all(db=db, model=Frame_size)
        return instance
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/products/frame/thickness/list")
def get_product_frame_thickness_list(db: Session = Depends(get_db)):
    try:
        instance = get_record_by_filters_all(db=db, model=Frame_Thickness)
        return instance
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/product/add_to_cart/")
def product_add_to_cart(payload: AddToCartPayload, db: Session = Depends(get_db)):
    try:
        cart_details = create_record(
            db,
            Carts,
            product_id=payload.product_id,
            session_id=payload.session_id,
            certificate_color=payload.certificate_color,
            frame_color=payload.frame_color,
            frame_size=payload.frame_size,  # Store image path
            frame_thickness=payload.frame_thickness,
        )
        if cart_details is not None:
            tags = payload.tag_options if payload.tag_options else None
            if tags is not None:
                for objs in tags:
                    create_record(
                        db,
                        order_selected_tags,
                        product_id=payload.product_id,
                        cart_id=cart_details.id,
                        tag_name=objs["name"],
                        tag_data=objs["data"],
                    )

        return {"message": "Product  added in cart successfully"}

    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# --- GET API ---
@router.get(
    "/product/cart_details/{session_id}", response_model=List[CartDetailsResponse]
)
def get_cart_details(session_id: str, db: Session = Depends(get_db)):
    try:
        carts = db.query(Carts).filter(Carts.session_id == session_id).all()
        if not carts:
            raise ValueError("No cart items found for this session")
        result = []
        for cart in carts:
            product = (
                db.query(Products).filter(Products.id == cart.product_id).first()
            )  # Assuming Carts has relationship: `product = relationship("Products")`
            result.append(
                CartDetailsResponse(
                    cart_id=cart.id,
                    product_id=cart.product_id,
                    product_name=product.product_name,
                    price=product.price,
                    is_digital=product.is_digital,
                    thumbnail=product.thumbnail,
                )
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/product/delete_cart/{cart_id}")
def delete_cart_item(cart_id: int, db: Session = Depends(get_db)):
    try:
        # Fetch the cart item
        cart_item = db.query(Carts).filter(Carts.id == cart_id).first()
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        # Delete related tags
        db.query(order_selected_tags).filter(
            order_selected_tags.cart_id == cart_id
        ).delete()

        # Delete cart item
        db.delete(cart_item)
        db.commit()

        return {"message": "Cart item deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# create order
@router.post("/product/create/order/")
def create_product_order(total_amount: int, db: Session = Depends(get_db)):
    try:
        # 1. Get or create user
        razorpay_order = razorpay_client.order.create(
            {
                "amount": total_amount * 100,
                "currency": "INR",
                "receipt": generate_order_id(),
                "payment_capture": 1,
            }
        )
        return {
            "message": "Order created successfully",
            "razorpay_order": razorpay_order,
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order creation failed: {str(error)}",
        )


@router.post("/product/verify/order/")
def create_product_order(
    session_id: str,
    background_tasks: BackgroundTasks,
    payload: OrderCreatePayload,
    db: Session = Depends(get_db),
):
    try:
        # verify payments
        payment = razorpay_client.payment.fetch(payload.payment_id)
        print("payment", payment)
        if payment is None:
            raise ValueError("Payment not found")
        # 1. Get or create user
        user = db.query(User).filter(User.phone == payload.phone).first()
        if not user:
            user = User(
                username=payload.username,
                phone=payload.phone,
                email=payload.email,
                password=payload.phone,
                status="active",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 2. Create user shipping address
        shipping = User_shipping_address(
            user_email=payload.user_email,
            user_fname=payload.user_fname,
            user_lname=payload.user_lname,
            user_address=payload.user_address,
            city=payload.city,
            landmark=payload.landmark,
            state=payload.state,
            pincode=payload.pincode,
            country=payload.country,
            contact_mobile=payload.contact_mobile,
            user_id=user.id,
        )
        db.add(shipping)
        db.commit()
        db.refresh(shipping)

        # 3. Create main order
        order = Orders(
            user_id=user.id,
            total_amount=payload.total_amount,
            shipping_fee=payload.shipping_fee,
            shipping_address=shipping.id,
            paid_amount=payload.total_amount,
            txn_id=payment["order_id"],
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # 4. Fetch cart items
        carts = db.query(Carts).filter(Carts.session_id == session_id).all()
        if not carts:
            raise HTTPException(
                status_code=404, detail="No cart items found for session"
            )

        # 5. Add order details and assign tags
        for product in carts:
            order_detail = Order_details(
                user_id=user.id,
                product_id=product.product_id,
                order_id=order.id,
                quantity=1,
                certificate_color=(
                    product.certificate_color
                    if product.certificate_color is not None
                    else ""
                ),
                frame_color=(
                    product.frame_color if product.frame_color is not None else ""
                ),
                frame_size=product.frame_size if product.frame_size is not None else "",
                frame_thickness=(
                    product.frame_thickness
                    if product.frame_thickness is not None
                    else ""
                ),
            )
            db.add(order_detail)
            db.commit()
            db.refresh(order_detail)

            # Move associated tags from cart to order
            tag = (
                db.query(order_selected_tags)
                .filter(order_selected_tags.cart_id == product.id)
                .first()
            )
            if tag:
                tag.cart_id = None
                tag.order_id = order_detail.id
                db.commit()
                db.refresh(tag)

        # payment record
        payment_obj = Payment_details(
            order_id=order.id,
            user_id=user.id,
            payment_id=payload.payment_id,
            payment_amount=payment["amount"],
            payment_status=payment["status"],
            payment_response=payment,
        )

        db.add(payment_obj)
        db.commit()
        db.refresh(payment_obj)
        # order status update
        create_record(
            db,
            Orders_status,
            order_status="Pending",
            order_id=order.id,
            user_id=user.id,
        )

        # ✅ Delete cart item
        db.query(Carts).filter(Carts.session_id == session_id).delete()
        # db.delete(product)
        db.commit()
        # create order in Razorpay

        # Get order product details
        order_details = (
            db.query(Order_details).filter(Order_details.order_id == order.id).all()
        )

        product_details = []
        for order_det_obj in order_details:
            product = (
                db.query(Products)
                .filter(Products.id == order_det_obj.product_id)
                .first()
            )
            product_details.append(
                {
                    "product_id": product.id,
                    "product_name": product.product_name,
                    "price": product.price,
                    "is_digital": product.is_digital,
                    "thumbnail": product.thumbnail,
                    "thumbnail_url": settings.IMAGE_URL + product.thumbnail,
                    "certificate_color": order_det_obj.certificate_color,
                    "frame_color": order_det_obj.frame_color,
                }
            )

        # ✅ Build final order object
        order_obj = {
            "txn_id": order.txn_id,
            "user": {
                "id": user.id,
                "username": user.username,
                "phone": user.phone,
            },
            "shipping_address": {
                "user_email": shipping.user_email,
                "full_name": shipping.user_fname + " " + shipping.user_lname,
                "user_fname": shipping.user_fname,
                "user_lname": shipping.user_lname,
                "user_address": shipping.user_address,
                "city": shipping.city,
                "state": shipping.state,
                "pincode": shipping.pincode,
                "country": shipping.country,
                "contact_mobile": shipping.contact_mobile,
            },
            "products": product_details,
            "total_amount": order.total_amount,
            "amount": int(order.total_amount) - int(order.shipping_fee),
            "shipping_fee": order.shipping_fee,
            "paid_amount": order.paid_amount,
            "WEB_URL": settings.WEB_URL + order.txn_id,
        }

        background_tasks.add_task(order_email_sent, email_to=user.email, data=order_obj)

        # generate_pdf_and_upload_to_s3
        background_tasks.add_task(
            generate_pdf_and_upload_to_s3,
            db=db,
            file_name="order_invoice",
            data=order_obj,
            order_id=order.txn_id,
        )

        return {
            "message": "Payment created successfully",
            "order_id": order.id,
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order creation failed: {str(error)}",
        )


# get order full details by order id
@router.get("/product/order/details/{order_id}")
def get_cart_details(
    order_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    try:
        orders = db.query(Orders).filter(Orders.txn_id == order_id).first()
        if not orders:
            raise ValueError("Order details not found")

        # Get user
        user = db.query(User).filter(User.id == orders.user_id).first()

        # Get shipping address
        shipping_address = (
            db.query(User_shipping_address)
            .filter(User_shipping_address.id == orders.shipping_address)
            .first()
        )

        # Get order product details
        order_details = (
            db.query(Order_details).filter(Order_details.order_id == orders.id).all()
        )

        product_details = []
        for order_det_obj in order_details:
            product = (
                db.query(Products)
                .filter(Products.id == order_det_obj.product_id)
                .first()
            )
            product_details.append(
                {
                    "product_id": product.id,
                    "product_name": product.product_name,
                    "price": product.price,
                    "is_digital": product.is_digital,
                    "thumbnail": product.thumbnail,
                    "thumbnail_url": settings.IMAGE_URL + product.thumbnail,
                    "certificate_color": order_det_obj.certificate_color,
                    "frame_color": order_det_obj.frame_color,
                }
            )

        # Get order status history
        order_status = (
            db.query(Orders_status).filter(Orders_status.order_id == orders.id).all()
        )
        order_status_list = []
        for status_obj in order_status:
            order_status_list.append(
                {
                    "title": status_obj.order_status,
                    "description": status_obj.created_at.strftime("%d/%m/%Y"),
                }
            )

        # ✅ Build final order object
        order_obj = {
            "txn_id": orders.txn_id,
            "user": {
                "id": user.id,
                "username": user.username,
                "phone": user.phone,
            },
            "shipping_address": {
                "user_email": shipping_address.user_email,
                "full_name": shipping_address.user_fname
                + " "
                + shipping_address.user_lname,
                "user_fname": shipping_address.user_fname,
                "user_lname": shipping_address.user_lname,
                "user_address": shipping_address.user_address,
                "city": shipping_address.city,
                "state": shipping_address.state,
                "pincode": shipping_address.pincode,
                "country": shipping_address.country,
                "contact_mobile": shipping_address.contact_mobile,
            },
            "products": product_details,
            "order_status": order_status_list,
            "total_amount": orders.total_amount,
            "amount": int(orders.total_amount) - int(orders.shipping_fee),
            "shipping_fee": orders.shipping_fee,
            "paid_amount": orders.paid_amount,
            "invoice_url": orders.invoice,
            # "order_status_current": orders.order_status,
        }
        return order_obj  # return in list to match response_model

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send-email/")
async def send_email(email_to: str, subject: str):
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("index.html")
    html_content = template.render(user_name="John Doe")

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=html_content,
        subtype=MessageType.html,  # or .plain for plain text
    )
    fm = FastMail(mail_conf)
    await fm.send_message(message)
    return {"message": "Email sent successfully via Outlook"}
