#FROM ghcr.io/tripl-ai/arc::latest
FROM ghcr.io/tripl-ai/arc:arc_3.10.0_spark_3.0.3_scala_2.12_hadoop_3.2.0_1.0.0
ENV SPARK_HOME /opt/spark
RUN mkdir -p $SPARK_HOME/work-dir
WORKDIR $SPARK_HOME/work-dir