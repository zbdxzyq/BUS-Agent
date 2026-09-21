import json

from confluent_kafka import Consumer, KafkaError


KAFKA_CONFIG = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "bus-gps-monitor",
    "auto.offset.reset": "earliest"
}

TOPIC = "bus-gps"

consumer = Consumer(KAFKA_CONFIG)

consumer.subscribe([TOPIC])


if __name__ == "__main__":
    print("公交 GPS Consumer 已启动，Ctrl+C 停止")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue

                print(f"消费失败: {msg.error()}")
                continue

            event = json.loads(
                msg.value().decode("utf-8")
            )

            print(
                f"收到消息 | "
                f"partition={msg.partition()} "
                f"offset={msg.offset()} | "
                f"{event}"
            )

    except KeyboardInterrupt:
        print("\n正在停止 Consumer...")

    finally:
        consumer.close()
        print("Consumer 已停止")