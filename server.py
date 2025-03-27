# === Arquivo: ester_webhook.py ===

from flask import Flask, request
from ester_funcoes import tratar_interacao

app = Flask(__name__)

VERIFY_TOKEN = 'vitor-martins-server'

# Endpoint do webhook do WhatsApp
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Validação do webhook via token
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if token == VERIFY_TOKEN:
            return challenge
        return 'Token inválido', 403

    elif request.method == 'POST':
        # Trata mensagens recebidas
        data = request.get_json()
        print("📩 Webhook recebeu:", data)

        try:
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            messages = value.get('messages')

            if messages:
                message = messages[0]
                sender = message['from']
                msg_type = message.get('type')

                # Passa para a lógica principal
                tratar_interacao(sender, message, msg_type)

        except Exception as e:
            print("⚠️ Erro no webhook:", e)

        return 'EVENT_RECEIVED', 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
