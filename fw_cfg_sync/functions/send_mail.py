import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from os.path import basename
from loguru import logger


def send_mail(text: str,
              subject: str,
              send_from: str,
              send_to: list[str],
              server: str,
              enabled: bool,
              files: list[str] = None) -> None :
    """Compose and send email with provided info and attachments.

    Args:
        text: message
        subject: message title
        send_from: from name
        send_to: to name(s)       
        server: mail server host name
        enabled: True/False
        files: list of file paths to be attached to email
    """

    if not enabled:
        logger.debug(f"Mail is disabled by app config but send_mail is called with text: {text}")

        return

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
    try:
        server = smtplib.SMTP(server)

        server.sendmail(send_from, send_to, msg_full)
        server.quit()
    except Exception as e:
        logger.error('Unable to send message')
        logger.error(f"Exception: {e}")
        return
    
# send_mail("test", files = ["del.txt"])
