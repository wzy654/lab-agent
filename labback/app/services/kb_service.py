from pathlib import Path

import chromadb
import numpy as np
from chromadb import Collection
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from app.config import BASE_DIR

KB_DIR=BASE_DIR/"data"/"kb"
CHROMA_DIR=BASE_DIR/"data"/"chroma"

# 模型文件目录：chromadb 默认的缓存位置，已手动放置多语言模型 paraphrase-multilingual-MiniLM-L12-v2
# （从 hf-mirror.com 下载，共 6 个文件，chromadb 检测到文件齐全就不会再去官方源下载）
MODEL_DIR=Path.home()/".cache"/"chroma"/"onnx_models"/"all-MiniLM-L6-v2"/"onnx"

_collection=None


class MultilingualMiniLMEmbedding(EmbeddingFunction[Documents]):
    """多语言 MiniLM 嵌入函数（绕开 chromadb 默认推理实现的 pad_id 缺陷）

    为什么不用 chromadb 自带的推理：
      chromadb 默认把所有文本 pad 到固定 256 长度且硬编码 pad_id=0，
      而本模型（XLM-R 架构）的 pad token id 是 1，id=0 是 <s> 起始符，
      导致 mean pooling 被大量 <s> 向量稀释，所有嵌入向量几乎相同（实测距离全部挤在 1.4~2.1）。
    这里的做法：
      逐条编码、完全不 padding，每条文本只由自己的真实 token 参与 mean pooling，
      与诊断脚本验证过的「干净编码路径」完全一致。
    """

    def __init__(self):
        # 延迟导入重依赖，避免模块导入时才失败导致整个服务起不来
        from tokenizers import Tokenizer
        import onnxruntime as ort

        self._tokenizer=Tokenizer.from_file(str(MODEL_DIR/"tokenizer.json"))
        self._session=ort.InferenceSession(
            str(MODEL_DIR/"model.onnx"), providers=["CPUExecutionProvider"]
        )

    def __call__(self, input: Documents) -> Embeddings:
        """把一批文本转成嵌入向量列表（chromadb 在 add/query 时自动调用）"""
        result=[]
        for text in input:
            enc=self._tokenizer.encode(text, add_special_tokens=True)
            ids=np.array([enc.ids], dtype=np.int64)
            mask=np.array([enc.attention_mask], dtype=np.int64)
            feed={
                "input_ids": ids,
                "attention_mask": mask,
                # XLM-R 架构没有 token_type 概念，但 onnx 导出保留了该输入，全 0 即可
                "token_type_ids": np.zeros_like(ids),
            }
            out=self._session.run(None, feed)[0]  # 形状 (1, 序列长度, 384)
            # mean pooling：只对真实 token（attention_mask=1）求平均，再归一化
            m=mask[0].reshape(-1, 1).astype(np.float32)
            vec=np.sum(out[0]*m, axis=0)/np.clip(m.sum(), 1e-9, None)
            vec=vec/np.linalg.norm(vec)
            result.append(vec.astype(np.float32).tolist())
        return result

    @staticmethod
    def name() -> str:
        return "multilingual_minilm_l12"

    def default_space(self) -> str:
        # 余弦距离：语义检索的标准选择
        return "cosine"


def get_collection() -> Collection:
    """向量库初始化"""
    global _collection
    if _collection is not None:
        return _collection
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # 必须显式传入自定义嵌入函数，否则 chromadb 用默认实现（有 pad_id 缺陷）
    col = client.get_or_create_collection(
        name="lab_kb", embedding_function=MultilingualMiniLMEmbedding()
    )
    if col.count() == 0:
        ids=[]
        docs=[]
        metas=[]
        for file in sorted(KB_DIR.glob("*.md")):
            text=file.read_text(encoding="UTF-8").strip()
            if not text:
                continue
            docs.append(text)
            ids.append(file.stem)#根据文件名称作为id
            metas.append({"source":file.name})
        if docs:
            col.add(ids=ids,documents=docs,metadatas=metas)
    _collection=col
    return col

def search(query:str):
    """搜索向量存储集合"""
    col=get_collection()
    if col.count() == 0:
        return ""
    # 只取相关度最高的 3 篇（n_results=col.count() 会全量返回，检索失去意义且 prompt 膨胀）
    results=col.query(query_texts=query,n_results=min(3, col.count()))
    docs= (results.get("documents") or [])[0]
    metas= (results.get("metadatas") or [])[0]
    distances = (results.get("distances") or [])[0]
    parts=[]
    for doc,meta,distance in zip(docs,metas,distances):
        score=1/(1+distance)
        # 阈值兜底用：多语言模型下相关问题的 distance 约 0.3~0.7（score>0.59），
        # score<0.35（distance>1.86）只滤掉极端无关的查询，正常检索不会被误杀
        if score<0.35:
            continue
        name=meta.get("source","")
        parts.append({"score":score,"content":f"{name}\n{doc}"})
    parts.sort(key=lambda x:x["score"],reverse=True)
    final_parts=[item["content"] for item in parts[:2]]
    print(final_parts)
    # 必须返回拼接后的字符串：ai_service 直接把结果拼进 system_prompt，
    # 如果返回 list，f-string 会把 Python repr（带引号方括号）塞进提示词
    return "\n\n".join(final_parts)






