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

from aws_cdk import (aws_eks as eks,aws_ec2 as ec2, RemovalPolicy)
from aws_cdk.aws_iam import IRole
from constructs import Construct
from aws_cdk.lambda_layer_kubectl_v27 import KubectlV27Layer

class EksConst(Construct):

    @property
    def my_cluster(self):
        return self._my_cluster

    def __init__(self, scope: Construct, id:str, eksname: str, eksvpc: ec2.IVpc, noderole: IRole, eks_adminrole: IRole, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # 1.Create EKS cluster without node group
        self._my_cluster = eks.Cluster(self,'EKS',
                vpc= eksvpc,
                cluster_name=eksname,
                masters_role=eks_adminrole,
                output_cluster_name=True,
                version= eks.KubernetesVersion.V1_27,
                endpoint_access= eks.EndpointAccess.PUBLIC_AND_PRIVATE,
                default_capacity=0,
                kubectl_layer=KubectlV27Layer(self, 'kubectlV27Layer')
        )

        # 2.Add Managed NodeGroup to EKS, compute resource to run Spark jobs
        self._my_cluster.add_nodegroup_capacity('onDemand-mn',
            nodegroup_name = 'etl-ondemand',
            node_role = noderole,
            desired_size = 1,
            max_size = 5,
            disk_size = 50,
            instance_types = [ec2.InstanceType('m7g.xlarge')],
            labels = {'lifecycle':'OnDemand'},
            # create one nodegroup per AZ, as cluster autoscaler has no control over what AZ ASG will launch instance in.
            # if using Karpenter, this is not needed.
            subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,one_per_az=True),
            tags = {'Name':'OnDemand-'+eksname,'k8s.io/cluster-autoscaler/enabled': 'true', 'k8s.io/cluster-autoscaler/'+eksname: 'owned'}
        )

        # 3. Add Spot managed NodeGroup to EKS (Run Spark exectutor on spot)
        self._my_cluster.add_nodegroup_capacity('spot-mn',
            nodegroup_name = 'etl-spot',
            node_role = noderole,
            capacity_type=eks.CapacityType.SPOT,
            desired_size = 1,
            max_size = 30,
            disk_size = 50,
            instance_types=[ec2.InstanceType('r5.xlarge'),ec2.InstanceType('r4.xlarge'),ec2.InstanceType('r5a.xlarge')],
            subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,one_per_az=True),
            labels = {'lifecycle':'Ec2Spot'},
            # The unique tag k8s.io/cluster-autoscaler/node-template/label/nodegroup: etl-spot is a must
            # to enable the nodegroup scale from 0 to N for the cost efficiency
            tags = {'Name':'Spot-'+eksname, 'k8s.io/cluster-autoscaler/enabled': 'true', 'k8s.io/cluster-autoscaler/'+eksname: 'owned'}
        )
        self._my_cluster.add_nodegroup_capacity('spot-arm64',
            nodegroup_name = 'single-az-graviton',
            node_role = noderole,
            capacity_type=eks.CapacityType.SPOT,
            desired_size = 0,
            min_size=0,
            max_size = 30,
            disk_size = 50,
            instance_types = [ec2.InstanceType('r7g.xlarge'),ec2.InstanceType('r6g.xlarge'),ec2.InstanceType('r6gd.xlarge')],
            # create one nodegroup per AZ, as cluster autoscaler has no control over what AZ ASG will launch instance in.
            # if using Karpenter, this is not needed.
            subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,availability_zones=sorted(eksvpc.availability_zones)[1:2]),
            labels = {'nodegroup':'single-az-graviton', 'lifecycle':'Ec2Spot'},
            # The unique tag k8s.io/cluster-autoscaler/node-template/label/nodegroup:etl-spot-graviton is a must
            # to enable the nodegroup scale from 0 to N for the cost efficiency
            tags = {'Name':'single-az-graviton','k8s.io/cluster-autoscaler/enabled': 'true', 'k8s.io/cluster-autoscaler/'+eksname: 'owned','k8s.io/cluster-autoscaler/node-template/label/nodegroup':'single-az-graviton'}
        )  

        # # 4. Add Fargate NodeGroup to EKS, without setup cluster-autoscaler
        # self._my_cluster.add_fargate_profile('FargateEnabled',
        #     selectors =[{
        #         "namespace": "spark"
        #     }],
        #     fargate_profile_name='sparkETL'
        # )