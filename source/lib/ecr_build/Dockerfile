#FROM ghcr.io/tripl-ai/arc::latest
FROM ghcr.io/tripl-ai/arc:arc_3.11.1_spark_3.1.2_scala_2.12_hadoop_3.2.0_1.0.0
ENV SPARK_HOME /opt/spark
RUN mkdir -p $SPARK_HOME/work-dir
WORKDIR $SPARK_HOME/work-dir