FROM flink:2.1.3-scala_2.12

ARG KAFKA_CONNECTOR_VERSION=5.0.0-2.1
ARG DORIS_CONNECTOR_VERSION=26.0.0

RUN wget -P /opt/flink/lib \
    https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/${KAFKA_CONNECTOR_VERSION}/flink-sql-connector-kafka-${KAFKA_CONNECTOR_VERSION}.jar

RUN wget -P /opt/flink/lib \
    https://repo.maven.apache.org/maven2/org/apache/doris/flink-doris-connector-2.1/${DORIS_CONNECTOR_VERSION}/flink-doris-connector-2.1-${DORIS_CONNECTOR_VERSION}.jar