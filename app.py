import streamlit as st
import pandas as pd
import os
from PIL import Image
from datetime import datetime
import google.generativeai as genai

# Configuração da página
st.set_page_config(page_title="Meu Livro de Receitas", page_icon="🍳", layout="wide")

# Configuração da IA (Gemini)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    modelo_ia = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    modelo_ia = None
    st.sidebar.warning("Chave de API do Gemini não configurada.")

# Variáveis de sessão para preenchimento automático
if "ingredientes_ia" not in st.session_state:
    st.session_state.ingredientes_ia = ""
if "preparo_ia" not in st.session_state:
    st.session_state.preparo_ia = ""

# Pastas e arquivos
PASTA_IMAGENS = "imagens_receitas"
ARQUIVO_DADOS = "minhas_receitas.csv"

if not os.path.exists(PASTA_IMAGENS):
    os.makedirs(PASTA_IMAGENS)

st.title("🍳 Meu Livro de Receitas")

aba_cadastrar, aba_visualizar = st.tabs(["Cadastrar Nova Receita", "Minhas Receitas"])

# ABA 1: CADASTRO
with aba_cadastrar:
    st.header("Adicionar Receita")
    
    nome_receita = st.text_input("Nome do Prato (ex: Hambúrguer Artesanal, Lamen, etc.)")
    
    # Text areas puxando o valor da session_state
    ingredientes = st.text_area("Ingredientes", value=st.session_state.ingredientes_ia, height=150)
    modo_preparo = st.text_area("Modo de Preparo", value=st.session_state.preparo_ia, height=150)
    
    st.subheader("Foto do Prato")
    metodo_foto = st.radio("Como deseja inserir a foto?", ["Tirar Foto agora", "Fazer Upload de arquivo"])
    
    foto = st.camera_input("Tire uma foto do prato") if metodo_foto == "Tirar Foto agora" else st.file_uploader("Selecione a imagem", type=["jpg", "jpeg", "png"])

    # NOVO: Botão da Inteligência Artificial
    if foto and modelo_ia:
        if st.button("✨ Gerar Receita com IA (Mágica!)"):
            with st.spinner("Analisando o prato e escrevendo a receita..."):
                img = Image.open(foto)
                
                # Pedindo para a IA analisar a imagem
                prompt_ingredientes = "Liste apenas os prováveis ingredientes da comida nesta foto, um por linha, sem introduções."
                prompt_preparo = "Crie um modo de preparo passo a passo provável para a comida da foto, de forma direta."
                
                try:
                    res_ingredientes = modelo_ia.generate_content([prompt_ingredientes, img])
                    res_preparo = modelo_ia.generate_content([prompt_preparo, img])
                    
                    # Atualiza os campos na tela
                    st.session_state.ingredientes_ia = res_ingredientes.text
                    st.session_state.preparo_ia = res_preparo.text
                    st.rerun() # Recarrega a tela com os textos preenchidos
                except Exception as e:
                    st.error("Erro ao conectar com a IA. Tente novamente.")

    if st.button("Salvar Receita", type="primary"):
        if nome_receita and foto:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho_imagem = f"{PASTA_IMAGENS}/img_{timestamp}.jpg"
            
            Image.open(foto).save(caminho_imagem)
            
            nova_receita = pd.DataFrame([{
                "Data": datetime.now().strftime("%d/%m/%Y"),
                "Nome": nome_receita,
                "Ingredientes": ingredientes,
                "Preparo": modo_preparo,
                "Caminho_Imagem": caminho_imagem
            }])
            
            if os.path.exists(ARQUIVO_DADOS):
                df_receitas = pd.read_csv(ARQUIVO_DADOS)
                df_receitas = pd.concat([df_receitas, nova_receita], ignore_index=True)
            else:
                df_receitas = nova_receita
                
            df_receitas.to_csv(ARQUIVO_DADOS, index=False)
            
            # Limpa a tela após salvar
            st.session_state.ingredientes_ia = ""
            st.session_state.preparo_ia = ""
            st.success(f"Receita salva com sucesso!")
        else:
            st.error("Preencha o nome da receita e inclua uma foto.")

# ABA 2: VISUALIZAÇÃO
with aba_visualizar:
    st.header("Minhas Receitas Salvas")
    
    if os.path.exists(ARQUIVO_DADOS):
        df_receitas = pd.read_csv(ARQUIVO_DADOS).iloc[::-1]
        
        for index, row in df_receitas.iterrows():
            with st.expander(f"🍽️ {row['Nome']} ({row['Data']})"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    if pd.notna(row["Caminho_Imagem"]) and os.path.exists(row["Caminho_Imagem"]):
                        st.image(row["Caminho_Imagem"], use_container_width=True)
                with col2:
                    st.markdown("### Ingredientes")
                    st.write(row["Ingredientes"])
                    st.markdown("### Modo de Preparo")
                    st.write(row["Preparo"])
