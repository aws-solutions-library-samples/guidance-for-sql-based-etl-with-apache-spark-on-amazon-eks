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
#
from aws_cdk import (
    core, 
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_kms as kms
)
import os

class S3AppCodeConst(core.Construct):

    @property
    def code_bucket(self):
        return self.bucket_name

    @property
    def artifact_bucket(self):
        return self._artifact_bucket   
    
    @property
    def s3_deploy_contrust(self):
        return self.deploy

    def __init__(self,scope: core.Construct, id: str, **kwargs,) -> None:
        super().__init__(scope, id, **kwargs)

       # Upload application code to S3 bucket 
        self._artifact_bucket=s3.Bucket(self, id, 
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.KMS_MANAGED,
            removal_policy=core.RemovalPolicy.RETAIN,
            access_control = s3.BucketAccessControl.LOG_DELIVERY_WRITE,
            versioned=True #required by codebuild
        )

        proj_dir=os.path.split(os.environ['VIRTUAL_ENV'])[0]
        self.deploy=s3deploy.BucketDeployment(self, "DeployCode",
            sources=[s3deploy.Source.asset(proj_dir+'/deployment/app_code')],
            destination_bucket= self.artifact_bucket,
            destination_key_prefix="app_code"
        )
        self.bucket_name = self.artifact_bucket.bucket_name

        # # Override Cfn_Nag rule for S3 access logging
        self.artifact_bucket.node.default_child.add_metadata('cfn_nag',{
            "rules_to_suppress": [
                {
                    "id": "W35",
                    "reason": "bucket access log stops bucket removal, disable for now"
                },
                {
                    "id": "W51",
                    "reason": "bucket access is controled by IAM level"
                }
            ]
        })