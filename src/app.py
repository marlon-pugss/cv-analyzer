import os
import streamlit as st
import uuid
from your_database_module import AnalyzeDatabase  # Altere para o módulo correto
from your_ai_module import GroqClient  # Altere para o módulo correto

# Inicializa a base de dados e a IA
database = AnalyzeDatabase()
ai = GroqClient()

# Caminho relativo para o diretório de currículos
directory = 'src/drive/curriculos'

# Função para obter os caminhos dos PDFs
def get_pdf_paths(directory):
    return [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.pdf')]

# Pega o caminho dos currículos no diretório especificado
cv_paths = get_pdf_paths(directory)

# Exibe quantos currículos foram encontrados
num_curriculos = len(cv_paths)
st.write(f"Total de currículos encontrados: {num_curriculos}")

# Lista para armazenar os scores dos candidatos
scores = []

# Verifica se há currículos no diretório
if num_curriculos > 0:
    # Cria um botão para iniciar a análise
    if st.button("Iniciar Análise dos Currículos"):
        # Exibe um GIF ou imagem enquanto os dados estão carregando
        with st.spinner("Analisando currículos... ⏳"):
            # Processa cada currículo
            for path in cv_paths:
                # Lê o conteúdo do arquivo de currículo
                with open(path, 'r') as file:
                    content = file.read()

                # Chama o método para extrair as informações do candidato
                candidate_summary = ai.extract_candidate_summary(content)
                
                # Gera a opinião da IA
                opinion = ai.generate_opinion(content)
                
                # Gera o score do currículo
                score = ai.generate_score(content)
                
                # Armazena o score para o gráfico
                scores.append(score)

                # Exibe as análises
                st.subheader(f"Análise do Currículo: {os.path.basename(path)}")
                st.write(f"**Opinião da IA:** {opinion}")
                st.write(f"**Score do Currículo:** {score}")
                st.markdown("---")
                
        # Gera um resumo das análises
        if scores:
            avg_score = sum(scores) / len(scores)
            st.write(f"**Score médio dos currículos:** {avg_score:.2f}")

else:
    st.warning("⚠️ Nenhum currículo encontrado no diretório especificado.")
