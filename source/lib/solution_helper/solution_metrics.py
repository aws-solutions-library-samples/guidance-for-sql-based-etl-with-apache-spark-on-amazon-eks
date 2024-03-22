from constructs import Construct
from aws_cdk.aws_s3 import IBucket
from lib.util.conditional_resources import Condition
from aws_cdk import (
    aws_lambda as _lambda,
    custom_resources as _custom_resources,
    aws_ec2 as _ec2
)
from aws_cdk import (
    Aspects,
    Fn, 
    Duration,
    CfnMapping, 
    CfnCondition, 
    CustomResource,
    Duration,
    RemovalPolicy
)
import lib.util.override_rule as scan

class SendAnonymousData(Construct):

    @property
    def UUID(self):
        return self._uuid   

    def __init__(self,scope: Construct, id: str, vpc: _ec2.IVpc, codebucket: IBucket, s3_deploy, metrics) -> None:
        super().__init__(scope, id)

        self._metrics_mapping = CfnMapping(self, 'AnonymousData',mapping={'SendAnonymousData': {'Data': 'Yes'}})
        self._metrics_condition = CfnCondition(self, 'AnonymousDatatoAWS',
            expression=Fn.condition_equals(self._metrics_mapping.find_in_map('SendAnonymousData','Data'),'Yes')
        )

        self._helper_func = _lambda.SingletonFunction(self, 'SolutionHelper',
            uuid='75248a81-9138-468c-9ba1-bca6c7137599',
            runtime= _lambda.Runtime.PYTHON_3_8,
            handler= 'lambda_function.handler',
            description= 'This function generates UUID for each deployment and sends anonymous data to the AWS Solutions team',
            code= _lambda.Code.from_bucket(bucket=codebucket,key='app_code/solution_helper.zip'),
            vpc=vpc,
            timeout=Duration.seconds(30)
        )
        self._helper_func.add_dependency(s3_deploy)
        
        self._lambda_provider = _custom_resources.Provider(
            self, 'LambdaProvider',
            on_event_handler=self._helper_func,
            vpc=vpc
        )

        self._uuid = CustomResource(self, 'UUIDCustomResource',
            service_token=self._lambda_provider.service_token,
            properties={
                "Resource": "UUID"
            },
            resource_type="Custom::CreateUUID",
            removal_policy=RemovalPolicy.DESTROY
        )

        self._send_data = CustomResource(self, 'SendDataCustomResource',
            service_token=self._lambda_provider.service_token,
            properties={
                "Resource": "AnonymousMetric",
                "UUID": self._uuid.get_att_string("UUID"),
                "Solution": metrics["Solution"],
                "Data": metrics
            },
            resource_type= 'Custom::AnonymousData',
            removal_policy=RemovalPolicy.DESTROY
        )
        self._send_data.node.add_dependency(self._uuid)

        Aspects.of(self._helper_func).add(Condition(self._metrics_condition))
        Aspects.of(self._uuid).add(Condition(self._metrics_condition))
        Aspects.of(self._send_data).add(Condition(self._metrics_condition))