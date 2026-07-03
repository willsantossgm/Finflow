import os
from datetime import date, timedelta
import json
import re
import streamlit as st
import pandas as pd
import altair as alt
import requests

# Regex simples e padrão de mercado para validação de e-mail
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Importando a classe do nosso backend
from backend.financas import GerenciadorFinancas

# Configuração da página do Streamlit
st.set_page_config(
    page_title="FinFlow - Controle Financeiro Premium",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização personalizada via CSS para dar um toque premium e moderno
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Outfit:wght@300;400;600;800&display=swap');

    /* Fontes globais */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Customização dos botões Streamlit */
    div.stButton > button {
        background-color: #115e59 !important;
        color: white !important;
        border: 1px solid #00D1B2 !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        background-color: #00D1B2 !important;
        color: #1A1F2C !important;
        box-shadow: 0 0 10px rgba(0, 209, 178, 0.5) !important;
        transform: translateY(-2px) !important;
    }

    /* Customização das caixas de input Streamlit */
    div[data-baseweb="input"] {
        border-radius: 8px !important;
        border: 1px solid #2D3748 !important;
        background-color: #1A1F2C !important;
    }
    div[data-baseweb="select"] {
        border-radius: 8px !important;
        border: 1px solid #2D3748 !important;
    }

    /* Customização da barra de progresso (metas) */
    div[data-testid="stProgress"] > div {
        height: 6px !important;
    }
    div[data-testid="stProgress"] > div > div {
        background-color: #00D1B2 !important;
    }

    /* Cabeçalho de Elite */
    .header-elite {
        margin-bottom: 2.5rem;
        text-align: left;
        border-bottom: 1px solid #2D3748;
        padding-bottom: 1.75rem;
    }
    .header-title {
        font-family: 'Outfit', sans-serif;
        font-size: 54px;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        line-height: 1.1;
        letter-spacing: -1.5px;
    }
    .header-title span {
        font-weight: 300;
        color: #00E5FF;
        text-shadow: 0px 0px 15px rgba(0, 229, 255, 0.4);
    }
    .header-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        color: #a0aec0;
        margin-top: 0.5rem;
        font-weight: 400;
        letter-spacing: 0.5px;
    }

    /* Grid de KPIs */
    .kpi-container {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 2rem;
        flex-wrap: wrap;
    }
    .kpi-card {
        flex: 1;
        min-width: 250px;
        background-color: #1A1F2C;
        border: 1px solid #2D3748;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
        display: flex;
        flex-direction: column;
    }
    .kpi-card-highlight {
        flex: 1;
        min-width: 250px;
        background: linear-gradient(135deg, #09332f 0%, #0c2b29 100%);
        border: 1.5px solid #00D1B2;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 0 15px rgba(0, 209, 178, 0.2);
        display: flex;
        flex-direction: column;
    }
    .kpi-title {
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    .kpi-value {
        font-family: 'Outfit', sans-serif;
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
        margin-top: 0.5rem;
    }
    .kpi-value-highlight {
        font-family: 'Outfit', sans-serif;
        font-size: 28px;
        font-weight: 700;
        color: #00D1B2;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Definição dos caminhos dos arquivos de dados e config locais
ARQUIVO_DADOS = "dados_financeiros.json"
ARQUIVO_CONFIG = "config_financas.json"

# Helper functions para Autenticação via Supabase Auth
def supabase_login(email, password):
    url = "https://ojiutbtyaxmpwstgnmnn.supabase.co/auth/v1/token?grant_type=password"
    headers = {
        "apikey": "sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
        "Authorization": "Bearer sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
        "Content-Type": "application/json"
    }
    payload = {"email": email, "password": password}
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response
    except Exception:
        return None

def supabase_signup(email, password):
    url = "https://ojiutbtyaxmpwstgnmnn.supabase.co/auth/v1/signup"
    headers = {
        "apikey": "sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
        "Authorization": "Bearer sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
        "Content-Type": "application/json"
    }
    payload = {"email": email, "password": password}
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response
    except Exception:
        return None

# ----------------- TELA DE AUTENTICAÇÃO CLERK / SUPABASE RLS -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "clerk_user_id" not in st.session_state:
    st.session_state.clerk_user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

if not st.session_state.authenticated:
    # Cabeçalho da página de login estilo elite
    st.markdown("""
        <div class="header-elite">
            <h1 class="header-title">Fin<span>flow</span> ⚡</h1>
            <div class="header-subtitle">Gestão Inteligente de Capital • Painel Premium • Identidade Segura via Clerk</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='max-width: 500px; margin: 0 auto; padding: 2rem; background-color: #1e293b; border-radius: 12px; border: 1px solid #334155;'>", unsafe_allow_html=True)
    
    auth_option = st.radio("Selecione uma opção:", ["Entrar (Login)", "Registrar-se (Cadastro)"], horizontal=True)
    
    email = st.text_input("E-mail do Clerk", placeholder="nome@provedor.com")
    senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
    
    if auth_option == "Entrar (Login)":
        if st.button("Acessar Conta 🔑", use_container_width=True):
            if email and senha:
                email_clean = email.strip().lower()
                if not EMAIL_REGEX.match(email_clean):
                    st.error("Por favor, digite um formato de e-mail válido (ex: nome@provedor.com).")
                else:
                    with st.spinner("Conectando ao Clerk..."):
                        res = supabase_login(email_clean, senha)
                        if res is not None and res.status_code == 200:
                            data = res.json()
                            st.session_state.authenticated = True
                            st.session_state.clerk_user_id = data['user']['id']
                            st.session_state.user_email = email_clean
                            st.session_state.user_access_token = data.get("access_token")
                            st.success("Autenticado com sucesso!")
                            st.rerun()
                        else:
                            error_detail = None
                            if res is not None:
                                try:
                                    json_res = res.json()
                                    error_detail = json_res.get("error_description") or json_res.get("message") or json_res.get("msg") or json_res.get("error")
                                except Exception:
                                    pass
                            if not error_detail:
                                error_detail = "Senha incorreta ou e-mail inválido."
                            st.error(f"Erro no Login: {error_detail}")
            else:
                st.error("Preencha todos os campos!")
    else:
        if st.button("Criar Conta Nova 🚀", use_container_width=True):
            if email and senha:
                email_clean = email.strip().lower()
                if not EMAIL_REGEX.match(email_clean):
                    st.error("Por favor, digite um formato de e-mail válido (ex: nome@provedor.com).")
                elif len(senha) < 6:
                    st.error("A senha deve ter no mínimo 6 caracteres.")
                else:
                    with st.spinner("Cadastrando no Clerk..."):
                        res = supabase_signup(email_clean, senha)
                        if res is not None and res.status_code in [200, 201]:
                            st.success("Cadastro efetuado! Se necessário, verifique sua caixa de e-mail e faça login.")
                        else:
                            error_detail = None
                            if res is not None:
                                try:
                                    json_res = res.json()
                                    error_detail = json_res.get("message") or json_res.get("msg") or json_res.get("error_description") or json_res.get("error")
                                except Exception:
                                    pass
                            if not error_detail:
                                error_detail = "E-mail inválido ou já registrado."
                            st.error(f"Erro no Cadastro: {error_detail}")
            else:
                st.error("Preencha todos os campos!")
                
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop() # Bloqueia toda a renderização abaixo até que faça login!

# ----------------- INICIALIZAÇÃO DO GERENCIADOR AUTENTICADO -----------------
# Garantimos que o GerenciadorFinancas seja instanciado com o ID do Clerk atual
if "gerenciador" not in st.session_state or getattr(st.session_state.gerenciador, "user_id", None) != st.session_state.clerk_user_id or not hasattr(st.session_state.gerenciador, "agrupar_por_categoria_ano"):
    st.session_state.gerenciador = GerenciadorFinancas(
        user_id=st.session_state.clerk_user_id,
        access_token=st.session_state.get("user_access_token")
    )
    # Tenta carregar dados do Supabase
    st.session_state.gerenciador.carregar_dados(ARQUIVO_DADOS)

# Carregar configurações locais de Renda e Categorias
if "renda_mensal" not in st.session_state:
    st.session_state.renda_mensal = 0.0
if "limite_gastos" not in st.session_state:
    st.session_state.limite_gastos = 1500.0
if "categorias" not in st.session_state:
    st.session_state.categorias = ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde"]

if os.path.exists(ARQUIVO_CONFIG):
    try:
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
            st.session_state.renda_mensal = config.get("renda_mensal", 0.0)
            st.session_state.limite_gastos = config.get("limite_gastos", 1500.0)
            if "categorias" in config:
                st.session_state.categorias = config["categorias"]
    except Exception:
        pass

st.markdown('''
    <style>
        /* Importação de uma fonte geométrica ultra fina e moderna */
        @import url("https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400&display=swap");

        .brand-container {
            display: flex !important;
            align-items: center !important;
            padding: 20px 0px 10px 0px !important;
            margin-bottom: 30px !important;
            gap: 15px !important;
        }
        .brand-text {
            font-family: "Inter", sans-serif !important;
            font-size: 68px !important;
            font-weight: 300 !important; /* Linhas finas e elegantes */
            letter-spacing: -1.5px !important;
            margin: 0px !important;
            line-height: 1 !important;
            color: #00E5FF !important; /* Ciano/Teal brilhante */
        }
        .brand-icon {
            font-size: 62px !important;
            line-height: 1 !important;
            display: inline-block !important;
            /* Gradiente no emoji de raio (Laranja para Vermelho) */
            background: linear-gradient(135deg, #FF9100 0%, #FF3D00 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
        }
    </style>

    <div class="brand-container">
        <h1 class="brand-text">Finflow</h1>
        <span class="brand-icon">⚡</span>
    </div>
''', unsafe_allow_html=True)

# ----------------- BARRA LATERAL (SIDEBAR) -----------------
st.sidebar.markdown("### 👤 Perfil & Autenticação")
st.sidebar.info(f"**Conta:** {st.session_state.user_email}\n\n**Clerk ID:** `{st.session_state.clerk_user_id[:20]}...`")

if st.sidebar.button("🚪 Sair (Logout)", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.clerk_user_id = None
    st.session_state.user_email = None
    st.session_state.user_access_token = None
    # Limpa o gerenciador
    st.session_state.gerenciador = GerenciadorFinancas()
    st.success("Sessão encerrada!")
    st.rerun()

# 🧭 MENU DE NAVEGAÇÃO na Barra Lateral
st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 Navegação")
pagina_selecionada = st.sidebar.radio(
    "Ir para:",
    options=["💸 Controle de Despesas", "💰 Gestão de Receitas", "📊 Comparação Geral"]
)

# Renderiza filtro de referência e carrega dados base de acordo com a seleção
if pagina_selecionada != "📊 Comparação Geral":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 Filtro de Referência")
    meses_disponiveis = st.session_state.gerenciador.obter_meses_disponiveis()
    hoje_str = date.today().strftime("%m/%Y")
    try:
        default_mes_idx = meses_disponiveis.index(hoje_str)
    except ValueError:
        default_mes_idx = len(meses_disponiveis) - 1

    mes_filtro = st.sidebar.selectbox(
        "Mês de Referência:",
        options=meses_disponiveis,
        index=default_mes_idx
    )

    # ----------------- FILTRAGEM E CÁLCULO DOS DADOS -----------------
    transacoes_filtradas = st.session_state.gerenciador.filtrar_por_mes_ano(mes_filtro)

    # Separa despesas de receitas
    receitas_filtradas = [t for t in transacoes_filtradas if t.categoria == "Receita"]
    gastos_filtrados = [t for t in transacoes_filtradas if t.categoria != "Receita"]

    total_receitas = sum(r.valor for r in receitas_filtradas)
    total_gastos = sum(g.valor for g in gastos_filtrados)

    # Renda dinâmica = Renda fixa + receitas registradas
    renda_atual = st.session_state.renda_mensal + total_receitas
    saldo_restante = renda_atual - total_gastos

# ----------------- RENDERIZAÇÃO DA PÁGINA SELECIONADA -----------------

if pagina_selecionada in ["💸 Controle de Despesas", "💰 Gestão de Receitas"]:
    # ----------------- GRID DE KPIs ESTILO DASHBOARD -----------------
    kpi_html = f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">Renda Mensal ({mes_filtro})</div>
            <div class="kpi-value">R$ {renda_atual:,.2f}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Total de Gastos ({mes_filtro})</div>
            <div class="kpi-value" style="color: #ef4444;">R$ {total_gastos:,.2f}</div>
        </div>
        <div class="kpi-card-highlight">
            <div class="kpi-title" style="color: #00D1B2;">Saldo Disponível ({mes_filtro})</div>
            <div class="kpi-value-highlight">R$ {saldo_restante:,.2f}</div>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)
    st.markdown("---")

# RENDERIZAÇÃO ESPECÍFICA DE CADA MENU

if pagina_selecionada == "💸 Controle de Despesas":
    # ----------------- PÁGINA DE DESPESAS -----------------
    
    # Metas e Limite de Gastos (Barra de Metas Fina e Elegante)
    limite_mensal = st.session_state.limite_gastos
    if limite_mensal > 0:
        porcentagem_limite = min(total_gastos / limite_mensal, 1.0)

        st.markdown(f"### 🎯 Metas do Mês ({mes_filtro})")

        col_meta1, col_meta2 = st.columns([3, 1])
        with col_meta1:
            st.progress(porcentagem_limite)
        with col_meta2:
            st.markdown(f"Consumido: **R$ {total_gastos:,.2f}** de **R$ {limite_mensal:,.2f}** ({porcentagem_limite*100:.1f}%)")

        if total_gastos >= limite_mensal:
            st.error(f"🚨 **Limite de gastos excedido!** Você ultrapassou o seu teto planejado de R$ {limite_mensal:,.2f}.")
        elif total_gastos >= limite_mensal * 0.8:
            st.warning(f"⚠️ **Cuidado!** Você está quase atingindo seu limite (mais de 80% do teto de R$ {limite_mensal:,.2f} consumido).")
        else:
            st.success("✅ Seu nível de gastos está dentro da meta estipulada para o mês.")

        st.markdown("---")

    col_form, col_list = st.columns([1, 2])

    with col_form:
        st.markdown("### 📝 Adicionar Novo Gasto")
        
        # Estados locais de valor para limpar após adicionar gasto
        if "val_descricao" not in st.session_state:
            st.session_state.val_descricao = ""
        if "val_valor" not in st.session_state:
            st.session_state.val_valor = 0.0

        descricao = st.text_input("Descrição do Gasto", value=st.session_state.val_descricao, placeholder="Ex: Mercado, Gasolina, Uber", key="gasto_desc")
        valor = st.number_input("Valor (R$)", min_value=0.0, value=st.session_state.val_valor, step=5.0, format="%.2f", key="gasto_val")
        
        # Monta as opções do dropdown com a opção especial no final
        opcoes_dropdown_cat = st.session_state.categorias + ["➕ Criar Nova Categoria..."]
        
        if "selected_categoria" not in st.session_state:
            st.session_state.selected_categoria = st.session_state.categorias[0]
            
        try:
            default_idx = opcoes_dropdown_cat.index(st.session_state.selected_categoria)
        except ValueError:
            default_idx = 0

        categoria_selecionada = st.selectbox(
            "Categoria",
            options=opcoes_dropdown_cat,
            index=default_idx,
            key="gasto_cat_select"
        )

        # Condicional reativa para criar nova categoria
        if categoria_selecionada == "➕ Criar Nova Categoria...":
            nova_categoria_input = st.text_input("Digite o nome da nova categoria:", placeholder="Ex: Educação, Presentes", key="gasto_nova_cat").strip()
            if st.button("Salvar Categoria", use_container_width=True, key="gasto_salvar_cat"):
                if nova_categoria_input:
                    cat_normalizada = nova_categoria_input.capitalize()
                    if cat_normalizada not in st.session_state.categorias:
                        st.session_state.categorias.append(cat_normalizada)
                        st.session_state.selected_categoria = cat_normalizada
                        try:
                            with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
                                json.dump({
                                    "renda_mensal": st.session_state.renda_mensal,
                                    "limite_gastos": st.session_state.limite_gastos,
                                    "categorias": st.session_state.categorias
                                }, f)
                            st.success(f"Categoria '{cat_normalizada}' criada e selecionada!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar nova categoria: {e}")
                    else:
                        st.warning("Esta categoria já existe!")
                else:
                    st.error("Por favor, digite um nome válido.")
        else:
            st.session_state.selected_categoria = categoria_selecionada

        data_gasto = st.date_input("Data do Gasto", value=date.today(), key="gasto_data")

        if st.button("Adicionar Gasto ➕", use_container_width=True, key="gasto_btn_add"):
            if not descricao.strip():
                st.error("Por favor, preencha a descrição do gasto.")
            elif valor <= 0:
                st.error("O valor do gasto deve ser maior que zero.")
            elif st.session_state.selected_categoria == "➕ Criar Nova Categoria...":
                st.error("Por favor, crie e salve a nova categoria primeiro ou escolha uma existente.")
            else:
                try:
                    # Adiciona e persiste os dados
                    st.session_state.gerenciador.adicionar_gasto(
                        descricao=descricao,
                        valor=valor,
                        categoria=st.session_state.selected_categoria,
                        data=data_gasto
                    )
                    st.session_state.gerenciador.salvar_dados(ARQUIVO_DADOS)
                    st.success("Gasto adicionado e salvo com sucesso!")
                    
                    # Reseta os campos
                    st.session_state.val_descricao = ""
                    st.session_state.val_valor = 0.0
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao adicionar gasto: {e}")

    with col_list:
        st.markdown(f"### 📊 Histórico de Despesas ({mes_filtro})")
        if len(gastos_filtrados) == 0:
            st.info(f"Nenhuma despesa cadastrada para o mês {mes_filtro}.")
        else:
            dados_tabela = []
            for g in reversed(gastos_filtrados):
                dados_tabela.append({
                    "Descrição": g.descricao,
                    "Valor (R$)": f"R$ {g.valor:.2f}",
                    "Categoria": g.categoria,
                    "Data": g.data.strftime("%d/%m/%Y")
                })

            st.dataframe(dados_tabela, use_container_width=True)

            # Botão de exportação
            df_export = pd.DataFrame([
                {
                    "ID": g.id,
                    "Descrição": g.descricao,
                    "Valor (R$)": g.valor,
                    "Categoria": g.categoria,
                    "Data": g.data.strftime("%Y-%m-%d")
                }
                for g in gastos_filtrados
            ])
            csv_data = df_export.to_csv(index=False).encode("utf-8")
            
            st.download_button(
                label="📥 Exportar Despesas Deste Mês (CSV)",
                data=csv_data,
                file_name=f"despesas_{mes_filtro.replace('/', '_')}.csv",
                mime="text/csv",
                key="export_despesas_btn",
                use_container_width=True
            )

        st.markdown("---")

        # Exclusão de Despesas
        st.markdown("### 🗑️ Excluir Despesa")
        if len(gastos_filtrados) == 0:
            st.info("Nenhuma despesa disponível para exclusão.")
        else:
            opcoes_exclusao_gastos = {
                g.id: f"{g.descricao} (R$ {g.valor:.2f} - {g.data.strftime('%d/%m/%Y')})"
                for g in gastos_filtrados
            }
            
            gasto_selecionado_id = st.selectbox(
                "Selecione uma despesa para excluir:",
                options=list(opcoes_exclusao_gastos.keys()),
                format_func=lambda x: opcoes_exclusao_gastos[x],
                key="gasto_excluir_select"
            )
            
            if st.button("Excluir Despesa 🗑️", use_container_width=True):
                if gasto_selecionado_id:
                    if st.session_state.gerenciador.remover_gasto(gasto_selecionado_id):
                        try:
                            st.session_state.gerenciador.salvar_dados(ARQUIVO_DADOS)
                            st.success("Despesa excluída com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar dados após exclusão: {e}")
                    else:
                        st.error("Erro interno ao tentar remover a despesa.")

        st.markdown("---")

        # Gráficos por Categoria (Apenas despesas)
        st.markdown("#### Distribuição de Gastos por Categoria")
        resumo_categorias = {}
        for g in gastos_filtrados:
            cat_normalizada = g.categoria.strip().capitalize()
            resumo_categorias[cat_normalizada] = resumo_categorias.get(cat_normalizada, 0.0) + g.valor

        if resumo_categorias:
            df_categorias = pd.DataFrame([
                {"Categoria": cat, "Valor": total}
                for cat, total in resumo_categorias.items()
            ])

            if not df_categorias.empty and "Valor" in df_categorias.columns:
                total_geral = df_categorias["Valor"].sum()
                df_categorias["Porcentagem"] = (df_categorias["Valor"] / total_geral * 100).round(1) if total_geral > 0 else 0.0

                col_l, col_c, col_r = st.columns([1, 2, 1])
                with col_c:
                    st.markdown("<p style='text-align: center; font-size: 0.95rem; font-weight: 600; opacity: 0.9;'>Proporção do Orçamento (%)</p>", unsafe_allow_html=True)
                    grafico_rosca = alt.Chart(df_categorias).mark_arc(innerRadius=60).encode(
                        theta=alt.Theta(field="Valor", type="quantitative"),
                        color=alt.Color(
                            field="Categoria",
                            type="nominal",
                            scale=alt.Scale(scheme="tealblues")
                        ),
                        tooltip=[
                            alt.Tooltip("Categoria", title="Categoria"),
                            alt.Tooltip("Valor", format="$,.2f", title="Valor"),
                            alt.Tooltip("Porcentagem", format=".1f", title="Proporção (%)")
                        ]
                    ).properties(height=280).interactive()

                    st.altair_chart(grafico_rosca, use_container_width=True)

elif pagina_selecionada == "💰 Gestão de Receitas":
    # ----------------- PÁGINA DE RECEITAS -----------------
    
    st.markdown(f"### 💰 Gestão de Receitas ({mes_filtro})")
    
    # Novo KPI individual: Total Recebido no Mês Estilo Dashboard Premium
    st.markdown(f"""
        <div class="kpi-card-highlight" style="margin-bottom: 2rem;">
            <div class="kpi-title" style="color: #00D1B2;">Total Recebido no Mês ({mes_filtro})</div>
            <div class="kpi-value-highlight">R$ {total_receitas:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)
    
    col_form, col_list = st.columns([1, 2])

    with col_form:
        st.markdown("### 💰 Adicionar Novo Ganho")
        
        if "val_desc_rec" not in st.session_state:
            st.session_state.val_desc_rec = ""
        if "val_valor_rec" not in st.session_state:
            st.session_state.val_valor_rec = 0.0

        descricao_rec = st.text_input("Descrição da Receita", value=st.session_state.val_desc_rec, placeholder="Ex: Salário, Freela, Investimento", key="rec_desc")
        valor_rec = st.number_input("Valor Recebido (R$)", min_value=0.0, value=st.session_state.val_valor_rec, step=50.0, format="%.2f", key="rec_val")
        data_rec = st.date_input("Data da Receita", value=date.today(), key="rec_data")

        if st.button("Adicionar Receita 💰", use_container_width=True, key="rec_btn_add"):
            if not descricao_rec.strip():
                st.error("Por favor, preencha a descrição da receita.")
            elif valor_rec <= 0:
                st.error("O valor da receita deve ser maior que zero.")
            else:
                try:
                    # Adiciona e persiste como transação do tipo Receita
                    st.session_state.gerenciador.adicionar_gasto(
                        descricao=descricao_rec,
                        valor=valor_rec,
                        categoria="Receita",
                        data=data_rec
                    )
                    st.session_state.gerenciador.salvar_dados(ARQUIVO_DADOS)
                    st.success("Receita adicionada e salva com sucesso!")
                    
                    # Reseta os campos
                    st.session_state.val_desc_rec = ""
                    st.session_state.val_valor_rec = 0.0
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao adicionar receita: {e}")

    with col_list:
        st.markdown(f"### 📊 Histórico de Receitas ({mes_filtro})")
        if len(receitas_filtradas) == 0:
            st.info(f"Nenhuma receita cadastrada para o mês {mes_filtro}.")
        else:
            dados_tabela_rec = []
            for r in reversed(receitas_filtradas):
                dados_tabela_rec.append({
                    "Descrição": r.descricao,
                    "Valor (R$)": f"R$ {r.valor:.2f}",
                    "Data": r.data.strftime("%d/%m/%Y")
                })

            st.dataframe(dados_tabela_rec, use_container_width=True)

            # Botão de exportação
            df_export_rec = pd.DataFrame([
                {
                    "ID": r.id,
                    "Descrição": r.descricao,
                    "Valor (R$)": r.valor,
                    "Data": r.data.strftime("%Y-%m-%d")
                }
                for r in receitas_filtradas
            ])
            csv_data_rec = df_export_rec.to_csv(index=False).encode("utf-8")
            
            st.download_button(
                label="📥 Exportar Receitas Deste Mês (CSV)",
                data=csv_data_rec,
                file_name=f"receitas_{mes_filtro.replace('/', '_')}.csv",
                mime="text/csv",
                key="export_receitas_btn",
                use_container_width=True
            )

        st.markdown("---")

        # Exclusão de Receitas
        st.markdown("### 🗑️ Excluir Receita")
        if len(receitas_filtradas) == 0:
            st.info("Nenhuma receita disponível para exclusão.")
        else:
            opcoes_exclusao_receitas = {
                r.id: f"{r.descricao} (R$ {r.valor:.2f} - {r.data.strftime('%d/%m/%Y')})"
                for r in receitas_filtradas
            }
            
            receita_selecionada_id = st.selectbox(
                "Selecione uma receita para excluir:",
                options=list(opcoes_exclusao_receitas.keys()),
                format_func=lambda x: opcoes_exclusao_receitas[x],
                key="receita_excluir_select"
            )
            
            if st.button("Excluir Receita 🗑️", use_container_width=True):
                if receita_selecionada_id:
                    if st.session_state.gerenciador.remover_gasto(receita_selecionada_id):
                        try:
                            st.session_state.gerenciador.salvar_dados(ARQUIVO_DADOS)
                            st.success("Receita excluída com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar dados após exclusão: {e}")
                    else:
                        st.error("Erro interno ao tentar remover a receita.")

else: # pagina_selecionada == "📊 Comparação Geral"
    # ----------------- PÁGINA DE COMPARAÇÃO GERAL (ANUAL) -----------------
    
    st.markdown("## 📊 Comparação Geral")
    st.markdown("Analise o histórico consolidado de gastos organizados por ano e mês, livre de filtros mensais da barra lateral.")
    
    # 1. Filtro de Ano e Seletor de Formato Unificado
    todos_gastos = st.session_state.gerenciador.gastos
    anos_disponiveis = sorted(list(set(g.data.year for g in todos_gastos)))
    ano_atual = date.today().year
    if ano_atual not in anos_disponiveis:
        anos_disponiveis.append(ano_atual)
    anos_disponiveis = sorted(anos_disponiveis)
    
    try:
        default_ano_idx = anos_disponiveis.index(ano_atual)
    except ValueError:
        default_ano_idx = len(anos_disponiveis) - 1
        
    col_ano, col_formato = st.columns([1, 2])
    with col_ano:
        ano_selecionado = st.selectbox(
            "Selecione o Ano de Análise:",
            options=anos_disponiveis,
            index=default_ano_idx
        )
    with col_formato:
        formato_visual = st.radio(
            "📊 Selecione o Formato de Visualização:",
            options=["Rosca ⭕", "Tabela 📋"],
            horizontal=True
        )
    
    # 2. Filtragem e Agrupamento (Focado em Gastos/Despesas, ignorando Receitas)
    gastos_ano = [g for g in todos_gastos if g.data.year == ano_selecionado and g.categoria != "Receita"]
    
    # Inicializa todos os 12 meses com 0.0 para garantir que todos apareçam
    resumo_mensal_ano = {m: 0.0 for m in range(1, 13)}
    for g in gastos_ano:
        resumo_mensal_ano[g.data.month] += g.valor
        
    total_acumulado_ano = sum(resumo_mensal_ano.values())
    
    # 3. Métricas de Destaque Estilo Dashboard Premium
    st.markdown("---")
    
    st.markdown(f"""
        <div class="kpi-card-highlight" style="margin-bottom: 2rem;">
            <div class="kpi-title" style="color: #00D1B2;">Total Acumulado Gasto em {ano_selecionado}</div>
            <div class="kpi-value-highlight">R$ {total_acumulado_ano:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Nomes dos meses para a Comparação Geral
    NOME_MESES = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }

    NOME_MESES_CURTO = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
        5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
        9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
    }

    # Prepara dados mensais
    df_grafico_ano = pd.DataFrame([
        {
            "Mês": NOME_MESES_CURTO[m],
            "Valor": resumo_mensal_ano[m]
        }
        for m in range(1, 13)
    ])
    
    # Prepara dados de categoria
    resumo_cat_ano = st.session_state.gerenciador.agrupar_por_categoria_ano(ano_selecionado)
    df_cat_ano = pd.DataFrame(columns=["Categoria", "Valor", "Porcentagem"])
    if resumo_cat_ano:
        linhas = [
            {"Categoria": cat, "Valor": total}
            for cat, total in resumo_cat_ano.items() if cat != "Receita"
        ]
        if linhas:
            df_cat_ano = pd.DataFrame(linhas)
            if df_cat_ano.empty or "Valor" not in df_cat_ano.columns:
                total_ano = 0.0
            else:
                total_ano = df_cat_ano["Valor"].sum()
            df_cat_ano["Porcentagem"] = (df_cat_ano["Valor"] / total_ano * 100).round(1) if total_ano > 0 else 0.0

    # 4. Renderização Condicional da Tela Inteira
    if formato_visual == "Rosca ⭕":
        # MODO VISUAL (Somente gráficos)
        
        # Linha de Cima: Histórico Mensal
        st.markdown("### 📈 Histórico de Gastos por Mês (R$)")
        chart_monthly = alt.Chart(df_grafico_ano).mark_line(
            color="#0d9488",
            point=alt.OverlayMarkDef(color="#0d9488", size=60)
        ).encode(
            x=alt.X("Mês:N", sort=list(NOME_MESES_CURTO.values()), title="Mês"),
            y=alt.Y("Valor:Q", title="Total Gasto (R$)"),
            tooltip=["Mês", alt.Tooltip("Valor", format="$,.2f", title="Total")]
        ).properties(height=300).interactive()
        st.altair_chart(chart_monthly, use_container_width=True)
        
        st.markdown("---")
        
        # Linha de Baixo: Distribuição por Categoria
        st.markdown("### 🏷️ Distribuição de Gastos por Categoria Anual")
        if not df_cat_ano.empty:
            col_l, col_c, col_r = st.columns([1, 2, 1])
            with col_c:
                st.markdown("<p style='text-align: center; font-size: 1.1rem; font-weight: 600;'>Proporção do Orçamento Anual (%)</p>", unsafe_allow_html=True)
                grafico_pizza_ano = alt.Chart(df_cat_ano).mark_arc(innerRadius=60).encode(
                    theta=alt.Theta(field="Valor", type="quantitative"),
                    color=alt.Color(
                        field="Categoria",
                        type="nominal",
                        scale=alt.Scale(scheme="tealblues")
                    ),
                    tooltip=[
                        alt.Tooltip("Categoria", title="Categoria"),
                        alt.Tooltip("Valor", format="$,.2f", title="Valor"),
                        alt.Tooltip("Porcentagem", format=".1f", title="Proporção (%)")
                    ]
                ).properties(height=320).interactive()
                st.altair_chart(grafico_pizza_ano, use_container_width=True)
        else:
            st.info("Nenhum gasto cadastrado no ano selecionado para analisar categorias.")
            
    else:
        # MODO TABELA (📋) - Esconde todos os gráficos, exibe tabelas mensais e por categoria lado a lado
        col_tab1, col_tab2 = st.columns([1, 1])
        
        with col_tab1:
            st.markdown("### 📅 Tabela Mensal de Gastos")
            df_resumo_ano = pd.DataFrame([
                {
                    "Mês": NOME_MESES[m],
                    "Total Gasto (R$)": f"R$ {resumo_mensal_ano[m]:,.2f}"
                }
                for m in range(1, 13)
            ])
            st.dataframe(df_resumo_ano, use_container_width=True, hide_index=True)
            
        with col_tab2:
            st.markdown("### 🏷️ Detalhamento por Categoria Anual")
            if not df_cat_ano.empty:
                df_resumo_cat_ex = pd.DataFrame()
                df_resumo_cat_ex["Categoria"] = df_cat_ano["Categoria"]
                df_resumo_cat_ex["Valor (R$)"] = df_cat_ano["Valor"].apply(lambda x: f"R$ {x:,.2f}")
                df_resumo_cat_ex["Porcentagem (%)"] = df_cat_ano["Porcentagem"].apply(lambda x: f"{x:.1f}%")
                st.dataframe(df_resumo_cat_ex, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum gasto cadastrado no ano selecionado para analisar categorias.")
