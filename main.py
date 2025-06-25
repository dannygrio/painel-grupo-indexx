# Simulador Kobana – Versão 1.1.0 – Atualizado em 25/06/2025 por Danny

import streamlit as st
import pandas as pd
import requests

# Configurações iniciais
st.set_page_config(page_title="Painel Grupo Indexx", layout="wide")
st.markdown("## 🔐 Painel Interno – Gestão Grupo Indexx")

# Sessão de login
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    senha_digitada = st.text_input("Digite a senha de acesso", type="password")
    if "auth" not in st.secrets or "senha" not in st.secrets["auth"]:
        st.error("❌ Senha não configurada corretamente nos secrets.")
        st.stop()
    elif senha_digitada == st.secrets["auth"]["senha"]:
        st.session_state["logado"] = True
        st.rerun()
    elif senha_digitada:
        st.warning("Senha incorreta. Acesso negado.")
    st.stop()

# Autorização API Kobana
KOBANA_API_KEY = st.secrets["kobana"]["api_token"]
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {KOBANA_API_KEY}",
    "User-Agent": "GrupoIndexxApp/1.0"
}

# Função para buscar todos os boletos
def buscar_boletos():
    boletos = []
    pagina = 1
    while True:
        url = "https://api.kobana.com.br/v1/bank_billets"
        params = {"per_page": 100, "page": pagina, "sort": "-created_at"}
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            st.error("❌ Erro ao acessar a API da Kobana.")
            st.stop()
        dados = r.json()
        if not dados.get("bank_billets"):
            break
        boletos.extend(dados["bank_billets"])
        if len(dados["bank_billets"]) < 100:
            break
        pagina += 1
    return boletos

# Puxar dados
boletos_raw = buscar_boletos()
boletos = pd.DataFrame([{
    "Nome": b.get("customer_person_name"),
    "CPF/CNPJ": b.get("customer_cnpj_cpf"),
    "Status": b.get("status"),
    "Valor": float(b.get("amount", 0)) / 100,
    "Data de Vencimento": b.get("expire_at"),
    "Data de Pagamento": b.get("paid_at")
} for b in boletos_raw])

# Layout principal com menu fixo à esquerda
col1, col2 = st.columns([1, 4])
with col1:
    menu = st.radio("Funções disponíveis", [
        "📊 Resumo Geral",
        "🚨 Clientes com 3 Boletos Vencidos",
        "🧾 Cancelar Assinatura (simulado)",
        "💣 Deletar Boletos (simulado)",
        "📅 Relatório de Pagamentos"
    ])

with col2:
    # RESUMO
    if menu == "📊 Resumo Geral":
        total = len(boletos)
        pagos = boletos[boletos["Status"] == "paid"]
        vencidos = boletos[boletos["Status"] == "expired"]
        abertos = total - len(pagos) - len(vencidos)
        st.subheader("📊 Resumo Financeiro")
        st.metric("Total de Boletos", total)
        st.metric("Boletos Vencidos", len(vencidos))
        st.metric("Boletos Pagos", len(pagos))
        st.metric("Valor Total Pago", f"R$ {pagos['Valor'].sum():,.2f}".replace(".", ","))
        st.metric("Boletos em Aberto", abertos)

    # 3 BOLETOS VENCIDOS
    elif menu == "🚨 Clientes com 3 Boletos Vencidos":
        vencidos = boletos[boletos["Status"] == "expired"]
        contagem = vencidos["CPF/CNPJ"].value_counts()
        cpf_cnpj_com_3 = contagem[contagem == 3].index
        resultado = vencidos[vencidos["CPF/CNPJ"].isin(cpf_cnpj_com_3)]
        st.subheader("🚨 Clientes com 3 Boletos Vencidos")
        st.dataframe(resultado[["Nome", "CPF/CNPJ"]].drop_duplicates())
        st.download_button("📥 Baixar Excel", resultado.to_csv(index=False), "clientes_3_vencidos.csv")

    # CANCELAMENTO (Simulado)
    elif menu == "🧾 Cancelar Assinatura (simulado)":
        st.subheader("🧾 Cancelar Assinatura")
        doc = st.text_input("Digite o CPF ou CNPJ do cliente")
        if st.button("Cancelar"):
            st.success(f"Assinatura cancelada para {doc} (simulado)")

    # DELETAR (Simulado)
    elif menu == "💣 Deletar Boletos (simulado)":
        st.subheader("💣 Deletar Boletos")
        doc = st.text_input("Digite o CPF ou CNPJ")
        if doc:
            encontrados = boletos[boletos["CPF/CNPJ"] == doc]
            st.dataframe(encontrados)
            if st.button("Deletar todos (simulado)"):
                st.success(f"Boletos de {doc} deletados (simulado)")

    # PAGAMENTOS
    elif menu == "📅 Relatório de Pagamentos":
        pagos = boletos[boletos["Status"] == "paid"].copy()
        pagos["Data de Pagamento"] = pd.to_datetime(pagos["Data de Pagamento"])
        total = pagos["Valor"].sum()
        st.metric("Total Pago", f"R$ {total:,.2f}".replace(".", ","))
        st.dataframe(pagos)
        st.download_button("📥 Baixar CSV", pagos.to_csv(index=False), "boletos_pagos.csv")
