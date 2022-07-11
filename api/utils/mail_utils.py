import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Mail:

    def __init__(self):
        self.port = 465
        self.smtp_server_domain_name = os.environ.get('SMTP_HOST')
        self.sender_mail = os.environ.get('SMTP_EMAIL')
        self.password = os.environ.get('SMTP_PASSWORD')


    def send(self, email, code, codes, host, event):
        
        ssl_context = ssl.create_default_context()
        service = smtplib.SMTP_SSL(
            self.smtp_server_domain_name, self.port, context=ssl_context)
        service.login(self.sender_mail, self.password)
        
        mail = MIMEMultipart('alternative')
        mail['From'] = self.sender_mail
        mail['To'] = email
        
        if event == 'registration':
            mail['Subject'] = 'ProLearn Account Registration'
            html_template = """
                <h1>Pro Learn</h1>

                <p>Hi {0},</p>
                <p>This is your verification link : {3}api/account/verify?code={1}&key={2}.</p>
                <p>Or you can click <a href="{3}api/account/verify?code={1}&key={2}">Here</a> to active your account </p>
                <p><b>Thanks for registration...</b></p>
                <p><b>Let's have fun learning...</b></p>
                """
        elif event == 'verify':
            mail['Subject'] = 'ProLearn Account Verification'
            html_template = """
                <h1>Pro Learn</h1>

                <p>Hi {0},</p>
                <p>Congratulation your account has been verified.</p>
                <p><b>Let's have fun learning...</b></p>
                """
        elif event == 'reset-password':
            mail['Subject'] = 'ProLearn Account Password Reset'
            html_template = """
                <h1>Pro Learn</h1>

                <p>Hi {0},</p>
                <p>We received a request to reset your password, here is your new password.</p>
                <p><b>{1}</b></p>
                <p>Please login and change password immediately.</p>
                <p><b>Let's have fun learning...</b></p>
                """
        elif event == 'send-code':
            mail['Subject'] = 'ProLearn Account Request Verification Code'
            html_template = """
                <h1>Pro Learn</h1>

                <p>Hi {0},</p>
                <p>We received a verification code request, here is your code.</p>
                <p><b>{1}</b></p>
                <p>Please input immediately.</p>
                <p><b>Let's have fun learning...</b></p>
                """
                
        html_content = MIMEText(
            html_template.format(email.split("@")[0], code, codes, host), 'html')

        mail.attach(html_content)

        service.sendmail(self.sender_mail, email, mail.as_string())

        service.quit()
