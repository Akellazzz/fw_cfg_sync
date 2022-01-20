import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from os.path import basename


def send_mail(text: str,
              subject: str = "Отчет о синхронизации конфигураций МСЭ",
              send_from: str = "eekosyanenko@vtb.ru",
              send_to: list[str] = ["eekosyanenko@vtb.ru"],
              server: str = "smtp.region.vtb.ru",
              files: list[str] = None) -> None :
    """Compose and send email with provided info and attachments.

    Args:
        text: message
        subject: message title
        send_from: from name
        send_to: to name(s)       
        server: mail server host name
        files: list of file paths to be attached to email
    """
    
    assert isinstance(send_to, list)

    message = MIMEMultipart()
    
    message["From"] = send_from
    message["To"] = ', '.join(send_to)
    message["Subject"] = subject

    html = f"""
    <html>
    <head></head>
    <body>
        <p>{text}
        </p>
    </body>
    </html>
    """
    message.attach(MIMEText(html, "html"))    

    for f in files or []:
        with open(f, "rb") as fil:            
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
            
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        
        message.attach(part)

    msg_full = message.as_string()

    server = smtplib.SMTP(server)
    server.sendmail(send_from, send_to, msg_full)
    server.quit()
    
# send_mail("test", files = ["del.txt"])
