ROUTE_RULES = [
    (["研究", "分析", "调查", "深度", "调研"], "deep_research_agent"),
    (["天气", "时间", "订单"], "general_agent"),
]


def route(message: str) -> str:
    msg_lower = (message or "").strip().lower()
    for keywords, agent_id in ROUTE_RULES:
        if any(kw in msg_lower for kw in keywords):
            return agent_id
    
    # 调用embedding model
    from openai import OpenAI
    import os
    import dotenv
    dotenv.load_dotenv()
    import numpy as np
    ebd_api_key = os.getenv("EMBEDDING_API_KEY")
    ebd_base_url = os.getenv("EMBEDDING_BASE_URL")
    # 计算query embedding
    EMBEDDING_RULES=[
        ("这是一个深度研究智能体，专门处理需要多步推理、联网搜索、信息综合和长文本生成的任务。适用于撰写研究报告、市场分析、技术调查、学术综述、趋势研判等需要深入调研的场景。输入通常为复杂问题，要求全面、准确且有依据的回答。",
        "deep_research_agent"),
        ("这是一个通用对话智能体，擅长日常问答、常识解释、内容摘要、创意写作、代码辅助和轻量级信息查询。它不执行深度研究，也不处理多模态数据，适用于简单直接的文本任务和闲聊场景。当问题不涉及复杂调查或非文本媒体时，默认使用此智能体。",
            "general_agent")]
    ebd_client =OpenAI(base_url=ebd_base_url, api_key=ebd_api_key)
    query_ebd = np.array(ebd_client.embeddings.create(
        model='Qwen3-Embedding-8B', # ModelScope Model-Id, required
        input=[message],
        encoding_format="float"
        ).data[0].embedding)
    
    # 计算rules embedding
    similarity = {}
    for dsc, agent_id in EMBEDDING_RULES:
        rule_ebd = np.array(ebd_client.embeddings.create(
            model='Qwen3-Embedding-8B', # ModelScope Model-Id, required
            input=[dsc],
            encoding_format="float"
            ).data[0].embedding)
        # 计算rules和query相似度
        sim = np.dot(query_ebd, rule_ebd)
        similarity[agent_id]=sim
    agent = max(similarity, key=similarity.get) #相似度最高的为选择的模型
    return agent

