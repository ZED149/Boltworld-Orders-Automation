

# Created at 6:57 PST 
# Author: Salman Ahmad a.k.a ZED

# this file contains mail_handling class

from email.mime.image import MIMEImage
from email.utils import formataddr
from email.header import Header
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl
from email.mime.text import MIMEText
from dotenv import load_dotenv
from os import getenv

# loading enviourmental variables
load_dotenv(dotenv_path="C:/Users/salma/OneDrive/Desktop/Boltworld Orders Automation/.env")

class MailHandling:
    """Performs basic tasks for an email.
    """
    __s_FROM = getenv('EMAIL_FROM_USERNAME')
    __s_SUBJECT = getenv("EMAIL_FROM_SUBJECT")
    __s_PASSWORD = getenv("EMAIL_FROM_PASSWORD")
    __LOGO_IMAGE_PATH = getenv("EMAIL_LOGO_IMAGE_PATH")
    __host = getenv("EMAIL_HOST")
    __port = int(getenv("EMAIL_PORT"))

    # Constructor
    def __init__(self):
        pass

    # send_email_core()
    def __send_email_core(cls, receiver: str = None, message: str = None, host: str = None,
                   port: int = None, context = None, sender_email: str = None,
                   sender_password: str = None, sender_name: str = None,
                   email_subject: str = None) -> None:
        """Sends an email to the user containing message.

        Args:
            receiver (str, optional): Receiver email. Defaults to None.
            message (str, optional): Message to be conveyed. Must be in html. Defaults to None.
            host (str, optional): host if any. Defaults to None.
            port (int, optional): port of the server to be used. Defaults to None.
            context (_type_, optional): context. Defaults to None.
        """
        msg = MIMEMultipart('related')
        msg['From'] = formataddr((str(Header('ZED', 'utf-8')), cls.__s_FROM))
        msg['To'] = receiver
        # ZED Management Systems
        msg['subject'] = email_subject
        # msg['Subject'] = "Test Mail 55"
        msg.preamble = "This is a multi-part message in MIME format."

        # attaching msgAlternative to the msg
        msgAlternative = MIMEMultipart('alternative')
        msg.attach(msgAlternative)

        # attaching message to the msgAlternative
        msgText = MIMEText(message, 'html')
        msgAlternative.attach(msgText)

        # opening image in binary
        with open(cls.__LOGO_IMAGE_PATH, 'rb') as fb:
            msgImage = MIMEImage(fb.read(), _subtype='png')
        
        del msgImage['Content-Disposition']
        msgImage.add_header('Content-Disposition', 'inline')
        msgImage.add_header('Content-ID', '<image1>')
        msgImage.add_header('X-Attachment-Id', 'image1')  # optional but may help

        msg.attach(msgImage)

        # send email    
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver, msg.as_string())

    # send_email()
    def send_email(self, verbose: bool = False, logger = None, message: str = None, 
                   receiver_email: str = None, sender_email: str = None,
                   sender_password: str = None, sender_name: str = None,
                   email_subject: str = None) -> bool:
        """_summary_

        Args:
            verbose (bool, optional): _description_. Defaults to True.
            message (str, optional): _description_. Defaults to None.
            receiver_email (str, optional): _description_. Defaults to None.
            host (str, optional): _description_. Defaults to None.
            port (str, optional): _description_. Defaults to None.
            context (_type_, optional): _description_. Defaults to None.

        Returns:
            bool: _description_
        """
        if verbose:
            logger.write("-------------------------Send Email, send_email()-------------------------\n")
        # Validations
        if verbose:
            logger.write("Performing validation on the attribute 'message'\n")
        if message:
            # creating secure context for the email
            context = ssl.create_default_context()
            if verbose:
                logger.write(f"Sending email to ({receiver_email})\n")
            self.__send_email_core(receiver=receiver_email, message=message, 
                            host=self.__host, port=self.__port, 
                            context=context, sender_name=sender_name,
                            sender_email=sender_email, sender_password=sender_password,
                            email_subject=email_subject)
            if verbose:
                logger.write("Email successfully sent.\n")
                logger.write("-------------------------send_email(), DONE-------------------------\n")
            return True
        else:
            if verbose:
                logger.write("Attribute 'message' cannot be none.\n")
            logger.write("-------------------------send_email(), DONE-------------------------\n")
            return False
