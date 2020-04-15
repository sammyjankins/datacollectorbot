import smtplib
from datetime import date
from email.header import Header
from email.mime.text import MIMEText

import db_operator
import private_constants


def send_data(user_id):
    user = db_operator.get_user(user_id)
    try:
        vars_dict = db_operator.get_last_data(user_id)
        vars_dict.update({'дата': date.today().strftime('%d.%m.%Y')})
    except Exception:
        vars_dict = None
    for mail_to in user['mail_to'].split():
        s = smtplib.SMTP('smtp.gmail.com', port=587)
        s.set_debuglevel(1)
        if vars_dict:
            msg = MIMEText(user['mail_text'].format(**vars_dict), 'plain', 'utf-8')
        else:
            msg = MIMEText(user['mail_text'], 'plain', 'utf-8')
        msg['Subject'] = Header(user['mail_theme'])
        msg['From'] = private_constants.email_from
        try:
            s.starttls()
            s.login(private_constants.email_from, private_constants.mailpass)
            msg['To'] = mail_to
            print(msg['To'])
            s.sendmail(msg['From'], msg['To'], msg.as_string())
        finally:
            s.quit()
