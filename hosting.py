import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def send_email(site, status_code):
    msg = MIMEText(f"The site {site} returned status code or error {status_code}.")
    msg['Subject'] = f"{site} - Site Check {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    msg['From'] = email_address
    msg['To'] = email_address

    s = smtplib.SMTP(smtp_server, smtp_port)
    s.starttls()
    s.login(email_address, email_password)
    s.send_message(msg)
    s.quit()

# Email settings
smtp_server = 'smtp.example.com'
smtp_port = 587
email_address = 'email@example.com'
email_password = 'password'

with open("sites.txt", "r") as sites:
    for site in sites:        
        site = site.strip()
        try:
            response = requests.get(f'https://{site}')        
            if response.status_code != 200:
                    send_email(site, response.status_code)
        except requests.exceptions.RequestException as err:
            send_email(site, err)