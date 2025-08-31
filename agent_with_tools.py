import os
from langchain_openai import ChatOpenAI
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_node import ToolNode
from rag_tool import load_vectorstore, retrieve_docs
from langchain.tools import Tool

class AgentState(TypedDict):
    input: str
    output: Optional[str]
    message: str    # 允许 message 字段动态添加 (Allow dynamic addition of the 'message' field)


# 加载向量库 (Load the vector store)
BASE_DIR = os.path.dirname(__file__)
db = load_vectorstore(os.path.join(BASE_DIR, "my_vectorstore_path"))

#llm = ChatOpenAI(temperature=0, model="deepseek-chat")

#  定义RAG工具 (Define the RAG tool)
def rag_tool_func(query: str) -> str:
    docs = retrieve_docs(query, db, top_k=3)
    return "\n\n".join([doc.page_content for doc in docs])

"""
# 创建工具列表 (Create tool list)
tools = [
    Tool(
        name="LegalDocumentRetriever",
        func=rag_tool_func,
        description="Retrieve legal content for Chinese rental law."
    )
]
"""

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    
    temperature=0,
)

# 创建 LangGraph 流程图 (Create LangGraph workflow)
builder = StateGraph(AgentState)

# 工具节点 (Tool node)
#tool_node = ToolNode(tools=tools)

#builder.add_node("tool", tool_node)


# LLM 执行节点 (LLM execution node)
def chat_node(state):
    user_input = state.get("input", "")
    print("chat_node收到:", state)  # chat_node received:
    answer = rag_tool_func(user_input)
    system_prompt = f"""
你是一个专业的法律助理（You are a professional legal assistant），请根据用户输入的语言（中文或英文）输出相同语言的意图类别（Output the intent category in the same language as the user's input: Chinese or English）。

请只用与用户输入相同的语言作答，不要中英混合。
Please answer only in the same language as the user's input, do not mix Chinese and English.

分类标准 (Classification criteria)：
- 如果用户在提供合同相关信息（如甲方、乙方、合同内容等），请回复："填写合同"（If the user is providing contract-related information, reply: 'Fill in contract'）
- 如果用户在提问与法律相关的问题，请回复："提问法律"（If the user is asking a legal question, reply: 'Legal question'）
- 如果用户问的是与法律无关的话题，请回复："抱歉，我不能回答法律以外的问题"（If the user's question is unrelated to law, reply: 'Sorry, I cannot answer questions outside the legal domain.'）

注意：output 只能是上述三种类别之一，且必须与用户输入语言一致。
(Note: output must be one of the three categories above, and must match the user's input language.)
"""

    # 直接用llm.invoke()，符合langchain新版规范 (Directly use llm.invoke(), compliant with the new langchain standard)
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ])

    intent = response.content.strip().lower()  # 提取答案 (Extract answer)

    if intent in ["填写合同", "fill in contract"]:
        print("chat_node返回:", {"output": response.content.strip()})  # chat_node returns:
        return {"output": response.content.strip()} # Return intent in user's language
    elif intent in ["提问法律", "legal question"]:
        prompt = (
            f"用户问题 (User question)：{user_input}\n"
            f"相关法律条文 (Relevant legal articles)：{answer}\n"
            "请用与用户输入相同的语言（中文或英文）简明回答用户问题。"
            "(Please answer the user's question concisely in the same language as the user's input, either Chinese or English.)"
        )
        response2 = llm.invoke([
            {"role": "system", "content": "你是专业法律助理（You are a professional legal assistant），请结合法律条文为用户解答（Please answer the user's question based on the legal articles）."},
            {"role": "user", "content": prompt}
        ])
        final_answer = response2.content.strip()
        print("chat_node返回:", {"output": final_answer})  # chat_node returns:
        return {"output": final_answer}
    else:
        print("chat_node返回:", {"output": response.content.strip()})  # chat_node returns:
        return {"output": response.content.strip()}
    
builder.add_node("chat", chat_node)

# 链接节点 (Link nodes)
builder.set_entry_point("chat")

"""
# 用条件分支跳转 (Conditional branching)
def chat_to_next_node(state):
    # 如果返回带 next 字段（即“提问法律”），跳到 tool (If 'next' field is returned, jump to tool)
    if "next" in state:
        return state["next"]
    else:
        return END
"""
    

#builder.add_conditional_edges("chat", chat_to_next_node)
#builder.add_edge("tool", END)
builder.add_edge("chat", END)

# 编译图 (Compile the graph)
graph = builder.compile()
