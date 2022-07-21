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
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_codepipeline as codepipeline,
    aws_codebuild as codebuild,
    aws_codepipeline_actions as codepipeline_actions,
    aws_ecr as ecr,
) 
from constructs import Construct
import lib.util.override_rule as scan

class DockerPipelineConstruct(Construct):

    @property
    def image_uri(self):
        return self.ecr_repo.repository_uri

    def __init__(self,scope: Construct, id: str, codebucket: s3.IBucket, **kwargs,) -> None:
        super().__init__(scope, id, **kwargs)
        
        # 1. Create ECR repositories
        self.ecr_repo=ecr.Repository(self,'ECRRepo',
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.DESTROY
        )
        # 2. Setup deployment CI/CD to deploy docker image to ECR
        pipeline = codepipeline.Pipeline(self, "Pipeline",
            pipeline_name='BuildArcDockerImage',
            artifact_bucket=codebucket
        )
        image_builder = codebuild.PipelineProject(self,'DockerBuild',
            project_name='BuildArcDockerImage',
            build_spec=codebuild.BuildSpec.from_source_filename('buildspec.yaml'),
            environment=dict(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                privileged=True
            ),
            environment_variables={
                'REPO_ECR': codebuild.BuildEnvironmentVariable(value=self.ecr_repo.repository_uri),
            },
            description='Pipeline for docker build',
            timeout=Duration.minutes(60)
        )
        image_builder.apply_removal_policy(RemovalPolicy.DESTROY)

        # 3. grant permissions for the CI/CD
        codebucket.grant_read_write(pipeline.role)
        codebucket.grant_read_write(image_builder)  
        self.ecr_repo.grant_pull_push(image_builder)

        source_output=codepipeline.Artifact('src')
        pipeline.add_stage(
            stage_name='Source',
            actions=[
                codepipeline_actions.S3SourceAction(
                    action_name='S3Trigger',
                    bucket=codebucket,
                    bucket_key='app_code/ecr_build_src.zip',
                    output=source_output,
                    trigger=codepipeline_actions.S3Trigger.POLL),
            ]
        )
        pipeline.add_stage(
            stage_name='Build',
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name='DockerImageBuild',
                    input=source_output,
                    project=image_builder
                )
            ]
        )

        # Override Cfn Nag warning W12: IAM policy should not allow * resource
        scan.suppress_cfnnag_rule('W12', 'the role for action of ecr:GetAuthorizationToken requires * resource', image_builder.role.node.find_child('DefaultPolicy').node.default_child)

        image_builder.role.node.find_child('DefaultPolicy').node.default_child.add_metadata('cfn_nag',{
            "rules_to_suppress": [
                {
                    "id": "W12",
                    "reason": "the role for action of ecr:GetAuthorizationToken requires * resource"
                },
                {
                    "id": "W76",
                    "reason": "the IAM policy is complex, need to be higher than 25"
                }
            ]
        })