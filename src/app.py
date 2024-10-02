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
job = database.get_job_by_name('Vaga de Gestor Comercial de B2B')

# Permitir o upload de múltiplos arquivos PDF
uploaded_files = st.file_uploader("Carregue seus currículos", type=["pdf"], accept_multiple_files=True)

# Exibe o total de currículos encontrados
if uploaded_files:
    num_curriculos = len(uploaded_files)
    st.write(f"Total de currículos encontrados: {num_curriculos}")

    for uploaded_file in uploaded_files:
        content = read_uploaded_file(uploaded_file)
        st.write(content)  # Exibe o conteúdo do currículo
        resum = ai.resume_cv(content)
        st.write(resum)  # Exibe o resumo do currículo
        opinion = ai.generate_opinion(content, job)
        st.write(opinion)  # Exibe a opinião da IA
        score = ai.generate_score(content, job)
        st.write(score)  # Exibe o score do currículo

        # Salva os dados processados no banco de dados
        resum_schema = Resum(
            id=str(uuid.uuid4()),
            job_id=job.get('id'),
            content=resum,
            file=uploaded_file.name,
            opinion=opinion
        )

        file_schema = File(
            file_id=str(uuid.uuid4()),
            job_id=job.get('id')
        )

        analyzis_schema = extract_data_analysis(resum, job.get('id'), resum_schema.id, score)

        database.resums.insert(resum_schema.model_dump())
        database.analysis.insert(analyzis_schema.model_dump())
        database.files.insert(file_schema.model_dump())

else:
    st.warning("⚠️ Nenhum currículo carregado.")
