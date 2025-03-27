# === Arquivo: ester_funcoes.py ===

import requests
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
API_VERSION = 'v22.0'

usuarios = {}

# Armazena mensagens já processadas para evitar duplicação
mensagens_processadas = set()

# Trata mensagens do webhook (textos ou botões interativos)
def tratar_interacao(sender, message, msg_type):
    message_id = message['id']
    if message_id in mensagens_processadas:
        print("🔁 Mensagem duplicada ignorada.")
        return
    mensagens_processadas.add(message_id)

    if msg_type == 'text':
        texto = message['text']['body'].strip()
        tratar_texto(sender, texto)

    elif msg_type == 'interactive':
        interacao = message.get('interactive')
        if interacao and interacao.get('type') == 'button_reply':
            resposta_id = interacao['button_reply']['id']
            tratar_botao(sender, resposta_id)

# === TEXTOS ===
def tratar_texto(sender, texto):
    estado = usuarios.get(sender, {}).get("estado")

    if not estado:
        usuarios[sender] = {"estado": "nome", "respostas": {}}
        responder(sender, "Olá! Sou a Ester, sua assistente essencial. Como posso te chamar?")
        return

    if estado == "nome":
        usuarios[sender]["respostas"]["nome"] = texto
        etapa_pos_nome(sender)

    elif estado == "informar_valor":
        if texto.isdigit():
            usuarios[sender]["respostas"]["limite"] = int(texto)
            etapa_informar_parcelas(sender)
        else:
            responder(sender, "Por favor, informe apenas números. Exemplo: 1500")

    elif estado == "informar_parcelas":
        if texto.isdigit():
            parcelas = int(texto)
            if 1 <= parcelas <= 18:
                usuarios[sender]["respostas"]["parcelas"] = parcelas
                etapa_calculo(sender)
            else:
                responder(sender, "Digite um número entre 1 e 18.")
        else:
            responder(sender, "Por favor, informe apenas números. Exemplo: 6")

# === BOTÕES ===
def tratar_botao(sender, resposta_id):
    if resposta_id == "tem_limite":
        etapa_informar_valor(sender)

    elif resposta_id == "nao_tem_limite":
        responder(sender, (
            "Para continuar com a solicitação do Saque Essencial, é necessário um cartão com limite. \n"
            "Infelizmente, não conseguimos prosseguir neste momento, mas agradecemos seu contato! 💙"
        ))
        usuarios.pop(sender, None)

    elif resposta_id == "continuar_simulacao":
        responder(sender, "Perfeito! Um especialista irá te acompanhar a partir de agora. ✅")
        usuarios.pop(sender, None)

    elif resposta_id == "refazer_simulacao":
        etapa_informar_valor(sender)

    elif resposta_id == "falar_atendente":
        responder(sender, "Certo! Em instantes um atendente humano vai te chamar. 🧑‍💼")
        usuarios.pop(sender, None)

# === ETAPAS MODULARES ===
def etapa_pos_nome(sender):
    usuarios[sender]["estado"] = "possui_limite"
    nome = usuarios[sender]["respostas"].get("nome", "cliente")
    texto = f"{nome}, você possui limite no cartão de crédito? 💳"
    enviar_botoes_limite(sender, texto)

def etapa_informar_valor(sender):
    usuarios[sender]["estado"] = "informar_valor"
    nome = usuarios[sender]["respostas"].get("nome", "cliente")
    texto = f"{nome}, qual é o limite disponível no seu cartão de crédito? 💳\nDigite apenas números. Ex: 1000"
    responder(sender, texto)

def etapa_informar_parcelas(sender):
    usuarios[sender]["estado"] = "informar_parcelas"
    responder(sender, "Em quantas vezes deseja parcelar? (1 a 18 vezes)")

def etapa_calculo(sender):
    dados = usuarios[sender]["respostas"]
    limite = dados.get("limite")
    parcelas = dados.get("parcelas")

    taxas = {
        1: 23.00, 2: 55.00, 3: 55.10, 4: 55.20, 5: 55.30,
        6: 55.40, 7: 55.47, 8: 55.60, 9: 55.70, 10: 55.80,
        11: 55.87, 12: 56.00, 13: 67.05, 14: 67.30, 15: 67.55,
        16: 67.68, 17: 67.79, 18: 67.94
    }
    taxa = taxas.get(parcelas, 55.0) / 100
    valor_saque = limite / (1 + taxa)
    valor_parcela = valor_saque / parcelas

    saque_fmt = f"R$ {valor_saque:,.2f}".replace(".", ",")
    parcela_fmt = f"R$ {valor_parcela:,.2f}".replace(".", ",")

    usuarios[sender]["estado"] = "pos_calculo"
    etapa_decisao_final(sender, saque_fmt, parcela_fmt)

def etapa_decisao_final(sender, saque_fmt, parcela_fmt):
    texto = (
        f"Com base no seu limite, você pode sacar até *{saque_fmt}* 💰\n"
        f"Parcelado em *{usuarios[sender]['respostas']['parcelas']}x* de aproximadamente *{parcela_fmt}* 💳\n\n"
        "Essa opção te agrada?"
    )
    enviar_botoes_decisao(sender, texto)

# === ENVIO DE MENSAGENS ===
def responder(to, texto):
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": texto}
    }
    requests.post(url, headers=headers, json=payload)

def enviar_botoes_limite(to, texto):
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": texto},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "tem_limite", "title": "1️⃣ Tenho limite"}},
                    {"type": "reply", "reply": {"id": "nao_tem_limite", "title": "2️⃣ Não tenho limite"}}
                ]
            }
        }
    }
    requests.post(url, headers=headers, json=payload)

def enviar_botoes_decisao(to, texto):
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": texto},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "continuar_simulacao", "title": "Sim, Continuar"}},
                    {"type": "reply", "reply": {"id": "refazer_simulacao", "title": "Tentar Outro valor"}},
                    {"type": "reply", "reply": {"id": "falar_atendente", "title": "Falar com Atendente"}}
                ]   
            }
        }
    }
    requests.post(url, headers=headers, json=payload)
