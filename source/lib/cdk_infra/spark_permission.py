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

from aws_cdk import (
    core,
    aws_iam as iam
)
from aws_cdk.aws_eks import ICluster, KubernetesManifest
from lib.util.manifest_reader import load_yaml_replace_var_local
import lib.util.override_rule as scan
import os

class SparkOnEksSAConst(core.Construct):

    @property
    def jupyter_sa(self):
        return self._jupyter_sa.service_account_name

    def __init__(self,scope: core.Construct, id: str, 
        eks_cluster: ICluster, 
        login_name: str, 
        code_bucket: str, 
        datalake_bucket: str,
        **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        source_dir=os.path.split(os.environ['VIRTUAL_ENV'])[0]+'/source'
# //******************************************************************************************//
# //************************ SETUP PERMISSION FOR ARC SPARK JOBS ****************************//
# //******* create k8s namespace, service account, and IAM role for service account ********//
# //***************************************************************************************//

        # create k8s namespace
        etl_ns = eks_cluster.add_manifest('SparkNamespace',{
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": { 
                    "name": "spark",
                    "labels": {"name":"spark"}
                }
            }
        )
        jupyter_ns = eks_cluster.add_manifest('jhubNamespace',{
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": { 
                    "name": "jupyter",
                    "labels": {"name":"spark"}
                }
            }
        )     
        
        # create k8s service account
        self._etl_sa = eks_cluster.add_service_account('ETLSa', 
            name='arcjob', 
            namespace='spark'
        )
        self._etl_sa.node.add_dependency(etl_ns)

        _etl_rb = KubernetesManifest(self,'ETLRoleBinding',
            cluster=eks_cluster,
            manifest=load_yaml_replace_var_local(source_dir+'/app_resources/etl-rbac.yaml', 
            fields= {
                "{{MY_SA}}": self._etl_sa.service_account_name
            }, 
            multi_resource=True)
        )
        _etl_rb.node.add_dependency(self._etl_sa)

        self._jupyter_sa = eks_cluster.add_service_account('jhubServiceAcct', 
            name=login_name,
            namespace='jupyter'
        )
        self._jupyter_sa.node.add_dependency(jupyter_ns)

        # Associate AWS IAM role to K8s Service Account
        datalake_bucket=code_bucket if not datalake_bucket.strip() else datalake_bucket
        _bucket_setting={
                "{{codeBucket}}": code_bucket,
                "{{datalakeBucket}}": datalake_bucket
        }
        _etl_iam = load_yaml_replace_var_local(source_dir+'/app_resources/etl-iam-role.yaml',fields=_bucket_setting)
        for statmnt in _etl_iam:
            self._etl_sa.add_to_principal_policy(iam.PolicyStatement.from_json(statmnt))
            self._jupyter_sa.add_to_principal_policy(iam.PolicyStatement.from_json(statmnt))

# # //*************************************************************************************//
# # //******************** SETUP PERMISSION FOR NATIVE SPARK JOBS   **********************//
# # //***********************************************************************************//
        self._spark_sa = eks_cluster.add_service_account('NativeSparkSa',
            name='nativejob',
            namespace='spark'
        )
        self._spark_sa.node.add_dependency(etl_ns)

        _spark_rb = eks_cluster.add_manifest('sparkRoleBinding',
            load_yaml_replace_var_local(source_dir+'/app_resources/native-spark-rbac.yaml',
                fields= {
                    "{{MY_SA}}": self._spark_sa.service_account_name
                })
        )
        _spark_rb.node.add_dependency(self._spark_sa)

        _native_spark_iam = load_yaml_replace_var_local(source_dir+'/app_resources/native-spark-iam-role.yaml',fields=_bucket_setting)
        for statmnt in _native_spark_iam:
            self._spark_sa.add_to_principal_policy(iam.PolicyStatement.from_json(statmnt))


        # Override Cfn Nag warning W12: IAM policy should not allow * resource
        scan.suppress_cfnnag_rule('W12', 'by default the etl_sa role has * resource', self._etl_sa.role.node.find_child('DefaultPolicy').node.default_child)
        scan.suppress_cfnnag_rule('W12', 'by default the role spark_sa has * resource', self._spark_sa.role.node.find_child('DefaultPolicy').node.default_child)
        scan.suppress_cfnnag_rule('W12', 'by default the role jupyter_sa has * resource', self._jupyter_sa.role.node.find_child('DefaultPolicy').node.default_child)