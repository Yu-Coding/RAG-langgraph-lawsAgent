from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader, UnstructuredWordDocumentLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, END
import os
import glob

# ✅ 配置常量
BASE_DIR = os.path.dirname(__file__)
VECTORSTORE_PATH = os.path.join(BASE_DIR, "my_vectorstore_path")
#SOURCE_TEXT_FILE = os.path.join(BASE_DIR, "china_rental_laws.txt")
SOURCE_TEXT_FILE = os.path.join(BASE_DIR, "laws")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


# ✅ 创建向量库
# 支持传入文件夹或单个文件

def create_vectorstore_from_file(file_path):
    all_documents = []
    if os.path.isdir(file_path):
        # 处理文件夹，加载所有 docx, doc, txt 文件
        for ext in ('*.docx', '*.doc', '*.txt'):
            for fname in glob.glob(os.path.join(file_path, ext)):
                if fname.endswith(('.docx', '.doc')):
                    loader = UnstructuredWordDocumentLoader(fname)
                else:
                    loader = TextLoader(fname, encoding="utf-8")
                documents = loader.load()
                all_documents.extend(documents)
    else:
        # 单文件
        if file_path.endswith(('.docx', '.doc')):
            loader = UnstructuredWordDocumentLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()
        all_documents.extend(documents)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "；", "，"]
    )
    split_docs = splitter.split_documents(all_documents)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL) 
    
    db = FAISS.from_documents(split_docs, embeddings)
    db.save_local(VECTORSTORE_PATH)
    print("向量库已成功创建并保存到:", VECTORSTORE_PATH)
    return db

# ✅ 加载向量库（自动修复维度不匹配）
def load_vectorstore(db_path, file_path=SOURCE_TEXT_FILE):
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    try:
        db = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
        return db
    except AssertionError as e:
        print("⚠️ 向量维度不匹配，正在重新生成向量库...")
        return create_vectorstore_from_file(file_path)

# ✅ 文档检索
def retrieve_docs(query, vectorstore, top_k=3):
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
    docs = retriever.get_relevant_documents(query)
    print("Top retrieved content:")
    for doc in docs:
        print(doc.page_content[:200])
    return docs