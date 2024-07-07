from datetime import datetime
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordBearer
from jinja2 import Template
from auth import BuyerAuth, SellerAuth, UserAuth
from models import ShoppingCart, Product, Order, Payment, User
from db import db
import config
import stripe

from sideFunctions import get_payment_form_html, send_delivery_notification_email, send_order_confirmation_email, send_seller_notification_email

stripe.api_key = config.STRIPE_SECRET_KEY

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/create-payment")
async def create_payment(
    request: Request,
    token: str = Depends(oauth2_scheme)
):
    try:
            
        body = await request.json()
        payment_method = body.get("payment_method")
        if payment_method not in ["payment_intent", "payment_link"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment method")

        user_id = await BuyerAuth(token)
        cart_items = await db["shopping_carts"].find({"user_id": user_id}).to_list(length=None)
        if not cart_items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart is empty")

        sellers = {}
        total_amount = 0

        for item in cart_items:
            product = await db["products"].find_one({"_id": item["product_id"], "isDeleted": False})
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {item['product_id']} not found")

            seller_id = product["seller_id"]
            if seller_id not in sellers:
                sellers[seller_id] = {
                    "products": [],
                    "total_price": 0
                }

            sellers[seller_id]["products"].append(item)
            sellers[seller_id]["total_price"] += product["price"] * item["quantity"]
            total_amount += product["price"] * item["quantity"]

        if payment_method == "payment_intent":
            try:
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(total_amount * 100),
                    currency="usd",
                    payment_method_types=["card"],
                )
                payment_id = payment_intent.id
                client_secret = payment_intent.client_secret

                payment_url = f"{config.API_URL}/orders/payment_form?client_secret={client_secret}&success_url={config.SUCCESS_URL}?payment_id={payment_id}"
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        elif payment_method == "payment_link":
            line_items = []
            for item in cart_items:
                product = await db["products"].find_one({"_id": item["product_id"], "isDeleted": False})
                price = stripe.Price.create(
                    currency="usd",
                    unit_amount=int(product["price"] * 100),
                    product_data={"name": product["name"]},
                )
                line_items.append({
                    "price": price.id,
                    "quantity": item["quantity"]
                })

            try:
                payment_link = stripe.PaymentLink.create(
                    line_items=line_items,
                )
                payment_id = payment_link.id
                payment_url = payment_link.url
                # Update the payment link URLs to include the payment_id
                success_url = f'{config.SUCCESS_URL}?payment_id={payment_link.id}'

                stripe.PaymentLink.modify(
                    payment_link.id,
                    after_completion={"type": "redirect", "redirect": {"url": success_url}}
                )
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        for seller_id, order_data in sellers.items():
            order = Order(
                seller_id=seller_id,
                user_id=user_id,
                payment_id=payment_id,
                products=order_data["products"],
                total_price=order_data["total_price"],
                status="pending"
            )
            await db["orders"].insert_one(order.dict(by_alias=True))

        payment = Payment(
            user_id=user_id,
            payment_id=payment_id,
            payment_method=payment_method,
            status="pending"
        )
        await db["payments"].insert_one(payment.dict(by_alias=True))

        return {"paymentUrl": payment_url}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")




@router.get("/getmyOrders")
async def get_my_orders(
token: str = Depends(oauth2_scheme)
):
    try:
        user = await UserAuth(token)
        userEmailType="Seller"
        query = {"status": "confirmed"}
        if user['is_seller']:
            userEmailType="Buyer"
            query["seller_id"] = user['_id']
        else:
            query["user_id"] = user['_id']

        # Use aggregation to join orders with products
        pipeline = [
            {"$match": query},
            {
                "$lookup": {
                    "from": "products",
                    "localField": "products.product_id",
                    "foreignField": "_id",
                    "as": "product_details"
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "buyer_details"
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "seller_id",
                    "foreignField": "_id",
                    "as": "seller_details"
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "user_id": 1,
                    "seller_id": 1,
                    "total_price": 1,
                    "status": 1,
                    "created_at": 1,
                    "updated_at": 1,
                    "products": {
                        "$map": {
                            "input": "$products",
                            "as": "item",
                            "in": {
                                "product_id": "$$item.product_id",
                                "quantity": "$$item.quantity",
                                "product_details": {
                                    "$arrayElemAt": [
                                        {
                                            "$filter": {
                                                "input": "$product_details",
                                                "as": "product",
                                                "cond": {
                                                    "$eq": ["$$product._id", "$$item.product_id"]
                                                }
                                            }
                                        },
                                        0
                                    ]
                                }
                            }
                        }
                    },
                    "email": {
                        "$cond": {
                            "if": user['is_seller'],
                            "then": {"$arrayElemAt": ["$buyer_details.email", 0]},
                            "else": {"$arrayElemAt": ["$seller_details.email", 0]}
                        }
                    }
                }
            }
        ]
 

        orders = await db["orders"].aggregate(pipeline).to_list(length=None)
        
        if not orders:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No orders found")

        # Construct result
        result = []
        for order in orders:
            order_data = {
                "order_id": order["_id"],
                "user_id": order["user_id"],
                "total_price": order["total_price"],
                "status": order["status"],
                "created_at": order["created_at"],
                "updated_at": order["updated_at"],
                f"{userEmailType} email":order['email'],
                "products": []
            }
            for item in order["products"]:
                product = item["product_details"]
                if product:
                    order_data["products"].append({
                        "product_id": product["_id"],
                        "product_name": product["name"],
                        "quantity": item["quantity"],
                        "price": product["price"]
                    })
            result.append(order_data)
        
        return result
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")


@router.get("/getOrderById/{order_id}")
async def get_order_by_id(
    order_id: str,
    token: str = Depends(oauth2_scheme)
):
    try:
        user = await UserAuth(token)
        userEmailType = "Buyer"
        query = {"_id":order_id, "status": "confirmed"}
        if user['is_seller']:
            userEmailType = "Seller"
            query["seller_id"] = user['_id']
        else:
            query["user_id"] = user['_id']

        # Use aggregation to join orders with products
        pipeline = [
            {"$match": query},
            {
                "$lookup": {
                    "from": "products",
                    "localField": "products.product_id",
                    "foreignField": "_id",
                    "as": "product_details"
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "buyer_details"
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "seller_id",
                    "foreignField": "_id",
                    "as": "seller_details"
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "user_id": 1,
                    "seller_id": 1,
                    "total_price": 1,
                    "status": 1,
                    "created_at": 1,
                    "updated_at": 1,
                    "products": {
                        "$map": {
                            "input": "$products",
                            "as": "item",
                            "in": {
                                "product_id": "$$item.product_id",
                                "quantity": "$$item.quantity",
                                "product_details": {
                                    "$arrayElemAt": [
                                        {
                                            "$filter": {
                                                "input": "$product_details",
                                                "as": "product",
                                                "cond": {
                                                    "$eq": ["$$product._id", "$$item.product_id"]
                                                }
                                            }
                                        },
                                        0
                                    ]
                                }
                            }
                        }
                    },
                    "email": {
                        "$cond": {
                            "if": user['is_seller'],
                            "then": {"$arrayElemAt": ["$buyer_details.email", 0]},
                            "else": {"$arrayElemAt": ["$seller_details.email", 0]}
                        }
                    }
                }
            }
        ]

        orders = await db["orders"].aggregate(pipeline).to_list(length=None)
        
        if not orders:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        order = orders[0]  # Since we are fetching by ID, there should be only one order
        order_data = {
            "order_id": order["_id"],
            "user_id": order["user_id"],
            "total_price": order["total_price"],
            "status": order["status"],
            "created_at": order["created_at"],
            "updated_at": order["updated_at"],
            f"{userEmailType} email": order['email'],
            "products": []
        }
        for item in order["products"]:
            product = item["product_details"]
            if product:
                order_data["products"].append({
                    "product_id": product["_id"],
                    "product_name": product["name"],
                    "quantity": item["quantity"],
                    "price": product["price"]
                })

        return order_data
    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")


@router.put("/setOrderStatusToDelivered/{order_id}")
async def set_order_status_to_delivered(
    order_id: str,
    token: str = Depends(oauth2_scheme)
):
    try:
        user = await UserAuth(token)
        
        if not user['is_seller']:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Only sellers can update order status")

        async with await db.client.start_session() as s:
            async with s.start_transaction():
                order = await db["orders"].find_one({"_id": order_id, "seller_id": user['_id'], "status": "confirmed"}, session=s)
                if not order:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or you are not authorized to update this order")

                buyer = await db["users"].find_one({"_id":order["user_id"]}, session=s)
                if not buyer:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer not found")

                # Update order status to delivered
                await db["orders"].update_one(
                    {"_id": order_id},
                    {"$set": {"status": "delivered", "updated_at": datetime.utcnow()}},
                    session=s
                )

                # Send email to buyer on behalf of seller
                send_delivery_notification_email(buyer["email"], user["email"])

                return {"message": "Order status updated to delivered and email sent to buyer"}


    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")

@router.get("/payment_form")
async def serve_payment_form(
    client_secret: str = Query(...),
    success_url: str = Query(...)
):
    html_content = get_payment_form_html(client_secret=client_secret, stripe_public_key=config.STRIPE_PUBLIC_KEY, success_url=success_url)
    return HTMLResponse(content=html_content)

async def update_order_status(payment_id: str, status: str):
    orders = await db["orders"].find({"payment_id": payment_id, "status": "pending"}).to_list(length=None)
    for order in orders:
        await db["orders"].update_one(
            {"_id": order["_id"]},
            {"$set": {"status": status}}
        )

async def get_total_order_items(payment_id: str, user_email: str):
    total_order_items = []
    total_price = 0  # Initialize total_price here
    orders = await db["orders"].find({"payment_id": payment_id}).to_list(length=None)
    for order in orders:
        items = []
        for item in order["products"]:
            product = await db["products"].find_one({"_id": item["product_id"]})
            items.append({
                "quantity": item["quantity"],
                "product_name": product["name"],
                "product_price": product["price"]
            })
            total_price += item["quantity"] * product["price"]  # Update total_price for each product
            print(total_price)
        seller = await db["users"].find_one({"_id": order["seller_id"]})
        seller_total = sum(item["quantity"] * item["product_price"] for item in items)
        send_seller_notification_email(seller["email"], user_email, items, seller_total)
        total_order_items.extend(items)
    return total_order_items, total_price  



@router.get("/confirm-payment", response_class=HTMLResponse)
async def confirm_payment(
    payment_id: str = Query(...)
):
    try:
        payment = await db["payments"].find_one({"payment_id": payment_id, "status": "pending"})
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

        user_id = payment["user_id"]
        user = await db["users"].find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


        if payment["payment_method"] == "payment_intent":
            intent = stripe.PaymentIntent.retrieve(payment_id)
            if intent.status == "succeeded":
                await update_order_status(payment_id, "confirmed")
                await db["payments"].update_one(
                    {"_id": payment["_id"]},
                    {"$set": {"status": "confirmed"}}
                )
                total_order_items, total_price = await get_total_order_items(payment_id, user["email"])  # Unpack both values
                send_order_confirmation_email(user["email"], total_order_items, total_price)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment not completed")
        elif payment["payment_method"] == "payment_link":
            session = stripe.PaymentLink.retrieve(payment_id)
            if session.active:
                await update_order_status(payment_id, "confirmed")
                await db["payments"].update_one(
                    {"_id": payment["_id"]},
                    {"$set": {"status": "confirmed"}}
                )
                total_order_items, total_price = await get_total_order_items(payment_id, user["email"])  # Unpack both values
                send_order_confirmation_email(user["email"], total_order_items, total_price)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment not completed")
        await db["shopping_carts"].delete_many({"user_id":user_id})    
        html_template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Order Confirmation</title>
        </head>
        <body>
            <h1>Thank you for your order!</h1>
            <p>Your order has been confirmed. Here are the details:</p>
            <ul>
                {% for item in items %}
                <li>{{ item['quantity'] }} x {{ item['product_name'] }} - ${{ item['product_price'] }}</li>
                {% endfor %}
            </ul>
            <p>Total: ${{ total_price }}</p>
        </body>
        </html>
        '''
        template = Template(html_template)
        html_content = template.render(items=total_order_items, total_price=total_price)
        return HTMLResponse(content=html_content)

    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")
