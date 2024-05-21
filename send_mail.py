import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

subject = "Global Review"
body = "This is global review"
csv_file_name = "./article_summary.csv"

load_dotenv()
to_email = os.getenv('TO_EMAIL')
from_email = os.getenv('FROM_EMAIL')
mailtrap_user = os.getenv('MAILTRAP_USER')
mailtrap_password = os.getenv('MAILTRAP_PASSWORD')
mailtrap_server = os.getenv('MAILTRAP_SERVER')
mail_port = os.getenv('MAIL_PORT')


sender = f"Global Review <{from_email}>"
receiver = f"<{to_email}>"

# Create a multipart message
msg = MIMEMultipart()
msg['From'] = sender
msg['To'] = receiver
msg['Subject'] = subject

# Add body to email
msg.attach(MIMEText(body, 'plain'))

# Open the file to be sent
with open(csv_file_name, "rb") as attachment:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())

# Encode file in ASCII characters to send by email    
encoders.encode_base64(part)

# Add header as key/value pair to attachment part
part.add_header(
    "Content-Disposition",
    f"attachment; filename= {os.path.basename(csv_file_name)}",
)

# Attach the file
msg.attach(part)


with smtplib.SMTP(mailtrap_server, mail_port) as server:
    server.starttls()
    server.login(mailtrap_user, mailtrap_password)
    server.sendmail(sender, receiver, msg.as_string())