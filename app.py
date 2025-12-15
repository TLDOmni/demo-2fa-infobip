import streamlit as st
import requests
import json
import re
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Infobip 2FA Demo", page_icon="🛡️", layout="centered")

# --- RECUPERAÇÃO SEGURA DE CREDENCIAIS (DO COFRE) ---
# O Streamlit Cloud injetará essas variáveis automaticamente
try:
    BASE_URL = st.secrets["infobip"]["base_url"]
    API_KEY = st.secrets["infobip"]["api_key"]
    APP_ID = st.secrets["infobip"]["app_id"]
    MSG_ID = st.secrets["infobip"]["msg_id"]
except Exception as e:
    st.error("❌ Erro de Configuração: Secrets não encontrados.")
    st.stop()

HEADERS = {
    'Authorization': f'App {API_KEY}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# --- FUNÇÕES DE BACKEND ---
def tratar_numero(numero_bruto):
    clean = re.sub(r'\D', '', numero_bruto)
    if len(clean) == 11: return "55" + clean
    elif len(clean) == 13 and clean.startswith("55"): return clean
    return None

def enviar_sms(numero):
    endpoint = f"{BASE_URL}/2fa/2/pin"
    payload = json.dumps({"applicationId": APP_ID, "messageId": MSG_ID, "to": numero})
    try:
        r = requests.post(endpoint, headers=HEADERS, data=payload)
        if r.status_code == 200:
            d = r.json()
            if d.get('smsStatus') in ["MESSAGE_NOT_SENT", "REJECTED"]:
                return None, d.get('smsStatus')
            return d.get('pinId'), "OK"
        return None, f"Erro API: {r.status_code}"
    except Exception as e: return None, str(e)

def validar_codigo(pin_id, codigo):
    endpoint = f"{BASE_URL}/2fa/2/pin/{pin_id}/verify"
    payload = json.dumps({"pin": codigo})
    try:
        r = requests.post(endpoint, headers=HEADERS, data=payload)
        if r.status_code == 200:
            return (r.json().get('verified') is True), r.json()
        return False, None
    except: return False, None

# --- FRONTEND ---
def main():
    st.title("🛡️ Acesso Seguro Corporativo")
    st.markdown("Validação de Identidade Multifator (2FA)")

    if 'passo' not in st.session_state: st.session_state.passo = 1
    if 'celular' not in st.session_state: st.session_state.celular = ""
    if 'pin_id' not in st.session_state: st.session_state.pin_id = ""

    # TELA 1
    if st.session_state.passo == 1:
        with st.container(border=True):
            st.subheader("1️⃣ Identificação")
            entrada = st.text_input("Celular (com DDD):", placeholder="Ex: 11 99999-8888")
            
            if st.button("Receber Código SMS", type="primary", use_container_width=True):
                numero_fmt = tratar_numero(entrada)
                if numero_fmt:
                    with st.spinner("Conectando ao Gateway Infobip..."):
                        pid, msg = enviar_sms(numero_fmt)
                    if pid:
                        st.session_state.pin_id = pid
                        st.session_state.celular = numero_fmt
                        st.session_state.passo = 2
                        st.rerun()
                    else:
                        st.error(f"Falha: {msg}")
                else:
                    st.warning("Número inválido.")

    # TELA 2
    elif st.session_state.passo == 2:
        with st.container(border=True):
            st.subheader("2️⃣ Validação")
            st.info(f"Código enviado para: **{st.session_state.celular}**")
            pin = st.text_input("PIN de 6 dígitos:", max_chars=6)
            
            if st.button("Validar Acesso", type="primary", use_container_width=True):
                sucesso, _ = validar_codigo(st.session_state.pin_id, pin)
                if sucesso:
                    st.balloons()
                    st.success("ACESSO AUTORIZADO")
                    time.sleep(4)
                    st.session_state.passo = 1
                    st.rerun()
                else:
                    st.error("Código incorreto.")
            
            if st.button("Voltar"):
                st.session_state.passo = 1
                st.rerun()

if __name__ == "__main__":
    main()