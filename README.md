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
