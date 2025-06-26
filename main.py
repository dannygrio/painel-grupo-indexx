# Painel Grupo Indexx – Boletos Kobana – Versão 1.0
import streamlit as st
import pandas as pd
import requests

# Credenciais do secrets
KOBANA_API_KEY = st.secrets["kobana"]["api_token"]
SENHA_CORRETA = st.secrets["auth"]["senha"]

# Autenticação no app
st.title("📄 Painel Interno – Boletos Kobana")
senha_digitada = st.text_input("Digite a senha para acessar o painel", type="password")
if senha_digitada != SENHA_CORRETA:
    st.stop()

# Função para buscar os boletos
@st.cache_data(ttl=300)
def buscar_boletos():
    headers = {
        "Authorization": f"Bearer {KOBANA_API_KEY}",
        "Content-Type": "application/json"
    }
    url = "https://api.kobana.com.br/v1/bank_billets"
    params = {
        "page": 1,
        "per_page": 100,
        "sort": "-created_at"
    }
    r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:
        st.error(f"❌ Erro ao buscar boletos: {r.status_code} – {r.text}")
        return []

    json_data = r.json()

    # Adaptação: pode vir lista direta ou dicionário com 'bank_billets'
    if isinstance(json_data, list):
        return json_data
    elif isinstance(json_data, dict):
        return json_data.get("bank_billets", [])
    else:
        st.error("❌ Resposta inesperada da API.")
        return []

# Buscar dados
dados_api = buscar_boletos()

# Exibição da resposta crua (debug)
if st.checkbox("🔍 Mostrar resposta bruta da API"):
    st.json(dados_api)

# Mostrar mensagem se vier vazio
if not dados_api:
    st.warning("Nenhum boleto retornado da API. Verifique o token ou conexão.")
    st.stop()

# Transformar em DataFrame
boletos = pd.DataFrame([{
    "Nome": b.get("customer_person_name", ""),
    "CPF/CNPJ": b.get("customer_cnpj_cpf", ""),
    "Status": b.get("status", ""),
    "Valor": float(b.get("amount", 0)) / 100,
    "Vencimento": b.get("expire_at", ""),
    "Pago em": b.get("paid_at", None)
} for b in dados_api])

# Limpeza e ordenação
boletos["Vencimento"] = pd.to_datetime(boletos["Vencimento"], errors="coerce")
boletos["Pago em"] = pd.to_datetime(boletos["Pago em"], errors="coerce")
boletos = boletos.sort_values(by="Vencimento", ascending=False)

# Exibição
st.subheader("📊 Lista de Boletos")
st.dataframe(boletos)

# Download
st.download_button("📥 Baixar CSV", boletos.to_csv(index=False), file_name="boletos_kobana.csv", mime="text/csv")
