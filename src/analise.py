import uuid
from helper import extract_data_analysis, get_pdf_paths, read_uploaded_file
from database import AnalyzeDatabase
from ai import GroqClient
from models.resum import Resum
from models.file import File

database = AnalyzeDatabase()
ai = GroqClient()
job = database.get_job_by_name('Vaga de Gestor Comercial de B2B')

cv_paths = get_pdf_paths(directory='/Users/fluencyacademy/projeto-pessoal/src/drive/curriculos')

for path in cv_paths:
    content = read_uploaded_file(path)
    print(content)
    resum = ai.resume_cv(content)
    print(resum)
    opinion = ai.generate_opinion(content, job)
    print(opinion)
    score = ai.generate_score(content, job)
    print(score)

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

    analyzis_schema = extract_data_analysis(resum,job.get('id'), resum_schema.id, score)

    database.resums.insert(resum_schema.model_dump())
    database.analysis.insert(analyzis_schema.model_dump())
    database.files.insert(file_schema.model_dump())


