import uuid
import streamlit as st
from helper import extract_data_analysis, read_uploaded_file
from database import AnalyzeDatabase
from ai import GroqClient
from models.resum import Resum
from models.file import File

# Inicializando o banco de dados e o cliente AI
database = AnalyzeDatabase()
ai = GroqClient()

# Permitir o upload de múltiplos arquivos PDF
uploaded_files = st.file_uploader("Carregue seus currículos", type=["pdf"], accept_multiple_files=True)

# Campo para a descrição da vaga
job_description = st.text_area("Descrição da Vaga", placeholder="Insira aqui a descrição da vaga...")

# Exibe o total de currículos encontrados
if uploaded_files:
    num_curriculos = len(uploaded_files)
    st.write(f"Total de currículos encontrados: {num_curriculos}")

    for uploaded_file in uploaded_files:
        # Lê o conteúdo do arquivo PDF carregado
        content = read_uploaded_file(uploaded_file)

        # Verificar se o currículo e a descrição da vaga não estão vazios
        if not content or not job_description:
            raise ValueError("O currículo e a descrição da vaga não podem ser vazios.")

        # Gera resumo, opinião e score do currículo
        resum = ai.resume_cv(content)

        opinion = ai.generate_opinion(content, job_description)  # Passando a descrição da vaga
        score = ai.generate_score(content, job_description)  # Passando a descrição da vaga

        # Salva os dados processados no banco de dados
        resum_schema = Resum(
            id=str(uuid.uuid4()),
            job_id=job_description,  # Caso você tenha um ID de trabalho correspondente
            content=resum,
            file=uploaded_file.name,
            opinion=opinion
        )

        file_schema = File(
            file_id=str(uuid.uuid4()),
            job_id=job_description  # Caso você tenha um ID de trabalho correspondente
        )

        analyzis_schema = extract_data_analysis(resum, job_description, resum_schema.id, score)

        database.resums.insert(resum_schema.model_dump())
        database.analysis.insert(analyzis_schema.model_dump())
        database.files.insert(file_schema.model_dump())

else:
    st.warning("⚠️ Nenhum currículo carregado.")
