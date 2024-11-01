'''
This module sends emails with attachments to the participants
Reference - https://developers.google.com/gmail/api/quickstart/python

In order to run this module, you need to enable Gmail API and download client_secrets.json file
'''

from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import mimetypes
import os
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import base64
import cv2


# If modifying these scopes, delete the file token.json.
# We are using Gmail API to send emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def aunthentication():
    creds = None
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        # Load the credentials from the file
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        # Refresh the token if it has expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # If there are no valid credentials available, let the user log in.
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def prepare_and_send_email(sender, recipient, subject, message_text, im0: bytes):
    """Prepares and send email with attachment to the participants 

    Args:
        sender: Email address of the sender.
        recipient: Email address of the receiver.
        subject: The subject of the email message.
        message_text: The text of the email message.
        im0: The image to be attached 
    
    Returns:
        None
    """
    # Get credentials 
    creds = aunthentication()

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)

        #create message using a custo, function create_message()
        msg = create_message(sender, recipient, subject, message_text, im0)
        # send the message using a custom function send_message()
        send_message(service, 'me', msg) #here 'me' is the user_id of the authenticated user

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


def create_message(sender, to, subject, message_text, img_file):
    """Create a message for an email.

    Args:
        sender: Email address of the sender.
        to: Email address of the receiver.
        subject: The subject of the email message.
        message_text: The text of the email message.
        img_file: The image to be attached

    Returns:
        An object containing a base64url encoded email object.
    """
    # create a multipart email message with attachment
    message = MIMEMultipart()

    message['from'] = sender
    message['to'] = to
    message['subject'] = subject

    #create a directory to store the images that are attached to the email
    base_loc = 'static/violations/'
    location = 'ABESIT'
    
    #get current date and time
    current_date_time = time.time()
    formatted_date_time = time.strftime("%H:%M:%S_%d-%m-%Y", time.localtime(current_date_time))
    
    #if base_loc doesn't exist, create it
    if not os.path.exists(base_loc):
        os.makedirs(base_loc)
    
    file_name = base_loc+'violation_'+location + '_' + formatted_date_time + '.jpg'

    #convert img_file into jpeg format and save it in the file_name
    cv2.imencode('.jpg', img_file)[1].tofile(file_name)

    msg = MIMEText(message_text)
    message.attach(msg)

    content_type, encoding = mimetypes.guess_type(file_name)
    main_type, sub_type = content_type.split('/', 1)

    print(f'Attachment main_type = {main_type}, subtype= {sub_type}, and encoding = {encoding}')

    # code to attach text, image, pdf and other files
    # if attachment is a text file
    if main_type == 'text':
        fp = open(file_name, 'rb')
        msg = MIMEText(fp.read(), _subtype=sub_type)
        fp.close()
    # if attachment is an image file    
    elif main_type == 'image':
        fp = open(file_name, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    # if attachment is a pdf file, then we need to set the main_type to application and sub_type to octet-stream
    elif main_type == 'application' and sub_type=='pdf' and encoding == None: #Reference - https://coderzcolumn.com/tutorials/python/mimetypes-guide-to-determine-mime-type-of-file
        print("INSIDE PDF")
        main_type = 'application'
        sub_type = 'octet-stream'
        fp = open(file_name, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        encoders.encode_base64(msg)
        fp.close()
    #if attachment is anything else
    else:
        fp = open(file_name, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()
    
    filename = os.path.basename(file_name)
    # add attachment to the message header
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)

    #convert the message into a string
    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}


def send_message(service, user_id, message):
    """Send an email message.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        message: Message to be sent.

    Returns:
        Sent Message.
    """
    try:
        message = (service.users().messages().send(userId=user_id, body=message)
                    .execute())
        print('Message Id: %s' % message['id'])
        return message
    except HttpError as error:
        print('An error occurred: %s' % error)


if __name__ == '__main__':
    
    # Uncomment the following lines to run the code locally
    # set sender and recipient accordingly
    # sender must be a gmail account using which you have enabled the gmail API
    '''prepare_and_send_email(sender='prakharsingh2018@gmail.com', 
                           recipient='itews20003@glbitm.ac.in',
                           subject= 'Greeting from Prakhar Singh', 
                           message_text= 'Hello, this is a test email from Prakhar's side',
                           im0= cv2.imread('test.jpg'))'''
    pass
    
    
