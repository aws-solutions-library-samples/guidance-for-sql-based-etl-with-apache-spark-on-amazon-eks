#FROM ghcr.io/tripl-ai/arc::latest
FROM ghcr.io/tripl-ai/arc:arc_4.2.0_spark_3.3.4_scala_2.12_hadoop_3.3.2_4.2.1_slim
ENV SPARK_HOME /opt/spark
RUN mkdir -p $SPARK_HOME/work-dir
WORKDIR $SPARK_HOME/work-dir