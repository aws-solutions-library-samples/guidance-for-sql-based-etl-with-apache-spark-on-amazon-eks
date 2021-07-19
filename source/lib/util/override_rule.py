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
  
from aws_cdk.core import IConstruct

def suppress_cfnnag_rule(rule_id: str, reason: str, cnstrt: IConstruct):    
    cnstrt.add_metadata('cfn_nag',{
        "rules_to_suppress": [{
                "id": rule_id,
                "reason": reason
            }]
    })

def suppress_lambda_cfnnag_rule(cnstrt: IConstruct):
    cnstrt.add_metadata('cfn_nag',{
            "rules_to_suppress": [
                {
                    "id": "W58",
                    "reason": "service role has permission to write logs to CloudWatch"
                },
                {
                    "id": "W89",
                    "reason": "interal function does not need to associate to VPC"
                },
                {
                    "id": "W92",
                    "reason": "Setting up ReservedConcurrentExecutions is out of reach with the internal function created by CDK"
                }
            ]
        })

def suppress_network_cfnnag_rule(cnstrt: IConstruct):
    cnstrt.add_metadata('cfn_nag',{
      "rules_to_suppress": [
                {
                    "id": "W40",
                    "reason": "Egress IP Protocol of -1 is default and generally considered OK"
                },
                {
                    "id": "W5",
                    "reason": "The Security Group with cidr open considered OK"
                }
            ]
    })

def suppress_iam_cfnnag_rule(cnstrt: IConstruct):
    cnstrt.add_metadata('cfn_nag',{
      "rules_to_suppress": [
                {
                    "id": "W12",
                    "reason": "by default the role scaler_sa has * resource"
                },
                {
                    "id": "W76",
                    "reason": "standard IAM role offered by ALB ingress controller"
                }
            ]
    })   