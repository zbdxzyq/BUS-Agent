import json
import random
import time
from datetime import datetime

from confluent_kafka import Producer


KAFKA_CONFIG = {
    "bootstrap.servers": "localhost:9092"
}

TOPIC = "bus-gps"

producer = Producer(KAFKA_CONFIG)


def generate_gps_event():
    route_id = random.choice([12, 88, 99])

    return {
        "vehicle_id": f"BUS_{random.randint(1, 30):03d}",
        "route_id": route_id,
        "longitude": round(118.75 + random.uniform(-0.05, 0.05), 6),
        "latitude": round(32.05 + random.uniform(-0.05, 0.05), 6),
        "speed": round(random.uniform(10, 60), 1),
        "passenger_count": random.randint(0, 60),
        "timestamp": datetime.now().isoformat(timespec="seconds")
    }


def delivery_report(err, msg):
    if err is not None:
        print(f"发送失败: {err}")
    else:
        print(
            f"发送成功 | topic={msg.topic()} "
            f"partition={msg.partition()} "
            f"offset={msg.offset()}"
        )


if __name__ == "__main__":
    print("公交 GPS Producer 已启动，Ctrl+C 停止")

    try:
        while True:
            event = generate_gps_event()

            producer.produce(
                topic=TOPIC,
                key=event["vehicle_id"].encode("utf-8"),
                value=json.dumps(
                    event,
                    ensure_ascii=False
                ).encode("utf-8"),
                callback=delivery_report
            )

            producer.poll(0)

            print(event)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n正在停止 Producer...")

    finally:
        producer.flush()
        print("Producer 已停止")