#!/usr/bin/env python3
from aws_cdk import (App,Tags,CfnOutput)
from lib.spark_on_eks_stack import SparkOnEksStack
from lib.cloud_front_stack import NestedStack

app = App()

eks_name = app.node.try_get_context('cluster_name')
solution_id = app.node.try_get_context('solution_id')
solution_version= app.node.try_get_context('version')

# main stack
eks_stack = SparkOnEksStack(app, 'sql-based-etl-with-apache-spark-on-amazon-eks', eks_name, solution_id, solution_version)
# Recommend to remove the CloudFront nested stack. Setup your own SSL certificate and add it to ALB.
cf_nested_stack = NestedStack(eks_stack,'CreateCloudFront', eks_stack.code_bucket, eks_stack.argo_url, eks_stack.jhub_url)
Tags.of(eks_stack).add('project', 'sqlbasedetl')
Tags.of(cf_nested_stack).add('project', 'sqlbasedetl')
# Deployment Output
CfnOutput(eks_stack,'CODE_BUCKET', value=eks_stack.code_bucket)
CfnOutput(eks_stack,'ARGO_URL', value='https://'+ cf_nested_stack.argo_cf)
CfnOutput(eks_stack,'JUPYTER_URL', value='https://'+ cf_nested_stack.jhub_cf)

app.synth()