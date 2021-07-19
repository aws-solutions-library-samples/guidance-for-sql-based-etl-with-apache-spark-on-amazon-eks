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
from aws_cdk.aws_secretsmanager import ISecret
from aws_cdk.aws_eks import ICluster
from lib.util.manifest_reader import *
import lib.util.override_rule as scan
import os

class EksSAConst(core.Construct):

    def __init__(self, scope: core.Construct, id:str, eks_cluster: ICluster, secret: ISecret, **kwargs,) -> None:
        super().__init__(scope, id, **kwargs)

        source_dir=os.path.split(os.environ['VIRTUAL_ENV'])[0]+'/source'

# //************************************v*************************************************************//
# //***************************** SERVICE ACCOUNT, RBAC and IAM ROLES *******************************//
# //****** Associating IAM role to K8s Service Account to provide fine-grain security control ******//
# //***********************************************************************************************//
        # Cluster Auto-scaler
        self._scaler_sa = eks_cluster.add_service_account('AutoScalerSa', 
            name='cluster-autoscaler', 
            namespace='kube-system'
        )  
        _scaler_role = load_yaml_local(source_dir+'/app_resources/autoscaler-iam-role.yaml')
        for statmt in _scaler_role:
            self._scaler_sa.add_to_principal_policy(iam.PolicyStatement.from_json(statmt))

        # ALB Ingress
        self._alb_sa = eks_cluster.add_service_account('ALBServiceAcct', 
            name='alb-aws-load-balancer-controller',
            namespace='kube-system'
        )
        _alb_role = load_yaml_local(source_dir+'/app_resources/alb-iam-role.yaml')
        for statmt in _alb_role:
            self._alb_sa.add_to_principal_policy(iam.PolicyStatement.from_json(statmt))

        # External secret controller
        self._secrets_sa = eks_cluster.add_service_account('ExSecretController',
            name='external-secrets-controller',
            namespace="kube-system"
        )
        self._secrets_sa.node.add_dependency(secret)
        _secrets_role = load_yaml_replace_var_local(source_dir+'/app_resources/ex-secret-iam-role.yaml',
                        fields={"{{secretsmanager}}": secret.secret_arn+"*"}
                    )
        for statmt in _secrets_role:
            self._secrets_sa.add_to_principal_policy(iam.PolicyStatement.from_json(statmt))  

# //************************************v*************************************************************//
# //*********************** Override cfn Nag scan rules for deployment *******************************//
# //***********************************************************************************************//   
        
        # Override Cfn Nag warning W12: IAM policy should not allow * resource
        scan.suppress_cfnnag_rule('W12', 'by default the role scaler_sa has * resource', self._scaler_sa.role.node.find_child('DefaultPolicy').node.default_child)
        scan.suppress_cfnnag_rule('W12', 'by default the role secrets_sa has * resource', self._secrets_sa.role.node.find_child('DefaultPolicy').node.default_child)
        scan.suppress_iam_cfnnag_rule(self._alb_sa.role.node.find_child('DefaultPolicy').node.default_child)