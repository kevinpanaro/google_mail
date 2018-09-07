from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import googleapiclient.errors
import logging
import sys
import os.path
import time
import json
import re


def init_logging(loglevel, logdir, logroot):
    """
    Initializes logging
    """

    logger = logging.getLogger('')
    logger.setLevel(loglevel)

    if logdir != None:
        logfile = logroot + '.' + time.strftime("%Y%m%d-%H%M%S", time.gmtime(time.time())) + '.log'
        logpath = os.path.join(logdir, logfile)

        ch = logging.FileHandler(logpath)
        ch.setLevel(loglevel)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%m/%d/%Y %H:%M:%S')   
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    else:
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(loglevel)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%m/%d/%Y %H:%M:%S')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

# If modifying these scopes, delete the file token.json.
def service_user():
    """
    Basic object to interact with google api
    """
    SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('gmail', 'v1', http=creds.authorize(Http()))
    return(service)

def get_message_ids(max_results: int = 5, labelIds="INBOX", service: object = service_user()):
    """
    These id's can be used to access the message

    :param max_results: the number of returned message_ids
    :param labelIds: the label to look in (default: INBOX)
    :param service: service object
    :return: list of message_ids only
    """
    messages = service.users().messages().list(userId="me", labelIds=labelIds, maxResults=max_results).execute()
    message_ids = [message['id'] for message in messages['messages']]
    logging.debug(f"found {len(message_ids)} message_ids")
    return(message_ids)

def get_sending_address(message_ids: list = None, service: object = service_user()):
    """
    Gets the address's of the requested ids (used for get_accounts)

    :param message_ids: message ids to for sending address
    :param service: service object
    :return: list of sending addresses
    sending_address = []
    if not isinstance(message_ids, list):
        message_ids = get_message_ids(service=service)
    for m_id in message_ids:
        message = service.users().messages().get(userId="me", id=m_id).execute()
        logging.debug(json.dumps(message, indent=4))
        message_headers = message['payload']['headers']
        for header in message_headers:
            if header['name'] == "To":
                data = {'id': m_id, "sending_address" : header['value'].lower()}
                sending_address.append(data)
        logging.debug("\n")
    return(sending_address)

def get_accounts(message_ids: list = None, service: object = service_user()):
    """
    This parses addresses and decides if they
    are valid to be categorized

    :param message_ids: valid ids to get account names for
    :param service: service object
    :return: accounts with address (debugging), id, and name
    """
    accounts = []
    regex =  re.compile("(?<=panaro\.kevin\+).+(?=@gmail\.com)")

    sending_address = get_sending_address(message_ids=message_ids, service=service)
    for item in sending_address:
        match = regex.search(item['sending_address'])
        if match:
            logging.debug(f"match found {match.group()}")
            item['mbox'] = match.group()
            accounts.append(item)
    return(accounts)

def get_labels(service: object = service_user()):
    """
    Gets the labels (mailboxes)

    :param service: service object 
    :return:  label dict
    """
    labels = service.users().labels().list(userId="me").execute()['labels']
    return(labels)

def create_mailbox(mbox: str, parent: str = None, service: object = service_user()):
    """
    creates a mailbox.

    use with care, label id's are not limited though.

    :param mbox: the mailbox to check if exists
    :param parent: the parent mailbox of mbox
    :param service: service object
    :return: None
    """
    if parent:
        mbox = '/'.join((parent, mbox))

    body = {"name": mbox}

    label = service.users().labels().create(userId="me", body=body).execute()
    logging.debug(f"mailbox {mbox} with label id {label['id']}")


def check_mailbox(mbox: str, parent: str = None, service: object = service_user()):
    """
    Checks if a mailbox exists (unused)

    :param mbox: the mailbox to check if exists
    :param parent: the parent mailbox of mbox
    :param service: service object
    :return: bool
    """
    if parent:
        mbox = '/'.join((parent, mbox))

    try:
        labels = get_labels(service)
        for label in labels:
            if label['name'] == mbox:
                return(True)
    except:
        print('An error occurred:')
    return(False)

def get_mailbox(mbox: str, parent: str = None, service: object = service_user()):
    """
    Get the mailbox label infomation

    :param mbox: mailbox name from email
    :param parent: parent label name
    :param service: service object to interact with google api
    :return: mailbox label
    if parent:
        mailbox = '/'.join((parent, mbox))

    labels = get_labels(service)
    for label in labels:
        if label['name'] == mailbox:
            return(label)
    else:
        logging.debug(f"mailbox {mbox} doesn't exist, and is being created")
        create_mailbox(mbox=mbox, parent=parent, service=service)
        return(get_mailbox(mbox=mbox, parent=parent, service=service))

def move_mail(max_results: int = 5,
              parent: str = None,
              service: object = service_user(),
              dry_run: bool = True,
              remove_from_inbox: bool = False):
    """
    Move mail to corresponding label

    :param max_results: number of emails to get from most recent
    :param parent: a parent label to move the emails to
    :param service: get access to google api service
    :param dry_run: don't move anything (will create folders tho)
    :param remove_from_inbox: removes the items from the inbox
    :returns: nothing
    """

    message_ids = get_message_ids(max_results=max_results, service=service)

    accounts = get_accounts(message_ids=message_ids, service=service)
    if remove_from_inbox:
        remove = ["INBOX"]
    else:
        remove = []

    for account in accounts:

        mailbox = get_mailbox(mbox=account['mbox'], parent=parent)

        body = {"addLabelIds": [mailbox["id"]],
                "removeLabelIds": remove}

        if not dry_run:
            logging.info(f"moving {account['sending_address']} to {mailbox['name']}")
            service.users().messages().modify(userId="me", id=account["id"], body=body).execute()
        else:
            logging.debug(f"would move {account['mbox']} to {mailbox['name']}")

    

if __name__ == '__main__':

    init_logging(loglevel=logging.INFO, logdir=None, logroot=None)
    
    move_mail(max_results=3, parent="Accounts", dry_run=False)