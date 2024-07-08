# Online Market Shop

This repository contains a set of APIs for managing an online market shop, including user flow, product flow, cart management, and order processing with two types of payments. 
Additionally, a log model is included to view API logs in the portal. The project is built using FastAPI and MongoDB.

## Getting Started



1. Install the dependencies:


    pip install -r requirements.txt
    

2. Run the application:

 
    uvicorn main:app --reload







3. To start testing the APIs, use the Postman collection URL available in `config.py`.

### Configuration

- The application configuration, including database settings and secret keys, are available in `config.py`.

## Testing

1. Start by registering a user as a seller or a buyer, then you will receive an email with a link to verify your email. The link should be run on the same machine where you are running the project.

2. Alternatively, you can use the following login credentials:

   **For Seller:**
   - Email: hussein.reda@allegiancetek.com
   - Password: P@ssw0rd

   **For Buyer:**
   - Email: husseinreda1472002@gmail.com
   - Password: P@ssw0rd

and happy testing you will find all the apis there



## API Endpoints

### User Flow

#### Register User
- **Endpoint:** `/register`
- **Method:** `POST`
- **Description:** Registers a new user (buyer or seller) and sends a verification email.
- **Request Body:**
  ```json
  {
      "email": "string",
      "password": "string",
      "is_seller": "boolean"
  }
  ```
- **Response:**
  ```json
  {
      "message": "Welcome [email]! We've sent a verification link, please check your mail."
  }
  ```

#### Verify Email
- **Endpoint:** `/verify-email`
- **Method:** `GET`
- **Description:** Verifies the user's email using the token sent in the email.
- **Request Params:**
  ```json
  {
      "token": "string"
  }
  ```
- **Response:** HTML page confirming email verification.

#### Login
- **Endpoint:** `/login`
- **Method:** `POST`
- **Description:** Authenticates the user and provides an access token.
- **Request Body:**
  ```json
  {
      "email": "string",
      "password": "string"
  }
  ```
- **Response:**
  ```json
  {
      "access_token": "string",
      "token_type": "bearer"
  }
  ```

#### Forgot Password
- **Endpoint:** `/forgot-password`
- **Method:** `POST`
- **Description:** Sends a password reset link to the user's email.
- **Request Body:**
  ```json
  {
      "email": "string"
  }
  ```
- **Response:**
  ```json
  {
      "message": "Password reset link sent to your email"
  }
  ```

#### Reset Password
- **Endpoint:** `/reset-password`
- **Method:** `POST`
- **Description:** Resets the user's password using the token sent in the email.
- **Request Body:**
  ```json
  {
      "token": "string",
      "new_password": "string"
  }
  ```
- **Response:** HTML page confirming password reset.

### Product Flow

#### Create Product
- **Endpoint:** `/products/create`
- **Method:** `POST`
- **Description:** Creates a new product listing by the seller.
- **Request Body:**
  ```json
  {
      "name": "string",
      "description": "string",
      "price": "float",
      "quantity": "integer",
      "files": ["UploadFile"]
  }
  ```
- **Response:**
  ```json
  {
      "message": "Product Created Successfully!",
      "product": {
          "id": "string",
          "seller_id": "string",
          "name": "string",
          "description": "string",
          "price": "float",
          "quantity": "integer",
          "isAvailable": "boolean",
          "images": ["string"],
          "created_at": "datetime"
      }
  }
  ```

#### Update Product
- **Endpoint:** `/products/update/{product_id}`
- **Method:** `PUT`
- **Description:** Updates an existing product listing by the seller.
- **Request Body:**
  ```json
  {
      "name": "string",
      "description": "string",
      "price": "float",
      "quantity": "integer",
      "files": ["UploadFile"]
  }
  ```
- **Response:**
  ```json
  {
      "message": "Product updated successfully",
      "product": {
          "id": "string",
          "name": "string",
          "description": "string",
          "price": "float",
          "quantity": "integer",
          "isAvailable": "boolean",
          "images": ["string"],
          "created_at": "datetime"
      }
  }
  ```

#### Delete Product
- **Endpoint:** `/products/delete/{product_id}`
- **Method:** `DELETE`
- **Description:** Soft deletes a product listing by the seller.
- **Response:**
  ```json
  {
      "message": "Product moved to bin successfully. You can restore it within 30 days."
  }
  ```

#### Get All Products
- **Endpoint:** `/products/GetAll`
- **Method:** `GET`
- **Description:** Retrieves all product listings with optional search, pagination, and sorting.
- **Request Params:**
  ```json
  {
      "search": "string",
      "page": "integer",
      "limit": "integer",
      "sort_by_price": "boolean"
  }
  ```
- **Response:**
  ```json
  [
      {
          "id": "string",
          "seller_email": "string",
          "name": "string",
          "description": "string",
          "price": "float",
          "quantity": "integer",
          "isAvailable": "boolean",
          "images": ["string"],
          "created_at": "datetime"
      }
  ]
  ```

#### Get Product by ID
- **Endpoint:** `/products/GetProduct/{product_id}`
- **Method:** `GET`
- **Description:** Retrieves a single product listing by ID.
- **Response:**
  ```json
  {
      "id": "string",
      "seller_email": "string",
      "name": "string",
      "description": "string",
      "price": "float",
      "quantity": "integer",
      "isAvailable": "boolean",
      "images": ["string"],
      "created_at": "datetime"
  }
  ```

#### Get Seller's Products
- **Endpoint:** `/products/getmineproducts`
- **Method:** `GET`
- **Description:** Retrieves all product listings by the authenticated seller.
- **Response:**
  ```json
  [
      {
          "id": "string",
          "name": "string",
          "description": "string",
          "price": "float",
          "quantity": "integer",
          "isAvailable": "boolean",
          "images": ["string"],
          "created_at": "datetime"
      }
  ]
  ```

#### Get Deleted Products
- **Endpoint:** `/products/getDeleted`
- **Method:** `GET`
- **Description:** Retrieves all deleted product listings by the authenticated seller.
- **Response:**
  ```json
  [
      {
          "id": "string",
          "name": "string",
          "description": "string",
          "price": "float",
          "quantity": "integer",
          "isAvailable": "boolean",
          "images": ["string"],
          "created_at": "datetime"
      }
  ]
  ```

#### Restore Deleted Product
- **Endpoint:** `/products/restore/{product_id}`
- **Method:** `PUT`
- **Description:** Restores a deleted product listing by the seller.
- **Response:**
  ```json
  {
      "message": "Product restored successfully."
  }
  ```

### Cart Management

#### Add to Cart
- **Endpoint:** `/cart/create`
- **Method:** `POST`
- **Description:** Adds a product to the user's shopping cart. Decreases the product quantity in the inventory.
- **Request Body:**
  ```json
  {
      "product_id": "string",
      "quantity": "integer"
  }
  ```
- **Response:**
  ```json
  {
      "message": "Product added to cart successfully"
  }
  ```

#### Get Cart Items
- **Endpoint:** `/cart/getmine`
- **Method:** `GET`
- **Description:** Retrieves all products in the user's shopping cart.
- **Response:**
  ```json
  [
      {
          "product_id": "string",
          "product_name": "string",
          "seller_email": "string",
          "quantity": "integer",
          "created_at": "datetime",
          "updated_at": "datetime"
      }
  ]
  ```

#### Update Cart
- **Endpoint:** `/cart/editCart`
- **Method:** `PUT`
- **Description:** Updates the quantity of a product in the user's shopping cart.
- **Request Body:**
  ```json
  {
      "product_id": "string",
      "quantity": "integer"
  }
  ```
- **Response:**
  ```json
  {
      "message": "Cart updated successfully"
  }
  ```

#### Remove from Cart
- **Endpoint:** `/cart/removeCart/{product_id}`
- **Method:** `DELETE`
- **Description:** Removes a product from the user's shopping cart and restores the quantity to the inventory.
- **Response:**
  ```json
  {
      "message": "Product removed from cart successfully"
  }
  ```

### Order Management

#### Create Payment
- **Endpoint:** `/orders/create-payment`
- **Method:** `POST`
- **Description:** Creates a payment for the items in the user's cart using either `payment_intent` or `payment_link`.
- **Request Body:**
  ```json
  {
      "payment_method": "string"
  }
  ```
- **Response:**
  ```json
  {
      "paymentUrl": "string"
  }
  ```

#### Confirm Payment
- **Endpoint:** `/orders/confirm-payment`
- **Method:** `GET`
- **Description:** Confirms the payment and updates the order status to "confirmed".
- **Request Params:**
  ```json
  {
      "payment_id": "string"
  }
  ```
- **Response:** HTML page confirming the order.

#### Get My Orders
- **Endpoint:** `/orders/getmyOrders`
- **Method:** `GET`
- **Description:** Retrieves all orders for the authenticated user (buyer or seller).
- **Response:**
  ```json
  [


      {
          "order_id": "string",
          "user_id": "string",
          "total_price": "float",
          "status": "string",
          "created_at": "datetime",
          "updated_at": "datetime",
          "buyer email": "string",
          "products": [
              {
                  "product_id": "string",
                  "product_name": "string",
                  "quantity": "integer",
                  "price": "float"
              }
          ]
      }
  ]
  ```

#### Get Order by ID
- **Endpoint:** `/orders/getOrderById/{order_id}`
- **Method:** `GET`
- **Description:** Retrieves a single order by ID for the authenticated user (buyer or seller).
- **Response:**
  ```json
  {
      "order_id": "string",
      "user_id": "string",
      "total_price": "float",
      "status": "string",
      "created_at": "datetime",
      "updated_at": "datetime",
      "buyer email": "string",
      "products": [
          {
              "product_id": "string",
              "product_name": "string",
              "quantity": "integer",
              "price": "float"
          }
      ]
  }
  ```

#### Set Order Status to Delivered
- **Endpoint:** `/orders/setOrderStatusToDelivered/{order_id}`
- **Method:** `PUT`
- **Description:** Updates the order status to "delivered" for the authenticated seller.
- **Response:**
  ```json
  {
      "message": "Order status updated to delivered and email sent to buyer"
  }
  ```

#### Serve Payment Form
- **Endpoint:** `/orders/payment_form`
- **Method:** `GET`
- **Description:** Serves the payment form for the provided client secret and success URL.
- **Request Params:**
  ```json
  {
      "client_secret": "string",
      "success_url": "string"
  }
  ```
- **Response:** HTML form for payment.

## Logging

- All actions, including successful operations and errors, are logged in the `logs` collection in MongoDB. This allows you to view API logs in the portal for monitoring and debugging purposes.

### Export Logs

- **Endpoint:** `/auth/export-logs`
- **Description:** Exports the logs as a CSV file.
- **Response:** Returns a CSV file containing the logs.