import smtplib
from flask_mail import sanitize_addresses
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import FROM_USER, EXMAIL_PASSWORD


def send_mail(msg):
    send_to = list(sanitize_addresses(msg.send_to))
    part = MIMEText(msg.html, "html")
    mp = MIMEMultipart("alternative")
    mp["Subject"] = msg.subject
    mp["From"] = FROM_USER
    mp["To"] = ",".join(send_to)
    mp.attach(part)

    s = smtplib.SMTP("smtp.qq.com", port=587)
    s.set_debuglevel(True)
    s.starttls()
    s.login(FROM_USER, EXMAIL_PASSWORD)
    s.sendmail(FROM_USER, send_to, mp.as_bytes())
    s.quit()
