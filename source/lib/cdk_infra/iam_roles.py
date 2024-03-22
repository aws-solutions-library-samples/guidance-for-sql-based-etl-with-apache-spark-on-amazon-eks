import typing
from aws_cdk import (Tags, aws_iam as iam)
from constructs import Construct
# import lib.util.override_rule as scan

class IamConst(Construct):

    @property
    def managed_node_role(self):
        return self._managed_node_role

    @property
    def admin_role(self):
        return self._clusterAdminRole

    def __init__(self,scope: Construct, id:str, cluster_name:str, **kwargs,) -> None:
        super().__init__(scope, id, **kwargs)

        # EKS admin role
        self._clusterAdminRole = iam.Role(self, 'clusterAdmin',
            assumed_by= iam.AccountRootPrincipal()
        )
        self._clusterAdminRole.add_to_policy(iam.PolicyStatement(
            resources=["*"],
            actions=[
                "eks:Describe*",
                "eks:List*",
                "eks:AccessKubernetesApi",
                "ssm:GetParameter",
                "iam:ListRoles",
                "emr-containers:CreateVirtualCluster"
            ],
        ))
        Tags.of(self._clusterAdminRole).add(
            key='eks/%s/type' % cluster_name, 
            value='admin-role'
        )

        # Managed Node Group Instance Role
        _managed_node_managed_policies = (
            iam.ManagedPolicy.from_aws_managed_policy_name('AmazonEKSWorkerNodePolicy'),
            iam.ManagedPolicy.from_aws_managed_policy_name('AmazonEKS_CNI_Policy'),
            iam.ManagedPolicy.from_aws_managed_policy_name('AmazonEC2ContainerRegistryReadOnly'),
            iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchAgentServerPolicy'), 
        )
        self._managed_node_role = iam.Role(self,'NodeInstance-Role',
            path='/',
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
            managed_policies=list(_managed_node_managed_policies),
        )


        # Override Cfn Nag rule
        # scan.suppress_cfnnag_rule('W12', 'by default the role has * resource', self._clusterAdminRole.node.find_child('DefaultPolicy').node.default_child)
        