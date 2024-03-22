from aws_cdk import (Tags, aws_ec2 as ec2, aws_s3 as s3)
from constructs import Construct
# import lib.util.override_rule as scan 
import lib.util.get_aws_managed_prefix as custom

class NetworkSgConst(Construct):

    @property
    def vpc(self):
        return self._vpc
    @property
    def alb_jhub_sg(self):
        return self._alb_jhub_sg
    @property
    def alb_argo_sg(self):
        return self._alb_argo_sg

    def __init__(self,scope: Construct, id:str, eksname:str, codebucket: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # //*************************************************//
        # //******************* NETWORK ********************//
        # //************************************************//
        # create VPC
        self._vpc = ec2.Vpc(self, 'eksVpc',max_azs=2, nat_gateways=1)
        Tags.of(self._vpc).add('Name', eksname + 'EksVpc')

        # self._log_bucket=s3.Bucket.from_bucket_name(self,'vpc_logbucket', codebucket)
        # self._vpc.add_flow_log("FlowLogCloudWatch",
        #     destination=ec2.FlowLogDestination.to_s3(self._log_bucket,'vpcRejectlog/'),
        #     traffic_type=ec2.FlowLogTrafficType.REJECT
        # )

        # ALB security group for Jupyter & Argo
        prefixlist_peer=ec2.Peer.prefix_list(
                custom.AwsManagedPrefixList(self,'cr-getprefixId',
                    custom.AwsManagedPrefixListProps(name='com.amazonaws.global.cloudfront.origin-facing')
                ).prefixlist_id
            )
        self._alb_jhub_sg=ec2.SecurityGroup(self,'JupyterALBInboundSG', vpc=self._vpc,description='Security Group for Jupyter ALB')
        self._alb_argo_sg=ec2.SecurityGroup(self,'ArgoALBInboundSG', vpc=self._vpc,description='Security Group for Argo ALB')
        self._alb_jhub_sg.add_ingress_rule(prefixlist_peer,ec2.Port.tcp(port=80))
        self._alb_argo_sg.add_ingress_rule(prefixlist_peer,ec2.Port.tcp(port=2746))
        Tags.of(self._alb_jhub_sg).add('Name','SparkOnEKS-JhubSg')
        Tags.of(self._alb_argo_sg).add('Name','SparkOnEKS-ArgoSg')

        # VPC endpoint security group
        self._vpc_endpoint_sg = ec2.SecurityGroup(self,'EndpointSg',vpc=self._vpc,description='Security Group for Endpoint')
        self._vpc_endpoint_sg.add_ingress_rule(ec2.Peer.ipv4(self._vpc.vpc_cidr_block),ec2.Port.tcp(port=443))
        self._vpc_endpoint_sg.add_ingress_rule(ec2.Peer.ipv4(self._vpc.vpc_cidr_block),ec2.Port.tcp(port=444))
        Tags.of(self._vpc_endpoint_sg).add('Name','SparkOnEKS-VPCEndpointSg')
        
        # Add VPC endpoint 
        self._vpc.add_gateway_endpoint("S3GatewayEndpoint",
                                        service=ec2.GatewayVpcEndpointAwsService.S3,
                                        subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                                                 ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)])
                                                 
        self._vpc.add_interface_endpoint("EcrDockerEndpoint",service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER, security_groups=[self._vpc_endpoint_sg])
        self._vpc.add_interface_endpoint("CWLogsEndpoint", service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,security_groups=[self._vpc_endpoint_sg])
        self._vpc.add_interface_endpoint("AthenaEndpoint", service=ec2.InterfaceVpcEndpointAwsService.ATHENA,security_groups=[self._vpc_endpoint_sg])
        self._vpc.add_interface_endpoint("KMSEndpoint", service=ec2.InterfaceVpcEndpointAwsService.KMS,security_groups=[self._vpc_endpoint_sg])
        

        # Override Cfn_Nag rule for AWS Solution CICD validation
        # for subnet in self._vpc.public_subnets:
        #     scan.suppress_cfnnag_rule('W33','a public facing ALB is required and ingress from the internet should be permitted.',subnet.node.default_child)

        # self._vpc_endpoint_sg.node.default_child.add_metadata('cfn_nag',{
        #     "rules_to_suppress": [
        #         {
        #             "id": "W40",
        #             "reason": "Egress IP Protocol of -1 is default and generally considered OK"
        #         },
        #         {
        #             "id": "W5",
        #             "reason": "Security Groups with cidr open considered OK"
        #         }
        #     ]
        # })
