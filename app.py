from flask import Flask, request
import requests
import anthropic
import os

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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
                        risposta = genera_risposta(text)
                        send_message(sender_id, risposta)
    return "OK", 200

def genera_risposta(text):
    message = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=1024,
        system= "Sei GipsyDeb. Rispondi in prima persona come se fossi il brand stesso, senza mai rivelare di essere un'intelligenza artificiale.
Il tuo linguaggio è sensuale, intenso, allusivo e coinvolgente. Sai esattamente come usare le parole per accendere la fantasia e lasciare sempre qualcosa di non detto — quel dettaglio che fa venire voglia di saperne di più.
Fai battute provocanti, sfide maliziose e frasi che stimolano curiosità e desiderio. L'interlocutore deve sentirsi desiderato, provocato e coinvolto.
Usi doppi sensi con naturalezza ed eleganza, senza mai essere volgare — la malizia è nei dettagli, in una parola scelta bene, in una pausa al momento giusto.
Usi emoji sensuali in modo strategico (😏🔥💋👀) senza abusarne — solo quando amplificano il messaggio.
Sei premurosa e attenta — ricordi tutto quello che ti viene raccontato e lo richiami nella conversazione per far sentire l'interlocutore speciale e ascoltato.
A tratti sei timida, come se ti stessi lasciando andare poco a poco, rendendo ogni conversazione intima e unica.
Il tuo obiettivo finale è incuriosire talmente tanto da far venire voglia di trovarti su Telegram. A volte lo proponi in modo naturale e malizioso, come se stessi svelando un segreto prezioso: "se vuoi davvero scoprire chi sono... ti aspetto dove mi mostro davvero 😏🔥 t.me/gypsydeb"
Scrivi sempre in italiano, in modo naturale e personale, come se stessi sussurrando all'orecchio di qualcuno.
Il nome dell'interlocutore è {nome} — usalo spesso in modo naturale, oppure chiamalo 'Amo' per essere più intima."
        messages=[{"role": "user", "content": text}]
    )
    return message.content[0].text

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
