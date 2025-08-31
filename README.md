# 智能法律助理（Intelligent Legal Assistant）

本项目是一个基于 FastAPI + LangChain + LangGraph + RAG 的智能法律问答系统，支持中英文、文档上传、法律检索与生成，适合部署在 Hugging Face Spaces。

## 主要特性
- 支持中英文法律问答
- 支持上传合同 PDF/图片自动解析
- 支持多法律领域知识库（RAG）
- 基于 LangGraph 的多步推理与流程编排
- ChatGPT 风格前端 UI
- 可一键 Docker 部署


### 本地构建与运行

```bash
docker build -t legal-assistant .
docker run -p 7860:7860 legal-assistant
```

访问 http://localhost:7860 即可体验。

## 目录结构
- `my_project/` 主要代码与资源
- `my_project/templates/chat.html` 前端页面
- `my_project/requirements.txt` 依赖
- `my_project/Dockerfile` Docker 构建文件

## 注意事项
- 向量库、上传文件等默认存储在项目目录下，首次部署建议重建向量库
- 如需自定义知识库，请将文档放入 `my_project/laws/` 目录

---

# Intelligent Legal Assistant

This project is an intelligent legal Q&A system based on FastAPI + LangChain + LangGraph + RAG, supporting both Chinese and English, document upload, legal retrieval and generation, and is suitable for deployment on Hugging Face Spaces.

## Features
- Bilingual (Chinese/English) legal Q&A
- Upload contract PDF/images for automatic parsing
- Multi-domain legal knowledge base (RAG)
- Multi-step reasoning and workflow orchestration powered by LangGraph
- ChatGPT-style frontend UI
- One-click Docker deployment

## Quick Start (Hugging Face Spaces Docker)

1. **Upload all project files to your Hugging Face Space and select Docker mode**
2. **Builds automatically, no manual commands needed**
3. Listens on port 7860 by default

### Local Build & Run

```bash
docker build -t legal-assistant .
docker run -p 7860:7860 legal-assistant
```

Visit http://localhost:7860 to try it out.

## Directory Structure
- `my_project/` main code and resources
- `my_project/templates/chat.html` frontend page
- `my_project/requirements.txt` dependencies
- `my_project/Dockerfile` Docker build file

## Notes
- Vectorstore, uploaded files, etc. are stored in the project directory by default. For first deployment, it is recommended to rebuild the vectorstore.
- To customize the knowledge base, put your documents in the `my_project/laws/` directory.

---

For issues or contributions, please open an issue or PR on GitHub. 
