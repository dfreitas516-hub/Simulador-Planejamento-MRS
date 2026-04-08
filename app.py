import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# ===== SIMULAÇÃO =====
def simulacao(clientes, dias_total, prazo, tempo_rota, prioridade):

    patio = {c: clientes[c]["volume"] for c in clientes}
    rota = {c: [] for c in clientes}
    idade_patio = {c: 0 for c in clientes}

    dados = []

    for dia in range(1, dias_total + 1):

        linha = {"Dia": dia}

        capacidade_total = sum([
            clientes[c]["veiculos"] * clientes[c]["viagens"] * clientes[c]["capacidade"]
            for c in clientes
        ])

        capacidade_restante = capacidade_total

        # CHEGADAS
        for c in clientes:
            if dia == clientes[c]["chegada_dia"]:
                patio[c] += clientes[c]["chegada_volume"]
                idade_patio[c] = 0

        # ENTREGA (ROTA)
        for c in clientes:
            entregue = 0
            nova_rota = []

            for carga in rota[c]:
                if carga["dias"] >= tempo_rota:
                    entregue += carga["volume"]
                else:
                    carga["dias"] += 1
                    nova_rota.append(carga)

            rota[c] = nova_rota
            linha[f"{c}_Entregue"] = entregue

        # EXPEDIÇÃO (PRIORIDADE)
        for c in prioridade:
            expedido = min(patio[c], capacidade_restante)
            patio[c] -= expedido
            capacidade_restante -= expedido

            if expedido > 0:
                rota[c].append({"volume": expedido, "dias": 0})

        # STATUS + AGING
        for c in clientes:

            idade_patio[c] += 1 if patio[c] > 0 else 0
            idade_rota = max([r["dias"] for r in rota[c]], default=0)

            status = "OK"
            if dia > prazo and patio[c] > 0:
                status = "ATRASO"

            linha[f"{c}_Patio"] = round(patio[c],1)
            linha[f"{c}_E1"] = idade_patio[c] if patio[c] > 0 else 0
            linha[f"{c}_Rota"] = round(sum([r["volume"] for r in rota[c]]),1)
            linha[f"{c}_E2"] = idade_rota
            linha[f"{c}_Status"] = status

        linha["Capacidade_Total"] = capacidade_total
        linha["Utilizado"] = capacidade_total - capacidade_restante

        dados.append(linha)

    return pd.DataFrame(dados)


# ===== GANTT =====
def gerar_gantt(clientes, prazo):
    fig, ax = plt.subplots()

    y = 0
    labels = []

    for cliente, dados in clientes.items():

        # estoque atual
        ax.barh(y, prazo, left=0)
        labels.append(f"{cliente} - Estoque")
        y += 1

        # chegada futura
        ax.barh(y, prazo, left=dados["chegada_dia"])
        labels.append(f"{cliente} - Chegada")
        y += 1

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Dias")
    ax.set_title("Gantt Operacional")

    return fig


# ===== GRÁFICO LINHA =====
def grafico_estoque(df):
    fig, ax = plt.subplots()

    ax.plot(df["Dia"], df["Centerval_Patio"])
    ax.plot(df["Dia"], df["Steel_Patio"])

    ax.set_title("Estoque em Pátio")
    ax.set_xlabel("Dias")
    ax.set_ylabel("Volume")

    return fig


# ===== INTERFACE =====
st.title("Simulador Logístico Completo")

col1, col2 = st.columns(2)

# CENTERVAL
with col1:
    st.subheader("Centerval")
    c_volume = st.number_input("Volume pátio", value=1500.0)
    c_veic = st.number_input("Veículos", value=1)
    c_viagens = st.number_input("Viagens", value=4)
    c_cap = st.number_input("Capacidade", value=113)
    c_dia = st.number_input("Dia chegada", value=3)
    c_vol = st.number_input("Volume chegada", value=1200.0)

# STEEL
with col2:
    st.subheader("Steel")
    s_volume = st.number_input("Volume pátio", value=800.0)
    s_veic = st.number_input("Veículos", value=3)
    s_viagens = st.number_input("Viagens", value=4)
    s_cap = st.number_input("Capacidade", value=113)
    s_dia = st.number_input("Dia chegada", value=5)
    s_vol = st.number_input("Volume chegada", value=1000.0)

st.divider()

prazo = st.number_input("Prazo máximo (dias)", value=10)
tempo_rota = st.number_input("Tempo em rota", value=3)
dias_total = st.slider("Período", 10, 40, 30)

prioridade = st.selectbox(
    "Prioridade",
    ["Steel primeiro", "Centerval primeiro"]
)

ordem = ["Steel","Centerval"] if prioridade == "Steel primeiro" else ["Centerval","Steel"]


# ===== EXECUÇÃO =====
if st.button("Rodar Simulação"):

    clientes = {
        "Centerval": {
            "volume": c_volume,
            "veiculos": c_veic,
            "viagens": c_viagens,
            "capacidade": c_cap,
            "chegada_dia": c_dia,
            "chegada_volume": c_vol
        },
        "Steel": {
            "volume": s_volume,
            "veiculos": s_veic,
            "viagens": s_viagens,
            "capacidade": s_cap,
            "chegada_dia": s_dia,
            "chegada_volume": s_vol
        }
    }

    df = simulacao(clientes, dias_total, prazo, tempo_rota, ordem)

    st.dataframe(df)

    # ===== CARDS =====
    st.subheader("Status de Prazo")

    colc1, colc2 = st.columns(2)

    atraso_c = (df["Centerval_Status"] == "ATRASO").any()
    atraso_s = (df["Steel_Status"] == "ATRASO").any()

    with colc1:
        st.error("Centerval em ATRASO") if atraso_c else st.success("Centerval OK")

    with colc2:
        st.error("Steel em ATRASO") if atraso_s else st.success("Steel OK")

    # ===== GANTT =====
    st.subheader("Gantt Operacional")
    st.pyplot(gerar_gantt(clientes, prazo))

    # ===== LINHA =====
    st.subheader("Evolução Estoque")
    st.pyplot(grafico_estoque(df))

    # ===== EXPORTAR =====
    file = "simulador_completo.xlsx"
    df.to_excel(file, index=False)

    with open(file, "rb") as f:
        st.download_button("Baixar Excel", f, file_name=file)
