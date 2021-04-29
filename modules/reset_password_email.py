#!/usr/bin/env python3

# import necessary modules
import smtplib
from email.message import EmailMessage

# send the reset password email
def send(email, url):  
    message=EmailMessage()
    message["Subject"]="E-shopping reset password"
    message["From"]="Your e-mail username"
    message["To"]=email
    # Add the html version.  
    message.add_alternative("""
    <!DOCTYPE html>
    <html lang="en-us">
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />                                        
        </head>
        <body>
            <p>Click the following hyperlink to reset your password!</p>
            <a href="%s">%s</a>
        </body>
    </html>
    """%(url, url), subtype="html")
    # Send the message via SMTP server.
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("Your e-mail username", "Your e-mail password")
        server.send_message(message)
