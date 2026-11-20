import json, anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, BRAND_NAME, BRAND_DESCRIPTION

def ask(prompt,limit=800):
    if not ANTHROPIC_API_KEY: raise RuntimeError("Set ANTHROPIC_API_KEY in .env")
    r=anthropic.Anthropic(api_key=ANTHROPIC_API_KEY).messages.create(
      model=CLAUDE_MODEL,max_tokens=limit,messages=[{"role":"user","content":prompt}])
    return "".join(x.text for x in r.content if getattr(x,"type",None)=="text")

def parse_json(raw):
    raw=raw.strip()
    if raw.startswith("```"): raw=raw.split("\n",1)[-1].rsplit("```",1)[0]
    return json.loads(raw)

def analyze(person):
    p=f"""Assess this creator for brand fit. Brand: {BRAND_NAME}. Offer/context: {BRAND_DESCRIPTION}.
Creator public/business information: {json.dumps(person,ensure_ascii=False)}
Return JSON only: score (0-100 integer), category, summary, reason.
Do not invent engagement, audience demographics, or facts. State when evidence is limited."""
    x=parse_json(ask(p,600)); x["score"]=max(0,min(100,int(x.get("score",0))))
    return x

def draft(person,kind="initial"):
    instructions={
      "initial":"Write a concise personalized first collaboration email.",
      "followup1":"Write a polite short first follow-up; do not imply they replied.",
      "followup2":"Write a respectful final follow-up and say this is the last follow-up."
    }
    p=f"""{instructions[kind]} Brand: {BRAND_NAME}. Offer: {BRAND_DESCRIPTION}.
Creator: {json.dumps(person,ensure_ascii=False)}
Mention only supplied facts. Include a clear CTA, sender identification placeholder if needed, and opt-out sentence. Return JSON only with subject and body."""
    return parse_json(ask(p,700))

def classify(person,reply):
    p=f"""Classify this email reply from creator {person.get('name')} (@{person.get('username')}).
Reply text: {reply}
Return JSON only: intent (interested/not_interested/pricing/question/opt_out/other), summary, suggested_action, draft_reply.
Do not promise prices or terms that are not known."""
    return parse_json(ask(p,700))
