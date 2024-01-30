######################################################################################################################
# Copyright 2020-2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                      #
#                                                                                                                   #
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance    #
# with the License. A copy of the License is located at                                                             #
#                                                                                                                   #
#     http://www.apache.org/licenses/LICENSE-2.0                                                                    #
#                                                                                                                   #
# or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES #
# OR CONDITIONS OF ANY KIND, express o#implied. See the License for the specific language governing permissions     #
# and limitations under the License.  																				#                                                                              #
######################################################################################################################

from aws_cdk import (Stack, CfnOutput, Duration, RemovalPolicy, Aws, Fn, CfnParameter, aws_eks as eks,aws_secretsmanager as secmger,aws_kms as kms)
from constructs import Construct
from lib.cdk_infra.network_sg import NetworkSgConst
from lib.cdk_infra.iam_roles import IamConst
from lib.cdk_infra.eks_cluster import EksConst
from lib.cdk_infra.eks_service_account import EksSAConst
from lib.cdk_infra.eks_base_app import EksBaseAppConst
from lib.cdk_infra.s3_app_code import S3AppCodeConst
from lib.cdk_infra.spark_permission import SparkOnEksSAConst
from lib.ecr_build.ecr_build_pipeline import DockerPipelineConstruct
from lib.cloud_front_stack import NestedStack
from lib.util.manifest_reader import *
# from lib.util import override_rule as scan
# from lib.solution_helper import solution_metrics
import json, os

class SparkOnEksStack(Stack):

    @property
    def code_bucket(self):
        return self.app_s3.code_bucket

    @property
    def argo_url(self):
        return self._argo_alb.value

    @property
    def jhub_url(self):
        return self._jhub_alb.value 

    def __init__(self, scope: Construct, id: str, eksname: str, solution_id: str, version: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.template_options.description = "(SO0141) SQL based ETL with Apache Spark on Amazon EKS. This solution provides a SQL based ETL option with a open-source declarative framework powered by Apache Spark."
        source_dir=os.path.split(os.environ['VIRTUAL_ENV'])[0]+'/source'

        # Cloudformation input params
        datalake_bucket = CfnParameter(self, "datalakebucket", type="String",
            description="Your existing S3 bucket to be accessed by Jupyter Notebook and ETL job. Default: blank",
            default=""
        )
        login_name = "sparkoneks"
        # login_name = CfnParameter(self, "jhubuser", type="String",
        #     description="Your username login to jupyter hub. Only alphanumeric characters are allowed",
        #     default="sparkoneks"
        # )

        # Auto-generate a user login in secrets manager
        key = kms.Key(self, 'KMSKey',removal_policy=RemovalPolicy.DESTROY,enable_key_rotation=True)
        key.add_alias("alias/secretsManager")
        jhub_secret = secmger.Secret(self, 'jHubPwd', 
            generate_secret_string=secmger.SecretStringGenerator(
                exclude_punctuation=True,
                secret_string_template=json.dumps({'username': login_name}),
                generate_string_key="password"),
            removal_policy=RemovalPolicy.DESTROY,
            encryption_key=key
        )

        # 1. a new bucket to store app code and logs
        self.app_s3 = S3AppCodeConst(self,'appcode')

        # 2. push docker image to ECR via AWS CICD pipeline
        ecr_image = DockerPipelineConstruct(self,'image', self.app_s3.artifact_bucket)
        ecr_image.node.add_dependency(self.app_s3)
        CfnOutput(self,'IMAGE_URI', value=ecr_image.image_uri)

        # 3. EKS base infrastructure
        network_sg = NetworkSgConst(self,'network-sg', eksname, self.app_s3.code_bucket)
        iam = IamConst(self,'iam_roles', eksname)
        eks_cluster = EksConst(self,'eks_cluster', eksname, network_sg.vpc, iam.managed_node_role, iam.admin_role)
        EksSAConst(self, 'eks_sa', eks_cluster.my_cluster, jhub_secret)
        base_app=EksBaseAppConst(self, 'eks_base_app', eks_cluster.my_cluster)

        # 4. Spark app access control
        app_security = SparkOnEksSAConst(self,'spark_service_account', 
            eks_cluster.my_cluster, 
            login_name,
            self.app_s3.code_bucket,
            datalake_bucket.value_as_string
        )
        app_security.node.add_dependency(base_app.secret_created)
        # 5. Install Arc Jupyter notebook in EKS
        jhub_install= eks_cluster.my_cluster.add_helm_chart('JHubChart',
            chart='jupyterhub',
            repository='https://jupyterhub.github.io/helm-chart',
            release='jhub',
            version='1.2.0',
            namespace='jupyter',
            create_namespace=False,
            values=load_yaml_replace_var_local(source_dir+'/app_resources/jupyter-values.yaml', 
                fields={
                    "{{codeBucket}}": self.app_s3.code_bucket,
                    "{{region}}": Aws.REGION
                })
        )
        jhub_install.node.add_dependency(app_security)
        # EKS get Jupyter login dynamically from secrets manager
        name_parts=Fn.split('-',jhub_secret.secret_name)
        name_no_suffix=Fn.join('-',[Fn.select(0, name_parts), Fn.select(1, name_parts)])

        config_hub = eks.KubernetesManifest(self,'JHubConfig',
            cluster=eks_cluster.my_cluster,
            manifest=load_yaml_replace_var_local(source_dir+'/app_resources/jupyter-config.yaml', 
                fields= {
                    "{{MY_SA}}": app_security.jupyter_sa,
                    "{{REGION}}": Aws.REGION, 
                    "{{SECRET_NAME}}": name_no_suffix,
                    "{{INBOUND_SG}}": network_sg.alb_jhub_sg.security_group_id
                }, 
                multi_resource=True)
        )
        config_hub.node.add_dependency(jhub_install)
            
        # 6. Install ETL orchestrator - Argo in EKS
        # can be replaced by other workflow tool, eg. Airflow
        argo_install = eks_cluster.my_cluster.add_helm_chart('ARGOChart',
            chart='argo-workflows',
            repository='https://argoproj.github.io/argo-helm',
            release='argo',
            version='0.40.7',
            namespace='argo',
            create_namespace=True,
            values=load_yaml_replace_var_local(source_dir+'/app_resources/argo-values.yaml',
                fields= {
                    "{{INBOUND_SG}}": network_sg.alb_argo_sg.security_group_id
                })
        )
        argo_install.node.add_dependency(config_hub)
        # Create argo workflow template for Spark with T-shirt size
        submit_tmpl = eks_cluster.my_cluster.add_manifest('SubmitSparkWrktmpl',
            load_yaml_local(source_dir+'/app_resources/spark-template.yaml')
        )
        submit_tmpl.node.add_dependency(argo_install)

        # 7. (OPTIONAL) retrieve ALB DNS Name to enable CloudFront in the nested stack.
        # It is used to serve HTTPS requests with its default domain name. 
        # Recommend to issue your own TLS certificate, and delete the CF components.
        self._jhub_alb=eks.KubernetesObjectValue(self, 'jhubALB',
            cluster=eks_cluster.my_cluster,
            json_path='..status.loadBalancer.ingress[0].hostname',
            object_type='ingress.networking',
            object_name='jupyterhub',
            object_namespace='jupyter',
            timeout=Duration.minutes(10)
        )
        self._jhub_alb.node.add_dependency(config_hub)

        self._argo_alb = eks.KubernetesObjectValue(self, 'argoALB',
            cluster=eks_cluster.my_cluster,
            json_path='..status.loadBalancer.ingress[0].hostname',
            object_type='ingress.networking',
            object_name='argo-argo-workflows-server',
            object_namespace='argo',
            timeout=Duration.minutes(10)
        )
        self._argo_alb.node.add_dependency(argo_install)

        # 8. (OPTIONAL) Send solution metrics to AWS
        # turn it off from the CloudFormation mapping section if prefer.
        # send_metrics=solution_metrics.SendAnonymousData(self,"SendMetrics", network_sg.vpc, self.app_s3.artifact_bucket,self.app_s3.s3_deploy_contrust,
        #     metrics={
        #                 "Solution": solution_id,
        #                 "Region": Aws.REGION,
        #                 "SolutionVersion": version,
        #                 "UUID": "MY_UUID",
        #                 "UseDataLakeBucket": "True" if not datalake_bucket.value_as_string else "False",
        #                 "UseAWSCICD": "True" if ecr_image.image_uri else "False",
        #                 "NoAZs": len(network_sg.vpc.availability_zones)
        #             }
        # )
        # send_metrics.node.add_dependency(self.app_s3.s3_deploy_contrust)

        # 9. (OPTIONAL) Override the cfn Nag rules for AWS Solution CICD deployment
        # remove the section if your CI/CD pipeline doesn't use the cfn_nag utility to validate the CFN.
        # k8s_ctl_node=self.node.find_child('@aws-cdk--aws-eks.KubectlProvider')
        # cluster_resrc_node=self.node.find_child('@aws-cdk--aws-eks.ClusterResourceProvider')
        # scan.suppress_cfnnag_rule('W12', 'by default the role has * resource', self.node.find_child('eks_cluster').node.find_child('EKS').node.default_child.node.find_child('CreationRole').node.find_child('DefaultPolicy').node.default_child)
        # scan.suppress_cfnnag_rule('W11', 'by default the role has * resource', self.node.find_child('Custom::AWSCDKOpenIdConnectProviderCustomResourceProvider').node.find_child('Role'))
        # scan.suppress_lambda_cfnnag_rule(k8s_ctl_node.node.find_child('Handler').node.default_child)
        # scan.suppress_lambda_cfnnag_rule(k8s_ctl_node.node.find_child('Provider').node.find_child('framework-onEvent').node.default_child)
        # scan.suppress_lambda_cfnnag_rule(self.node.find_child('Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C').node.default_child)
        # # scan.suppress_lambda_cfnnag_rule(self.node.find_child('Custom::S3AutoDeleteObjectsCustomResourceProvider').node.find_child('Handler'))
        # scan.suppress_lambda_cfnnag_rule(self.node.find_child('Custom::AWSCDKOpenIdConnectProviderCustomResourceProvider').node.find_child('Handler'))
        # scan.suppress_lambda_cfnnag_rule(self.node.find_child('AWSCDKCfnUtilsProviderCustomResourceProvider').node.find_child('Handler'))
        # scan.suppress_lambda_cfnnag_rule(cluster_resrc_node.node.find_child('OnEventHandler').node.default_child)
        # scan.suppress_lambda_cfnnag_rule(cluster_resrc_node.node.find_child('IsCompleteHandler').node.default_child)
        # scan.suppress_lambda_cfnnag_rule(cluster_resrc_node.node.find_child('Provider').node.find_child('framework-isComplete').node.default_child)
        # scan.suppress_lambda_cfnnag_rule(cluster_resrc_node.node.find_child('Provider').node.find_child('framework-onTimeout').node.default_child)      
        # scan.suppress_lambda_cfnnag_rule(cluster_resrc_node.node.find_child('Provider').node.find_child('framework-onEvent').node.default_child)
        # scan.suppress_network_cfnnag_rule(self.node.find_child('eks_cluster').node.find_child('EKS').node.find_child('ControlPlaneSecurityGroup').node.default_child)
        # scan.suppress_lambda_cfnnag_rule(self.node.find_child('SendMetrics').node.find_child('LambdaProvider').node.find_child('framework-onEvent').node.default_child)
        # scan.suppress_network_cfnnag_rule(self.node.find_child('SendMetrics').node.find_child('LambdaProvider').node.find_child('framework-onEvent').node.find_child('SecurityGroup').node.default_child)
        # scan.suppress_lambda_cfnnag_rule(self.node.find_child('SingletonLambda75248a819138468c9ba1bca6c7137599').node.default_child)
        # scan.suppress_network_cfnnag_rule(self.node.find_child('SingletonLambda75248a819138468c9ba1bca6c7137599').node.find_child('SecurityGroup').node.default_child)
