import json
import time
from datetime import datetime, timedelta

from confluent_kafka import Producer


producer = Producer({
    "bootstrap.servers": "localhost:9092"
})

TOPIC = "bus-gps"


def send_event(vehicle_id, delay_seconds):
    event_time = datetime.now() - timedelta(seconds=delay_seconds)

    event = {
        "vehicle_id": vehicle_id,
        "route_id": 12,
        "longitude": 118.78,
        "latitude": 32.05,
        "speed": 30.0,
        "passenger_count": 20,
        "timestamp": event_time.isoformat(timespec="seconds")
    }

    producer.produce(
        topic=TOPIC,
        key=vehicle_id.encode("utf-8"),
        value=json.dumps(event).encode("utf-8")
    )

    producer.poll(0)

    print(
        f"{vehicle_id:<15} "
        f"delay={delay_seconds:<2}s "
        f"event_time={event['timestamp']}"
    )


if __name__ == "__main__":
    print("先发送正常数据，推动 Watermark...")

    # 先用正常事件把 Watermark 推到当前时间附近
    for _ in range(12):
        send_event("NORMAL_TEST", 0)
        time.sleep(1)

    print("\n开始混合发送正常、5秒延迟、45秒延迟数据...")

    try:
        while True:
            send_event("NORMAL_TEST", 0)

            time.sleep(1)

            send_event("DELAY_5_TEST", 5)
            send_event("DELAY_45_TEST", 45)

            producer.flush()

            time.sleep(1)

    except KeyboardInterrupt:
        pass

    finally:
        producer.flush()
        print("测试 Producer 已停止")