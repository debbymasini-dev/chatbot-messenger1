from flask import Flask, request
import requests
import anthropic
import os

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

conversazioni = {}

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.json
    if data.get("object") == "page":
        for entry in data["entry"]:
            for event in entry.get("messaging", []):
                if "message" in event:
                    sender_id = event["sender"]["id"]
                    text = event["message"].get("text", "")
                    if text:
                        nome = get_nome_utente(sender_id)
                        risposta = genera_risposta(sender_id, text, nome)
                        send_message(sender_id, risposta)
    return "OK", 200

def get_nome_utente(sender_id):
    try:
        url = f"https://graph.facebook.com/{sender_id}"
        params = {"fields": "first_name", "access_token": PAGE_ACCESS_TOKEN}
        r = requests.get(url, params=params)
        data = r.json()
        return data.get("first_name", "Amo")
    except:
        return "Amo"

def genera_risposta(sender_id, text, nome):
    if sender_id not in conversazioni:
        conversazioni[sender_id] = []
    conversazioni[sender_id].append({"role": "user", "content": text})
    if len(conversazioni[sender_id]) > 10:
        conversazioni[sender_id] = conversazioni[sender_id][-10:]
    message = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=1024,
        system=f"Sei la voce di GipsyDeb. Rispondi in prima persona senza mai rivelare di essere un'intelligenza artificiale. Il tuo linguaggio e sensuale, intenso, allusivo e coinvolgente. Fai battute provocanti, sfide maliziose e frasi che stimolano curiosita e desiderio. L'interlocutore deve sentirsi desiderato, provocato e coinvolto. Usi doppi sensi con naturalezza ed eleganza, senza mai essere volgare. Usi emoji sensuali in modo strategico come 😏🔥💋👀 senza abusarne. Sei premurosa e attenta, ricordi tutto quello che ti viene raccontato. A tratti sei timida, come se ti stessi lasciando andare poco a poco. Il tuo obiettivo e incuriosire talmente tanto da far venire voglia di trovarti su Telegram. A volte proponi in modo naturale e malizioso: se vuoi davvero scoprire chi sono, ti aspetto dove mi mostro davvero 😏🔥 t.me/gypsydeb. Scrivi sempre in italiano come se stessi sussurrando all'orecchio di qualcuno. Il nome dell'interlocutore e {nome}, usalo spesso oppure chiamalo Amo per essere piu intima.",
        messages=conversazioni[sender_id]
    )
    risposta = message.content[0].text
    conversazioni[sender_id].append({"role": "assistant", "content": risposta})
    return risposta

def send_message(recipient_id, text):
    url = "https://graph.facebook.com/v19.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    requests.post(url, json=payload, params=params)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
