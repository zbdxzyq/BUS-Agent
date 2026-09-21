from app.rag.service import BusKnowledgeService


if __name__ == "__main__":


    service = BusKnowledgeService()


    result = service.search(
        "公交线路速度持续下降应该怎么办？"
    )


    for item in result:

        print("================")

        print(
            item["content"]
        )

        print(
            item["source"]
        )