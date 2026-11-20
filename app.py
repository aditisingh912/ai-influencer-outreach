import streamlit as st, pandas as pd
from datetime import datetime,timezone,timedelta
from config import BRAND_NAME,BRAND_DESCRIPTION,SENDER_EMAIL
from database.db import init_db,upsert,all_rows,one,update
from services.influencer_service import read_csv,demos
from services.claude_service import analyze,draft,classify
from services.gmail_service import send,inbox
from services.sheets_service import sync

st.set_page_config(page_title="AI Influencer Outreach",page_icon="📨",layout="wide")
init_db()
st.title("📨 AI Influencer Outreach Assistant")
st.caption("Sankar Group · AI research, CRM, personalized Gmail outreach and reply management")
with st.sidebar:
    st.subheader("Campaign settings")
    st.write("**Brand:** "+BRAND_NAME)
    st.write(BRAND_DESCRIPTION)
    st.warning("Use public business contact details only. Human approval is required before sending.")
tabs=st.tabs(["Dashboard","Research & Import","AI Analysis","Email Outreach","Follow-ups","Reply Manager","Google Sheets"])

with tabs[0]:
    rows=all_rows()
    a,b,c,d=st.columns(4)
    a.metric("Total leads",len(rows)); b.metric("Email available",sum(bool(x["email"]) for x in rows))
    c.metric("Emails sent",sum(x["status"] in ["Email Sent","Follow-up Due","Replied","Interested","Not Interested"] for x in rows))
    d.metric("Interested",sum(x["status"]=="Interested" for x in rows))
    if rows:
        df=pd.DataFrame(rows); st.dataframe(df[["name","username","niche","followers","email","score","status"]],use_container_width=True)
        st.bar_chart(df["status"].value_counts())
    else: st.info("Load demo data or import a CSV in Research & Import.")

with tabs[1]:
    st.subheader("Import researched creators")
    st.write("CSV columns: "+", ".join(["name","username","profile_url","niche","followers","email","location","bio"]))
    file=st.file_uploader("Upload CSV",type=["csv"])
    x,y=st.columns(2)
    if x.button("Load demo data"):
        for _,r in demos().iterrows(): upsert(r.to_dict())
        st.success("Three demo records loaded.")
    if file and y.button("Import CSV"):
        df=read_csv(file)
        for _,r in df.iterrows(): upsert(r.to_dict())
        st.success(f"Imported {len(df)} unique records.")
    st.caption("Research is manual/CSV-based in this version. Use official Meta APIs only when your app and account are eligible; no private scraping or access-control bypass.")
    st.dataframe(pd.DataFrame(all_rows()),use_container_width=True)

with tabs[2]:
    rows=all_rows()
    if rows:
        u=st.selectbox("Choose creator",[p["username"] for p in rows],key="analyze_user"); p=one(u)
        st.json({k:p[k] for k in ["name","username","niche","followers","location","bio"]})
        if st.button("Analyze profile with Claude"):
            try:
                with st.spinner("Claude is analyzing..."): r=analyze(p)
                update(u,score=r["score"],category=r.get("category",""),ai_summary=r.get("summary",""))
                st.metric("Suitability score",str(r["score"])+"/100")
                st.write("**Category:**",r.get("category")); st.write("**Summary:**",r.get("summary")); st.write("**Reason:**",r.get("reason"))
            except Exception as e: st.error(str(e))
    else: st.info("Import creators first.")

with tabs[3]:
    eligible=[p for p in all_rows() if p["email"] and not p["opted_out"]]
    if eligible:
        u=st.selectbox("Recipient", [p["username"] for p in eligible],key="mail_user"); p=one(u)
        kind=st.selectbox("Draft type",["initial","followup1","followup2"])
        if st.button("Generate personalized draft"):
            try: st.session_state["maildraft"]={"user":u,**draft(p,kind)}
            except Exception as e: st.error(str(e))
        dr=st.session_state.get("maildraft")
        if dr and dr["user"]==u:
            subject=st.text_input("Subject",dr["subject"]); body=st.text_area("Body",dr["body"],height=220)
            st.warning("Review recipient, factual claims, sender identity and opt-out wording before sending.")
            approved=st.checkbox("I have reviewed and approve this email.")
            if st.button("Send approved email",disabled=not approved):
                try:
                    result=send(p["email"],subject,body,SENDER_EMAIL or None)
                    update(u,status="Email Sent",last_contacted=datetime.now(timezone.utc).isoformat(),followup_stage=0,email_subject=subject,email_body=body,thread_id=result.get("threadId",""))
                    st.success("Email sent. Gmail message ID: "+result.get("id",""))
                except Exception as e: st.error(str(e))
    else: st.info("No eligible email contacts. Add publicly listed business emails.")

with tabs[4]:
    st.write("Follow-ups are calculated when this tab is refreshed. Each draft requires human approval.")
    now=datetime.now(timezone.utc); due=[]
    for p in all_rows():
        if p["status"] not in ["Email Sent","Follow-up Due"] or p["opted_out"] or p["last_reply"] or not p["last_contacted"]: continue
        stage=int(p["followup_stage"] or 0); wait=4 if stage==0 else 6
        if stage<2 and now-datetime.fromisoformat(p["last_contacted"])>=timedelta(days=wait): due.append(p)
    if not due: st.success("No follow-ups currently due.")
    for p in due:
        with st.expander("@"+p["username"]+" · "+p["email"]):
            st.write("Follow-up stage:",p["followup_stage"]+1)
            kind="followup1" if p["followup_stage"]==0 else "followup2"
            key="follow_"+p["username"]
            if st.button("Generate follow-up",key="gen_"+key):
                try: st.session_state[key]=draft(p,kind)
                except Exception as e: st.error(str(e))
            dr=st.session_state.get(key)
            if dr:
                sub=st.text_input("Subject",dr["subject"],key="sub_"+key)
                body=st.text_area("Body",dr["body"],key="body_"+key)
                ok=st.checkbox("Approve follow-up",key="ok_"+key)
                if st.button("Send follow-up",key="send_"+key,disabled=not ok):
                    try:
                        r=send(p["email"],sub,body,SENDER_EMAIL or None)
                        update(p["username"],status="Follow-up Due",last_contacted=now.isoformat(),followup_stage=int(p["followup_stage"])+1,thread_id=r.get("threadId",""))
                        st.success("Follow-up sent.")
                    except Exception as e: st.error(str(e))

with tabs[5]:
    if st.button("Fetch recent Gmail inbox replies"):
        try: st.session_state["inbox"]=inbox()
        except Exception as e: st.error(str(e))
    for i,m in enumerate(st.session_state.get("inbox",[])):
        with st.expander(m["from"]+" · "+m["subject"]):
            st.write(m["date"]); st.text(m["body"])
            match=next((p for p in all_rows() if p["email"].lower() and p["email"].lower() in m["from"].lower()),None)
            if match:
                if st.button("Classify with Claude",key="class"+str(i)):
                    try: st.session_state["class"+str(i)]=classify(match,m["body"])
                    except Exception as e: st.error(str(e))
                r=st.session_state.get("class"+str(i))
                if r:
                    st.write("Intent:",r["intent"]); st.write("Summary:",r["summary"]); st.write("Next action:",r["suggested_action"])
                    st.text_area("AI reply draft",r["draft_reply"],key="reply"+str(i))
                    if st.button("Approve CRM update",key="update"+str(i)):
                        intent=r["intent"]
                        status={"interested":"Interested","not_interested":"Not Interested","opt_out":"Not Interested","pricing":"Replied","question":"Replied","other":"Replied"}.get(intent,"Replied")
                        update(match["username"],status=status,last_reply=m["body"][:1000],opted_out=1 if intent=="opt_out" else 0)
                        st.success("CRM updated. AI reply remains a draft; send only after human review.")
            else: st.caption("No matching CRM contact found.")

with tabs[6]:
    st.write("Create a Sheet, share it with your service-account email as Editor, then set GOOGLE_SHEET_ID in .env.")
    if st.button("Sync CRM to Google Sheets"):
        try: sync(all_rows()); st.success("Google Sheet synchronized.")
        except Exception as e: st.error(str(e))
st.divider()
st.caption("Prototype note: follow-up queue runs on refresh, not as a persistent background scheduler. Reply drafts are not auto-sent.")
