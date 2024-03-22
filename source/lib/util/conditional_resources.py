import jsii
from constructs import IConstruct
from aws_cdk import CfnCondition, CfnResource, IAspect

# This code enables `apply_aspect()` to apply conditions to a resource.
# This way we can provision some resources if a condition is true.
# For example, if PROVISIONTYPE parameter is 'Git' then we provision CodePipeline
# with it's source stage being CodeCommit or GitHub
# https://docs.aws.amazon.com/cdk/latest/guide/aspects.html


@jsii.implements(IAspect)
class Condition:
    def __init__(self, condition: CfnCondition):
        self._condition = condition

    def visit(self, node: IConstruct):
        child = node.node.default_child  # type: CfnResource
        if child:
            child.cfn_options.condition = self._condition
