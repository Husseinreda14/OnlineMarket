
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from jinja2 import Template
import config

def send_verification_email(email: str, token: str):
    sender_address = config.EMAIL
    sender_password = config.PASSWORD
    receiver_address = email

    mail_content = f'''
    <html>
    <body>
        <h2>Welcome to Our Service!</h2>
        <p>Hello,</p>
        <p>Thank you for registering with us. To complete your registration, please click the link below to verify your email address:</p>
        <p><a href="{config.API_URL}/auth/verify-email?token={token}">Verify Email Address</a></p>
        <p>If you did not register for our service, please ignore this email.</p>
         <p>Note this Link is one time access!</p>
        <br>
        <p>Best regards,</p>
        <p>E-Market Shop</p>
    </body>
    </html>
    '''

    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = f'MarketShop <{sender_address}>'
    message['To'] = receiver_address
    message['Subject'] = 'Please verify your email address'
    message.attach(MIMEText(mail_content, 'html'))

    # Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
    session.starttls()  # enable security
    session.login(sender_address, sender_password)  # login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    print('Mail Sent')


def send_reset_password_email(email: str, token: str):
    sender_address = config.EMAIL
    sender_password = config.PASSWORD
    receiver_address = email

    reset_url = f"{config.API_URL}/auth/reset-password?token={token}"
    
    mail_content = f'''
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>Hello,</p>
        <p>We received a request to reset your password. Please click the link below to reset your password:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>If you did not request a password reset, please ignore this email.</p>
        <p>Note this Link is one time access!</p>
        <br>
        <p>Best regards,</p>
        <p>E-Market Shop</p>
    </body>
    </html>
    '''
    
    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = f'MarketShop <{sender_address}>'
    message['To'] = receiver_address
    message['Subject'] = 'Reset Your Password'
    message.attach(MIMEText(mail_content, 'html'))

    # Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
    session.starttls()  # enable security
    session.login(sender_address, sender_password)  # login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    print('Mail Sent')
    
    
    
def send_order_confirmation_email(email: str, items: List[dict], total_price: float):
    sender_address = config.EMAIL
    sender_password = config.PASSWORD
    receiver_address = email

    mail_content = f'''
    <html>
    <body>
        <h2>Thank you for your order!</h2>
        <p>Your order has been confirmed. Here are the details:</p>
        <ul>
        {''.join([f"<li>{item['quantity']} x {item['product_name']} - ${item['product_price']}</li>" for item in items])}
        </ul>
        <p>Total: ${total_price}</p>
        <br>
        <p>Best regards,</p>
        <p>E-Market Shop</p>
    </body>
    </html>
    '''

    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = f'MarketShop <{sender_address}>'
    message['To'] = receiver_address
    message['Subject'] = 'Order Confirmation'
    message.attach(MIMEText(mail_content, 'html'))

    # Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
    session.starttls()
    session.login(sender_address, sender_password)
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    print('Order confirmation email sent')
    
      
def send_seller_notification_email(email: str,buyer_email ,items: List[dict], total_price: float):
    sender_address = config.EMAIL
    sender_password = config.PASSWORD
    receiver_address = email

    mail_content = f'''
    <html>
    <body>
        <h2>New Order Received!</h2>
        <p>A new order has been placed from user {buyer_email}. Here are the details:</p>
        <ul>
        {''.join([f"<li>{item['quantity']} x {item['product_name']} - ${item['product_price']}</li>" for item in items])}
        </ul>
        <p>Total: ${total_price}</p>
        <br>
        <p>Best regards,</p>
        <p>Your MarketShop Team</p>
    </body>
    </html>
    '''

    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = f'MarketShop <{sender_address}>'
    message['To'] = receiver_address
    message['Subject'] = 'New Order Notification'
    message.attach(MIMEText(mail_content, 'html'))

    # Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
    session.starttls()
    session.login(sender_address, sender_password)
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    print('Seller notification email sent')


def send_delivery_notification_email(to_email: str, seller_email: str):
    sender_address = config.EMAIL
    sender_password = config.PASSWORD
    receiver_address = to_email

    mail_content = f'''
    <html>
    <body>
        <h2>Your Order Has Been Processed</h2>
        <p>Dear Customer,</p>
        <p>Your order has been processed by Aramex. You should receive a call or SMS from them within 3 business days.</p>
        <p>Thank you for shopping with us!</p>
        <br>
        <p>Best regards,</p>
       <p>E-Market Shop</p>
    </body>
    </html>
    '''

    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = f'MarketShop <{sender_address}>'
    message['To'] = receiver_address
    message['Subject'] = f'On Behalf of {seller_email}'
    message.attach(MIMEText(mail_content, 'html'))

    # Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
    session.starttls()  # enable security
    session.login(sender_address, sender_password)  # login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    print('Delivery notification email sent')
    
    
def get_payment_form_html(client_secret: str, success_url: str, stripe_public_key: str) -> str:
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Complete Your Payment</title>
        <script src="https://js.stripe.com/v3/"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f7f7f7;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .container {
                background-color: #fff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                width: 100%;
                max-width: 400px;
                text-align: center;
            }
            h1 {
                color: #333;
            }
            p {
                color: #666;
            }
            #card-element {
                border: 1px solid #ccc;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Complete Your Payment</h1>
            <p>Please enter your payment details below:</p>
            <form id="payment-form">
                <div id="card-element">
                    <!-- A Stripe Element will be inserted here. -->
                </div>
                <button type="submit">Pay</button>
            </form>
        </div>
        <script>
            var stripe = Stripe('{{ stripe_public_key }}');
            var elements = stripe.elements();
            var card = elements.create('card');
            card.mount('#card-element');

            var form = document.getElementById('payment-form');
            form.addEventListener('submit', function(event) {
                event.preventDefault();
                stripe.confirmCardPayment('{{ client_secret }}', {
                    payment_method: {
                        card: card,
                        billing_details: {
                            name: 'Jenny Rosen'
                        }
                    }
                }).then(function(result) {
                    if (result.error) {
  alert(result.error.message); 
                    } else {
                        if (result.paymentIntent.status === 'succeeded') {
                            window.location.href = '{{ success_url }}';
                        }
                    }
                });
            });
        </script>
    </body>
    </html>
    '''
    template = Template(html_template)
    return template.render(client_secret=client_secret, stripe_public_key=stripe_public_key, success_url=success_url)
