from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def preparar_documentos(ruta_pdf):
    # 1. Leer PDF
    loader = PyPDFLoader(ruta_pdf)
    paginas = loader.load()
    
    # 2. Chunking

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=350,
        chunk_overlap=0,
        separators=[
        r"\n(?=\d+\\.)",     # Tu expresión regular inteligente
        "\n\n", 
        "\n", 
        " "
    ], 
        is_separator_regex=True
    )
    
    # 3. Cortar texto en fragmentos
    chunks = splitter.split_documents(paginas)
    
    print(f"Documento procesado: {len(chunks)} fragmentos creados.")
    return chunks