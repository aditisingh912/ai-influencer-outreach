import os, base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import GOOGLE_OAUTH_CLIENT_FILE, GOOGLE_TOKEN_FILE
SCOPES=["https://www.googleapis.com/auth/gmail.send","https://www.googleapis.com/auth/gmail.readonly","https://www.googleapis.com/auth/gmail.modify"]

def service():
    creds=Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE,SCOPES) if os.path.exists(GOOGLE_TOKEN_FILE) else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        else:
            if not os.path.exists(GOOGLE_OAUTH_CLIENT_FILE): raise RuntimeError("Add Gmail OAuth desktop-client JSON at "+GOOGLE_OAUTH_CLIENT_FILE)
            flow=InstalledAppFlow.from_client_secrets_file(GOOGLE_OAUTH_CLIENT_FILE,SCOPES)
            creds=flow.run_local_server(port=0)
        os.makedirs(os.path.dirname(GOOGLE_TOKEN_FILE),exist_ok=True)
        open(GOOGLE_TOKEN_FILE,"w").write(creds.to_json())
    return build("gmail","v1",credentials=creds)

def send(to,subject,body,sender=None):
    msg=MIMEText(body); msg["to"]=to; msg["subject"]=subject
    if sender: msg["from"]=sender
    raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return service().users().messages().send(userId="me",body={"raw":raw}).execute()

def inbox():
    api=service()
    found=api.users().messages().list(userId="me",q="in:inbox newer_than:30d",maxResults=30).execute().get("messages",[])
    output=[]
    for item in found:
        m=api.users().messages().get(userId="me",id=item["id"],format="full").execute()
        h={x["name"].lower():x["value"] for x in m.get("payload",{}).get("headers",[])}
        body=""
        def walk(part):
            nonlocal body
            if part.get("mimeType")=="text/plain" and part.get("body",{}).get("data"):
                body+=base64.urlsafe_b64decode(part["body"]["data"]).decode(errors="ignore")
            for child in part.get("parts",[]): walk(child)
        walk(m.get("payload",{}))
        output.append({"from":h.get("from",""),"subject":h.get("subject",""),"date":h.get("date",""),"body":body[:4000]})
    return output
