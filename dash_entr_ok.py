import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# --------------------------------------------------------
st.set_page_config(page_title="Dashboard de Entregas", layout="wide")


# --------------------------------------------------------
# FUNÇÃO PARA CARREGAR E LIMPAR A PLANILHA
# --------------------------------------------------------
def carregar_bd():
    caminho = 'dadss.xlsx'
    df = pd.read_excel(caminho, engine="openpyxl", index_col=None)

    # Remove colunas Unnamed
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

    # Remove colunas vazias
    df = df.loc[:, df.columns != ""]

    # Converte DATA automaticamente
    if "DATA" in df.columns:
        df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce")

    return df


# --------------------------------------------------------
# LOGIN
# --------------------------------------------------------
USUARIO = "admin"
SENHA = "1234"

def login():
    st.title("🔐 Login")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if usuario == USUARIO and senha == SENHA:
            st.session_state["logado"] = True
            st.success("Login realizado com sucesso!")
        else:
            st.error("Usuário ou senha incorretos.")


# Estado inicial
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# Se não logado → trava o app
if not st.session_state["logado"]:
    login()
    st.stop()


# --------------------------------------------------------
# MENU LATERAL
# --------------------------------------------------------
st.sidebar.title("📌 Menu")

pagina = st.sidebar.radio(
    "Navegação",
    ["🏠 Início", "📦 Banco de Dados", "🔍 Filtros", "📘 Resumo"]
)


# --------------------------------------------------------
# CARREGAR PLANILHA
# --------------------------------------------------------
df = carregar_bd()


# ========================================================
# 🏠 PÁGINA INÍCIO
# ========================================================
if pagina == "🏠 Início":

    st.title("📊 Dashboard de Entregas")
    st.write("Bem-vindo ao painel da empresa de entregas de areia.")
    st.info("Use o menu lateral para navegar entre as páginas.")



# ========================================================
# 📦 PÁGINA BANCO DE DADOS
# ========================================================
elif pagina == "📦 Banco de Dados":

    st.title("📦 Banco de Dados — Entregas")
    st.dataframe(df, use_container_width=True, hide_index=True)



# ========================================================
# 🔍 PÁGINA FILTROS
# ========================================================
elif pagina == "🔍 Filtros":

    st.title("🔍 Filtros de Entregas")

    df_f = df.copy()

    # Filtro empresa
    if "EMPRESA" in df.columns:
        empresas = sorted(df["EMPRESA"].dropna().unique())
        empresa_sel = st.selectbox("Empresa:", ["Todas"] + empresas)

        if empresa_sel != "Todas":
            df_f = df_f[df_f["EMPRESA"] == empresa_sel]

    # ⭐ Filtro por PLACA
    if "PLACAS" in df.columns:
        placas = sorted(df["PLACAS"].dropna().unique())
        placa_sel = st.selectbox("Placa:", ["Todas"] + placas)

        if placa_sel != "Todas":
            df_f = df_f[df_f["PLACAS"] == placa_sel]

    # Filtro data
    col1, col2 = st.columns(2)

    with col1:
        data_inicio = st.date_input("Data inicial", df["DATA"].min())

    with col2:
        data_fim = st.date_input("Data final", df["DATA"].max())

    df_f = df_f[
        (df_f["DATA"] >= pd.to_datetime(data_inicio)) &
        (df_f["DATA"] <= pd.to_datetime(data_fim))
    ]

    # Filtro Entrega
    entrega_sel = st.selectbox("Entrega:", ["Todas", "Com entrega", "Sem entrega"])

    if entrega_sel == "Com entrega":
        df_f = df_f[df_f["DT.ENTREGA"].notna()]
    elif entrega_sel == "Sem entrega":
        df_f = df_f[df_f["DT.ENTREGA"].isna()]

    st.subheader("📄 Resultados filtrados")
    st.dataframe(df_f, use_container_width=True, hide_index=True)

    # -------------------------------------------
    # 🔽 BOTÃO PARA BAIXAR EXCEL (XLSX)
    # -------------------------------------------
    buffer = BytesIO()
    df_f.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    st.download_button(
        label="📥 Baixar resultados em Excel (.xlsx)",
        data=buffer,
        file_name="filtro_entregas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



# ========================================================
# 📘 PÁGINA RESUMO
# ========================================================
elif pagina == "📘 Resumo":

    st.title("📘 Resumo de Entregas")

    df_r = df.copy()

    st.subheader("🔍 Filtros do Resumo")

    # 1 — Filtro por Empresa
    if "EMPRESA" in df.columns:
        empresas = sorted(df["EMPRESA"].dropna().unique())
        empresa_sel = st.selectbox("Empresa:", ["Todas"] + empresas)

        if empresa_sel != "Todas":
            df_r = df_r[df_r["EMPRESA"] == empresa_sel]

    # ⭐ 2 — Filtro POR PLACA (NOVO)
    if "PLACAS" in df.columns:
        placas = sorted(df["PLACAS"].dropna().unique())
        placa_sel = st.selectbox("Placa:", ["Todas"] + placas)

        if placa_sel != "Todas":
            df_r = df_r[df_r["PLACAS"] == placa_sel]

    # 3 — Filtro por Cliente
    if "CLIENTE" in df.columns:
        clientes = sorted(df["CLIENTE"].dropna().unique())
        cliente_sel = st.selectbox("Cliente:", ["Todos"] + clientes)

        if cliente_sel != "Todos":
            df_r = df_r[df_r["CLIENTE"] == cliente_sel]

    # 4 — Filtro por Data
    col1, col2 = st.columns(2)

    with col1:
        data_inicio = st.date_input("Data inicial", df["DATA"].min(), key="res_ini")

    with col2:
        data_fim = st.date_input("Data final", df["DATA"].max(), key="res_fim")

    df_r = df_r[
        (df_r["DATA"] >= pd.to_datetime(data_inicio)) &
        (df_r["DATA"] <= pd.to_datetime(data_fim))
    ]

    # --------------------------------------------------------
    # CÁLCULOS IMPORTANTES DO RESUMO
    # --------------------------------------------------------
    total_viagens = len(df_r)
    total_m3 = df_r["QUANT."].sum() if "QUANT." in df_r.columns else 0
    total_faturamento = df_r["V.NF"].sum() if "V.NF" in df_r.columns else 0

    # --------------------------------------------------------
    # CARDS RESUMIDOS
    # --------------------------------------------------------
    st.subheader("📊 Indicadores Gerais")

    colA, colB, colC = st.columns(3)

    colA.metric("Total de viagens", total_viagens)
    colB.metric("Total de m³ entregues", f"{total_m3:,.2f}".replace(",", "."))
    colC.metric("Faturamento total", f"R$ {total_faturamento:,.2f}".replace(",", "."))

    st.divider()

    st.subheader("📄 Tabela usada no cálculo")
    st.dataframe(df_r, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("🧾 Resumo Final")
    resumo_texto = f"""
✔ Viagens filtradas: {total_viagens}

✔ Total de m³ filtrados: {total_m3:,.2f}

✔ Faturamento filtrado: R$ {total_faturamento:,.2f}

✔ Total de viagens (novamente): {total_viagens}
"""

    st.write(resumo_texto)

    # --------------------------------------------------------
    # 🔽 BOTÃO PARA BAIXAR RESUMO EM PDF
    # --------------------------------------------------------
    pdf_buffer = BytesIO()
    p = canvas.Canvas(pdf_buffer, pagesize=A4)
    p.setFont("Helvetica", 12)

    y = 800
    for linha in resumo_texto.split("\n"):
        p.drawString(50, y, linha)
        y -= 20
    
    p.save()
    pdf_buffer.seek(0)

    st.download_button(
        label="📥 Baixar resumo em PDF",
        data=pdf_buffer,
        file_name="resumo_entregas.pdf",
        mime="application/pdf"
    )
