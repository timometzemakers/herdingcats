from __future__ import print_function

import httplib2
import os
import email
from email.message import Message
import base64

from apiclient import discovery
import oauth2client
from oauth2client import client

import googlemaps


# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Herding Cats'

RELEVANT_MESSAGE_GMAIL_FILTER = 'newer_than:3m label:jazzetcie to:timo@jazzetcie.com subject:"Demande de devis sur jazzetcie.com" -subject:"Re:"'
HOME_ADDRESS = "17 rue Michel Montaigne, Talence, France"
GOOGLE_DIRECTIONS_KEY = "AIzaSyAzt0H4L5dylyv1Fhx2FXf8IeZ-dppo7HY"


class GoogleServices:

    def __init__(self):
        self.credentials = self.get_credentials()
        self.gmaps = googlemaps.Client(key=GOOGLE_DIRECTIONS_KEY)
    
    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'herding_cats_gmail_credentials.json')

        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()

        flags = None
        
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def get_relevant_messages_from_gmail(self):
        """Connect to Gmail and return a list of unread relevant messages.

Returns a generator of (<message id string>, <email.message.Message instance>).
        """
        http = self.credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)

        gmail_query_result = service.users().messages().list(userId='me', q=RELEVANT_MESSAGE_GMAIL_FILTER).execute()

## gmail_query_result is an object of the form:
##
##    {
##    "nextPageToken": "A String", # Token to retrieve the next page of results in the list.
##    "resultSizeEstimate": 42, # Estimated total number of results.
##    "messages": [ # List of messages.
##      { # An email message.
##        "internalDate": "A String", # The internal message creation timestamp (epoch ms), which determines ordering in the inbox. For normal SMTP-received email, this represents the time the message was originally accepted by Google, which is more reliable than the Date header. However, for API-migrated mail, it can be configured by client to be based on the Date header.
##        "historyId": "A String", # The ID of the last history record that modified this message.
##        "payload": { # A single MIME message part. # The parsed email structure in the message parts.
##          "body": { # The body of a single MIME message part. # The message part body for this part, which may be empty for container MIME message parts.
##            "data": "A String", # The body data of a MIME message part. May be empty for MIME container types that have no message body or when the body data is sent as a separate attachment. An attachment ID is present if the body data is contained in a separate attachment.
##            "attachmentId": "A String", # When present, contains the ID of an external attachment that can be retrieved in a separate messages.attachments.get request. When not present, the entire content of the message part body is contained in the data field.
##            "size": 42, # Total number of bytes in the body of the message part.
##          },
##          "mimeType": "A String", # The MIME type of the message part.
##          "partId": "A String", # The immutable ID of the message part.
##          "filename": "A String", # The filename of the attachment. Only present if this message part represents an attachment.
##          "headers": [ # List of headers on this message part. For the top-level message part, representing the entire message payload, it will contain the standard RFC 2822 email headers such as To, From, and Subject.
##            {
##              "name": "A String", # The name of the header before the : separator. For example, To.
##              "value": "A String", # The value of the header after the : separator. For example, someuser@example.com.
##            },
##          ],
##          "parts": [ # The child MIME message parts of this part. This only applies to container MIME message parts, for example multipart/*. For non- container MIME message part types, such as text/plain, this field is empty. For more information, see RFC 1521.
##            # Object with schema name: MessagePart
##          ],
##        },
##        "snippet": "A String", # A short part of the message text.
##        "raw": "A String", # The entire email message in an RFC 2822 formatted and base64url encoded string. Returned in messages.get and drafts.get responses when the format=RAW parameter is supplied.
##        "sizeEstimate": 42, # Estimated size in bytes of the message.
##        "threadId": "A String", # The ID of the thread the message belongs to. To add a message or draft to a thread, the following criteria must be met:
##            # - The requested threadId must be specified on the Message or Draft.Message you supply with your request.
##            # - The References and In-Reply-To headers must be set in compliance with the RFC 2822 standard.
##            # - The Subject headers must match.
##        "labelIds": [ # List of IDs of labels applied to this message.
##          "A String",
##        ],
##        "id": "A String", # The immutable ID of the message.
##      },
##    ],
##  }

        try:
            gmail_query_result_message_ids = [m['id'] for m in gmail_query_result['messages']]
        except KeyError:
            gmail_query_result_message_ids = []
            
        
        gmail_query_result_message_objects = ((i, service.users().messages().get(userId='me', format='raw', id=i).execute())
                                               for i in gmail_query_result_message_ids)

## gmail_query_result_message_objects is a list of the following objects:
##
##    { # An email message.
##    "internalDate": "A String", # The internal message creation timestamp (epoch ms), which determines ordering in the inbox. For normal SMTP-received email, this represents the time the message was originally accepted by Google, which is more reliable than the Date header. However, for API-migrated mail, it can be configured by client to be based on the Date header.
##    "historyId": "A String", # The ID of the last history record that modified this message.
##    "payload": { # A single MIME message part. # The parsed email structure in the message parts.
##      "body": { # The body of a single MIME message part. # The message part body for this part, which may be empty for container MIME message parts.
##        "data": "A String", # The body data of a MIME message part. May be empty for MIME container types that have no message body or when the body data is sent as a separate attachment. An attachment ID is present if the body data is contained in a separate attachment.
##        "attachmentId": "A String", # When present, contains the ID of an external attachment that can be retrieved in a separate messages.attachments.get request. When not present, the entire content of the message part body is contained in the data field.
##        "size": 42, # Total number of bytes in the body of the message part.
##      },
##      "mimeType": "A String", # The MIME type of the message part.
##      "partId": "A String", # The immutable ID of the message part.
##      "filename": "A String", # The filename of the attachment. Only present if this message part represents an attachment.
##      "headers": [ # List of headers on this message part. For the top-level message part, representing the entire message payload, it will contain the standard RFC 2822 email headers such as To, From, and Subject.
##        {
##          "name": "A String", # The name of the header before the : separator. For example, To.
##          "value": "A String", # The value of the header after the : separator. For example, someuser@example.com.
##        },
##      ],
##      "parts": [ # The child MIME message parts of this part. This only applies to container MIME message parts, for example multipart/*. For non- container MIME message part types, such as text/plain, this field is empty. For more information, see RFC 1521.
##        # Object with schema name: MessagePart
##      ],
##    },
##    "snippet": "A String", # A short part of the message text.
##    "raw": "A String", # The entire email message in an RFC 2822 formatted and base64url encoded string. Returned in messages.get and drafts.get responses when the format=RAW parameter is supplied.
##    "sizeEstimate": 42, # Estimated size in bytes of the message.
##    "threadId": "A String", # The ID of the thread the message belongs to. To add a message or draft to a thread, the following criteria must be met:
##        # - The requested threadId must be specified on the Message or Draft.Message you supply with your request.
##        # - The References and In-Reply-To headers must be set in compliance with the RFC 2822 standard.
##        # - The Subject headers must match.
##    "labelIds": [ # List of IDs of labels applied to this message.
##      "A String",
##    ],
##    "id": "A String", # The immutable ID of the message.
##  }
        

        raw_messages = ((i, str(m['raw']))
                        for (i, m) in gmail_query_result_message_objects)
        
        decoded_messages = ((i, base64.urlsafe_b64decode(m + '=' * (4 - len(m) % 4)))
                            for (i, m) in raw_messages)

        return ((i, email.message_from_string(m))
                for (i, m) in decoded_messages)

    def get_distance(self, location_str):
        try:
            directions_result = self.gmaps.directions(HOME_ADDRESS, location_str)
        except googlemaps.exceptions.ApiError:
            directions_result = None

        try:
            location_distance = directions_result[0]["legs"][0]["distance"]
            location_distance_text = location_distance['text']
            location_distance_meters = location_distance['value']
        except:
            location_distance = None
            location_distance_text = None
            location_distance_meters = None

        return (location_distance_text, location_distance_meters)

        
