import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
        <p>Hussein Reda</p>
    </body>
    </html>
    '''

    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_address
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
        <p>Hussein Reda</p>
    </body>
    </html>
    '''
    
    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_address
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