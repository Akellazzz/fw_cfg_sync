from zipfile import ZipFile

import datetime
import os
import smtplib
from email.mime.text import MIMEText
from contextlib import closing
from sys import argv, exit

os.chdir(app.config["UPLOAD_FOLDER"])
with ZipFile("result.zip", "w") as zipObj:
    zipObj.write("report.csv")
    zipObj.write(res_filename)


# EMAIL
HOST = "smtp.vtb.ru"
FROM = "eekosyanenko@vtb.ru"
SUBJECT = "Результат синхронизации конфигураций МСЭ"
ADMINS = "eekosyanenko@vtb.ru"


def alert(alert_text, to=ADMINS):

    html = f"""
    <html>
    <head></head>
    <body>
        <p>{alert_text}
        </p>
    </body>
    </html>
    """
    message = MIMEText(html, "html")
    message["From"] = FROM
    # message["To"] = TO
    message["To"] = to
    message["Subject"] = SUBJECT

    msg_full = message.as_string()

    server = smtplib.SMTP(HOST)
    # server.sendmail(FROM, [TO], msg_full)
    server.sendmail(FROM, [to], msg_full)
    server.quit()


alert_text += host + "<br>" + show_result.replace("\n", "<br>") + "<br><br>"
# Общая рассылка:
alert(alert_text, to=LIST)

# Расширенная рассылка админам:
adm_alert_text = alert_text + f"<br>Будут выполнены команды: <br>"
alert(adm_alert_text, to=LIST)