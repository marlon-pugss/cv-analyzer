import uuid
import streamlit as st
from helper import extract_data_analysis, read_uploaded_file
from database import AnalyzeDatabase
from ai import GroqClient
from models.resum import Resum
from models.file import File
from fpdf import FPDF  # Importando a biblioteca para gerar PDF

# Inicializando o banco de dados e o cliente AI
database = AnalyzeDatabase()
ai = GroqClient()

# Função para gerar PDF
def generate_pdf(suggestions, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Adiciona um título
    pdf.cell(200, 10, txt="Sugestões de Melhorias para o Currículo", ln=True, align='C')

    # Adiciona as sugestões ao PDF
    for suggestion in suggestions:
        pdf.cell(200, 10, txt=suggestion, ln=True)

    # Salva o PDF
    pdf_file_path = f"./{filename}.pdf"
    pdf.output(pdf_file_path)
    return pdf_file_path

# Permitir o upload de múltiplos arquivos PDF
uploaded_files = st.file_uploader("Carregue seus currículos", type=["pdf"], accept_multiple_files=True)

# Campo para a descrição da vaga
job_description = st.text_area("Descrição da Vaga", placeholder="Insira aqui a descrição da vaga...")

# Verifica se currículos foram carregados e se a descrição da vaga foi fornecida
if uploaded_files and job_description:
    # Exibe o total de currículos encontrados
    num_curriculos = len(uploaded_files)
    st.write(f"Total de currículos encontrados: {num_curriculos}")

    # Botão para continuar
    if st.button("Continuar"):
        for uploaded_file in uploaded_files:
            # Lê o conteúdo do arquivo PDF carregado
            content = read_uploaded_file(uploaded_file)

            # Gera resumo, opinião e score do currículo
            resum = ai.resume_cv(content)
            opinion = ai.generate_opinion(content, job_description)
            score = ai.generate_score(content, job_description)

            # Classifica a pontuação e gera feedback humanizado
            feedback = ai.classify_score(score)

            # Gerar sugestões de melhoria
            suggestions = ["Melhore a formatação", "Adicione experiências relevantes", "Revise as palavras-chave"]

            # Gerar PDF com sugestões
            pdf_file_path = generate_pdf(suggestions, uploaded_file.name.split('.')[0] + "_sugestoes")

            # Salva os dados processados no banco de dados
            resum_schema = Resum(
                id=str(uuid.uuid4()),
                job_id=job_description,
                content=resum,
                file=uploaded_file.name,
                opinion=opinion
            )

            file_schema = File(
                file_id=str(uuid.uuid4()),
                job_id=job_description
            )

            analyzis_schema = extract_data_analysis(resum, job_description, resum_schema.id, score)

            database.resums.insert(resum_schema.model_dump())
            database.analysis.insert(analyzis_schema.model_dump())
            database.files.insert(file_schema.model_dump())

            # Exibe as análises
            st.subheader(f"Análise do Currículo: {uploaded_file.name}")
            st.write("### Resumo:")
            st.markdown(resum)
            st.write("### Opinião Crítica:")
            st.markdown(opinion)
            st.write("### Pontuação:")
            st.write(f"Pontuação Final: {score}")
            st.write("### Feedback:")
            st.write(feedback)

            # Link para download do PDF
            st.download_button(label="Baixar Sugestões de Melhoria", data=open(pdf_file_path, "rb"), file_name=f"{uploaded_file.name.split('.')[0]}_sugestoes.pdf")

else:
    # Mensagem de aviso caso não haja arquivos ou descrição
    st.warning("⚠️ Nenhum currículo carregado ou descrição da vaga fornecida.")
