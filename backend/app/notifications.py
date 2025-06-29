import os
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase Admin
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "firebase_service_account.json")
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred)

def send_push_notification(fcm_token: str, title: str, body: str, data: dict | None = None):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=fcm_token,
        data=data or {}
    )
    response = messaging.send(message)
    return response 