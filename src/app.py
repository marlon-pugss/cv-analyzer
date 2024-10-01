import uuid
import streamlit as st
from helper import extract_data_analysis, get_pdf_paths, read_uploaded_file
from database import AnalyzeDatabase
from ai import GroqClient
from models.resum import Resum
from models.file import File
import matplotlib.pyplot as plt

# Inicializa a base de dados e a IA
database = AnalyzeDatabase()
ai = GroqClient()

# Escolhe a vaga de interesse
job = database.get_job_by_name('Vaga de Gestor Comercial de B2B')

# Configura a página do Streamlit
st.set_page_config(layout="wide", page_title="Análise de Currículos", page_icon=":file_folder:")

# Exibe o título com um estilo
st.title("🔍 Análise de Currículos para a Vaga: **Gestor Comercial de B2B**")

# Pega o caminho dos currículos no diretório especificado
cv_paths = get_pdf_paths(directory='/Users/fluencyacademy/projeto-pessoal/src/drive/curriculos')

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
