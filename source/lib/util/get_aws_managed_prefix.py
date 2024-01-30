from aws_cdk import (Aws, aws_ec2 as ec2,aws_iam as iam, Fn)
from aws_cdk.custom_resources import (
    AwsCustomResource,
    AwsCustomResourcePolicy,
    PhysicalResourceId,
    AwsSdkCall
)
from constructs import Construct

class AwsManagedPrefixListProps:
    def __init__(self, name: str):
        """
        Name of the AWS managed prefix list.
        See: https://docs.aws.amazon.com/vpc/latest/userguide/working-with-aws-managed-prefix-lists.html#available-aws-managed-prefix-lists
        eg. com.amazonaws.global.cloudfront.origin-facing
        """
        self.name = name

class AwsManagedPrefixList(Construct):
    def __init__(self, scope: Construct, id: str, props: AwsManagedPrefixListProps):
        super().__init__(scope, id)
        res = AwsCustomResource(
            self, 'AWSCustomResource',
            on_create=self.create(props),
            policy=AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=['ec2:DescribeManagedPrefixLists'],
                    resources=['*'],
                ),
            ])
        )
        self.prefixlist_id=res.get_response_field("PrefixLists.0.PrefixListId")

    def create(self, props):
        custom_params = {
            'Filters': [
                {
                    'Name': 'prefix-list-name',
                    'Values': [props.name],
                },
            ]
        }

        return AwsSdkCall(
                service='EC2',
                action='describeManagedPrefixLists',
                parameters=custom_params,
                physical_resource_id=PhysicalResourceId.of(f"{id}-{Fn.select(0, Fn.split(':', self.node.addr))}"),
                region=Aws.REGION
        )

