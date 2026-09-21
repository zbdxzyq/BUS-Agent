from pathlib import Path

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


BASE_DIR = Path(__file__).resolve().parents[2]


def main():

    # ======================
    # 1.读取知识文件
    # ======================

    knowledge_dir = (
            BASE_DIR / "knowledge_base"
    )

    file_path = list(
        knowledge_dir.glob("*.md")
    )

    print("发现知识文件:")
    for f in file_path:
        print("-", f.name)

    # ======================
    # 2.文本切片
    # ======================

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=50
    )

    documents = []

    total_chunks = 0

    for file in file_path:

        print("\n正在处理:", file.name)

        text = file.read_text(
            encoding="utf-8"
        )

        print(
            "文本长度:",
            len(text)
        )

        chunks = splitter.split_text(text)

        print(
            "切片数量:",
            len(chunks)
        )

        for i, chunk in enumerate(chunks):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": file.name,
                        "chunk_id": i
                    }
                )
            )

        total_chunks += len(chunks)

    print("\n总切片数量:", total_chunks)


    # ======================
    # 3.Embedding模型
    # ======================

    embeddings = OllamaEmbeddings(
        model="qwen3-embedding:0.6b"
    )


    # ======================
    # 4.建立Chroma
    # ======================

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(
            BASE_DIR / "data" / "chroma"
        )
    )


    print("Chroma知识库创建完成")


if __name__ == "__main__":
    main()