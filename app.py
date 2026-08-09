import streamlit as st
import pandas as pd
import os
from PIL import Image
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Meu Livro de Receitas", page_icon="🍳", layout="wide")

# Cria as pastas para salvar os dados se não existirem
PASTA_IMAGENS = "imagens_receitas"
ARQUIVO_DADOS = "minhas_receitas.csv"

if not os.path.exists(PASTA_IMAGENS):
    os.makedirs(PASTA_IMAGENS)

# Título do App
st.title("🍳 Meu Livro de Receitas")

# Criando abas de navegação
aba_cadastrar, aba_visualizar = st.tabs(["Cadastrar Nova Receita", "Minhas Receitas"])

# ABA 1: CADASTRO
with aba_cadastrar:
    st.header("Adicionar Receita")
    
    nome_receita = st.text_input("Nome do Prato (ex: Hambúrguer Artesanal, Lamen, etc.)")
    ingredientes = st.text_area("Ingredientes")
    modo_preparo = st.text_area("Modo de Preparo")
    
    st.subheader("Foto do Prato")
    metodo_foto = st.radio("Como deseja inserir a foto?", ["Tirar Foto agora", "Fazer Upload de arquivo"])
    
    foto = None
    if metodo_foto == "Tirar Foto agora":
        # Ativa a câmera do dispositivo
        foto = st.camera_input("Tire uma foto do seu prato finalizado")
    else:
        # Abre o explorador de arquivos
        foto = st.file_uploader("Selecione a imagem", type=["jpg", "jpeg", "png"])

    if st.button("Salvar Receita", type="primary"):
        if nome_receita and foto:
            # 1. Salvar a imagem física na pasta
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho_imagem = f"{PASTA_IMAGENS}/img_{timestamp}.jpg"
            
            img = Image.open(foto)
            img.save(caminho_imagem)
            
            # 2. Salvar os dados no CSV
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
            
            st.success(f"Receita de '{nome_receita}' salva com sucesso!")
        else:
            st.error("Por favor, preencha o nome da receita e inclua uma foto.")

# ABA 2: VISUALIZAÇÃO
with aba_visualizar:
    st.header("Minhas Receitas Salvas")
    
    if os.path.exists(ARQUIVO_DADOS):
        df_receitas = pd.read_csv(ARQUIVO_DADOS)
        
        # Inverte o dataframe para mostrar as mais recentes primeiro
        df_receitas = df_receitas.iloc[::-1]
        
        for index, row in df_receitas.iterrows():
            with st.expander(f"🍽️ {row['Nome']} (Adicionada em {row['Data']})"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if pd.notna(row["Caminho_Imagem"]) and os.path.exists(row["Caminho_Imagem"]):
                        st.image(row["Caminho_Imagem"], use_container_width=True)
                    else:
                        st.warning("Imagem não encontrada.")
                        
                with col2:
                    st.markdown("### Ingredientes")
                    st.write(row["Ingredientes"])
                    
                    st.markdown("### Modo de Preparo")
                    st.write(row["Preparo"])
    else:
        st.info("Nenhuma receita cadastrada ainda. Vá para a aba 'Cadastrar Nova Receita' para começar!")
