import os
import uuid
import streamlit as st
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from helper import extract_data_analysis, get_pdf_paths, read_uploaded_file
from database import AnalyzeDatabase
from ai import GroqClient
from models.resum import Resum
from models.file import File

# Token e credenciais
token_info = {
    "token": "ya29.a0AcM612yH9v5F3JGfFKfV4F6ENxpmB-LBeficerv0NpOrxkvb7Qd7Lv5GbLdhjZFc9QDGk2aSPW7VJBv_U8EUloEr-yYqYAWPKZWm-KCv1VGjtCITDC67Zf0vClvCGCQ9KZWfAssyG_LMubg1U-f97h9BqK4JvgtBjYEICg5JaCgYKAUYSARISFQHGX2MiMRJJ9qGpoh2qH0AmU6gUog0175",
    "refresh_token": "1//0hCKdupjTIpuuCgYIARAAGBESNwF-L9Ir50uGLBJ-WQVTBOUWwmdXPdqBPZvPS9nzltXxYD-LHb4rnIDk_fV6W0PaCgEoA8aRh0c",
    "client_id": "912425965095-flp8g1i5anr6gbq5mts4km74254u90pj.apps.googleusercontent.com",
    "client_secret": "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",
    "token_uri": "https://oauth2.googleapis.com/token",
    "scopes": [
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
    ],
    "expiry": "2024-09-27T01:43:57.417822Z"
}

# Cria um objeto de credenciais a partir do dicionário
creds = Credentials(
    token=token_info["token"],
    refresh_token=token_info["refresh_token"],
    token_uri=token_info["token_uri"],
    client_id=token_info["client_id"],
    client_secret=token_info["client_secret"],
    scopes=token_info["scopes"]
)

# Construa o serviço da API Google Drive
service = build('drive', 'v3', credentials=creds)

# Inicializa a base de dados e a IA
database = AnalyzeDatabase()
ai = GroqClient()

# Escolhe a vaga de interesse
job = database.get_job_by_name('Vaga de Gestor Comercial de B2B')

# Configura a página do Streamlit
st.set_page_config(layout="wide", page_title="Análise de Currículos", page_icon=":file_folder:")

# Exibe o título com um estilo
st.title("🔍 Análise de Currículos para a Vaga: **Gestor Comercial de B2B**")

# Caminho relativo para o diretório de currículos
directory = 'src/drive/curriculos'

# Pega o caminho dos currículos no diretório especificado
try:
    cv_paths = get_pdf_paths(directory=directory)
    
    # Exibe quantos currículos foram encontrados
    num_curriculos = len(cv_paths)
    st.write(f"Total de currículos encontrados: {num_curriculos}")

except FileNotFoundError:
    st.error(f"O diretório '{directory}' não foi encontrado. Verifique se o caminho está correto.")

# Contar o número de currículos encontrados
num_curriculos = len(cv_paths)
st.write(f"📄 Número de currículos encontrados: {num_curriculos}")

# Lista para armazenar os scores dos candidatos
scores = []

# Verifica se há currículos no diretório
if not cv_paths:
    st.warning("⚠️ Nenhum currículo encontrado no diretório especificado.")
else:
    # Cria um botão para iniciar a análise
    if st.button("Iniciar Análise dos Currículos"):
        # Exibe um GIF ou imagem enquanto os dados estão carregando
        with st.spinner("Analisando currículos... ⏳"):
            # Processa cada currículo
            for path in cv_paths:
                # Lê o conteúdo do arquivo de currículo
                content = read_uploaded_file(path)

                # Exibe as informações do currículo
                with st.expander(f"Currículo: {path}", expanded=True):
                    # Extrai o nome do candidato (presumindo que o nome esteja na primeira linha do conteúdo)
                    name = content.split('\n')[0]  # Modifique conforme necessário para obter o nome corretamente

                    # Chama o método para extrair as informações do candidato
                    candidate_summary = ai.extract_candidate_summary(content)

                    # Verifica se candidate_summary não é None e é um dicionário
                    if candidate_summary is not None:
                        # Usa .get() para acessar 'nome', evitando KeyError
                        nome = candidate_summary.get('nome', 'Não disponível')
                        st.write(f"**Nome:** {nome}")
                    else:
                        st.write("Não foi possível gerar o resumo do candidato.")

                    # Gera o resumo do currículo usando a IA
                    resum = ai.resume_cv(content)

                    # Gera a opinião da IA
                    opinion = ai.generate_opinion(content, job)
                    st.write("### Opinião da IA:")
                    st.text(opinion)

                    # Gera o score do currículo em relação à vaga
                    score = ai.generate_score(content, job)
                    st.write("### Score do Currículo:")
                    st.text(score)

                    # Armazena o score para o gráfico
                    scores.append(score)

                    # Gera o comentário baseado no score
                    score_comment = ai.get_score_comment(score)
                    st.write("### Comentário sobre a Pontuação:")
                    st.text(score_comment)

                    # Salva os dados processados no banco de dados
                    resum_schema = Resum(
                        id=str(uuid.uuid4()),
                        job_id=job.get('id'),
                        content=resum,
                        file=str(path),
                        opinion=opinion
                    )

                    file_schema = File(
                        file_id=str(uuid.uuid4()),
                        job_id=job.get('id')
                    )

                    analyzis_schema = extract_data_analysis(resum, job.get('id'), resum_schema.id, score)

                    # Insere os dados no banco de dados
                    database.resums.insert(resum_schema.model_dump())
                    database.analysis.insert(analyzis_schema.model_dump())
                    database.files.insert(file_schema.model_dump())

                    # Exibe uma separação entre currículos
                    st.markdown("---")

            # Cria um gráfico após a análise de todos os currículos
            if scores:
                score_ranges = {'Abaixo de 7': 0, 'Entre 7 e 9': 0, '9 ou mais': 0}
                for score in scores:
                    if score < 7:
                        score_ranges['Abaixo de 7'] += 1
                    elif 7 <= score < 9:
                        score_ranges['Entre 7 e 9'] += 1
                    else:  # score >= 9
                        score_ranges['9 ou mais'] += 1

                # Gera o gráfico
                fig, ax = plt.subplots()
                ax.bar(score_ranges.keys(), score_ranges.values(), color=['red', 'orange', 'green'])
                ax.set_xlabel('Faixa de Pontuação')
                ax.set_ylabel('Número de Candidatos')
                ax.set_title('Ranking dos Candidatos por Faixa de Pontuação')
                st.pyplot(fig)  # Exibe o gráfico no Streamlit
