import os
import sys
from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
#from pydantic import BaseModel
from langchain_unstructured import UnstructuredLoader
from agent_with_tools import llm
from PIL import Image
import pytesseract
import cv2
import numpy as np

from rag_tool import retrieve_docs
from agent_with_tools import graph  # now using LangGraph workflow
from mcp_planner import planner
from doc_generator import generate_contract_doc
from db_tool import init_db, insert_contract, DB_PATH
#from langchain_openai import ChatOpenAI
from unstructured.partition.auto import partition
# 保存到数据库
import sqlite3



#DB_PATH = os.path.join(os.path.dirname(__file__), "uploads/contracts.db")

# 初始化数据库
init_db()

def summarize_contract(text):
    prompt = f"""
请阅读以下租赁合同内容，并提取关键信息（如甲方、乙方、租金、租赁地址、租赁期限等），并简要总结主要条款：

合同内容如下：
{text[:]}
"""
    # 说明：通常一次 prompt 4000 字左右（太长要分块）。
    response = llm.invoke([
        {"role": "system", "content": "你是文你是法律文档分析助手，善于总结合同内容。"},
        {"role": "user", "content": prompt}
    ])
    return response.content.strip()

# 🔧 ensure proper path for relative imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()
templates = Jinja2Templates(directory="templates")

#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

#EPROCESSED_FOLDER = "processed"
#os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def extract_text(file_path, filename):
    ext = os.path.splitext(filename)[-1].lower()
    if ext in ['.jpg', '.jpeg', '.png']:
        # OCR for image
        #img = Image.open(file_path).convert('L')
        # 用opencv读图
        image = cv2.imread(file_path)
        # 灰度化
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 二值化增强
        _, threshed = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # 保存处理后的图片
        cv2.imwrite(file_path, threshed)
        # PIL对象
        img = Image.fromarray(threshed)
        #enhancer = ImageEnhance.Contrast(img)
        #img = enhancer.enhance(2)           # improving the contrast
        #img = img.point(lambda x:0 if x < 180 else 255, '1')   # Simple two value
        custom_config = r'--oem 3 --psm 6'     # Normal configure LSTM mode
        text = pytesseract.image_to_string(img, lang='chi_sim', config=custom_config)
    elif ext in ['.pdf', '.docx', '.doc']:
        # Unstructured for PDF/Word
        elements = partition(filename=file_path)
        text = "\n".join(str(el) for el in elements)
    else:
        raise ValueError("Unsupported file type")
    return text

# optional if you have CSS/JS
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# GET: render chat page
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

# POST: main chat logic
@app.post("/", response_class=PlainTextResponse)
async def chat(user_input: str = Form(...)):
    if not user_input:
        return "请输入内容！"

    user_input = user_input.strip()

    if planner.contract_ready:
        if "下载" in user_input:
            filename = generate_contract_doc(
                planner.state.get("landlord", "未填写"),
                planner.state.get("tenant", "未填写"),
                planner.state.get("location", "未填写"),
                planner.state.get("rent", "未填写"),
                planner.state.get("duration", "未填写")
            )
            planner.contract_ready = False
            planner.contract_todo = False
            planner.reset()
            return FileResponse(filename, media_type='application/octet-stream', filename=os.path.basename(filename))
        else:
            planner.contract_ready = False
            planner.contract_todo = False
            planner.reset()
            return "好的，合同未下载，如需重新生成，请重新开始。"

    if planner.contract_todo:
        planner.update(user_input)
        if planner.is_complete():
            contract_text = planner.build_contract_request()
            planner.contract_ready = True
            planner.contract_todo = False
            return contract_text + "\n\n如果您确认无误，请回复【下载】，我将提供下载链接。"
        else:
            return planner.prompt_next()

    #用 LangGraph 调用意图识别 + 工具链
    result = await graph.ainvoke({"input": user_input})
    #result = await graph.ainvoke({"message": user_input})
    return result.get("output", "无法获取输出。")


# POST: file upload
@app.post("/upload", response_class=HTMLResponse)
async def upload_file(file: UploadFile = File(...)):
    if file.filename != '':
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        original__filename = "original_" + file.filename
        original__path = os.path.join(UPLOAD_FOLDER, original__filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        print("file_path:", file_path)
        print("processed_path:", original__path)
        print("file exists?", os.path.exists(file_path), os.path.getsize(file_path) if os.path.exists(file_path) else "不存在")

        #loader = UnstructuredLoader(file_path)
        #docs = loader.load()
        #text = docs[0].page_content
       
        try:
            text = extract_text(file_path, file.filename)
        except Exception as e:
            return f"提取文本失败: {e}"


        # 调用 summarize_contract(text) 实现总结
        summary = summarize_contract(text)
        
        # 用 insert_contract 存储到 SQLite
        insert_contract(file.filename, text, summary)
        
        return f"{text}<h2>提取总结：</h2><pre>{summary}</pre>"
        
        # 返回网页包含原图、处理后图和识别文本
        #return f"""
        #<h2>原图：</h2>
        #<img src="/uploads/{os.path.basename(original__path)}" width="400"><br>
        #<h2>处理后图：</h2>
        #<img src="/uploads/{os.path.basename(file_path)}" width="400"><br>
        #<h2>图片OCR识别结果：</h2>
        #<pre>{text}</pre>
        #"""

        #return f"<h2>File content:</h2><pre>{text[:1000]}</pre>"
        #return f"<h2>File content:</h2><pre>{text}</pre>"
        #return text

    return "No file uploaded."

