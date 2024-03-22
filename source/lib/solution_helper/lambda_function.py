import logging
import uuid
import requests
from copy import copy
from crhelper import CfnResource
from datetime import datetime

logger = logging.getLogger(__name__)
helper = CfnResource(json_logging=True, log_level='INFO')
METRICS_ENDPOINT = "https://metrics.awssolutionsbuilder.com/generic"

def _sanitize_data(resource_properties):
    resource_properties.pop("ServiceToken", None)
    resource_properties.pop("Resource", None)

    # Solution ID and unique ID are sent separately
    resource_properties["Data"].pop("Solution", None)
    resource_properties["Data"].pop("UUID", None)

    return resource_properties

@helper.create
@helper.update
@helper.delete
def custom_resource(event, _):
    # print("Received event: " + json.dumps(event, indent=2))
    request_type = event["RequestType"]
    resource_properties = event["ResourceProperties"]
    resource = resource_properties["Resource"]

    # One UUID per CFN deployment
    if resource == "UUID" and request_type == "Create":
        random_id = str(uuid.uuid4())
        helper.Data.update({"UUID":random_id})
    elif resource == "AnonymousMetric":
        try:
            metrics_data = _sanitize_data(copy(resource_properties))
            metrics_data["CFTemplate"]= request_type + "d"
            headers = {"Content-Type": "application/json"}
            payload = {
                "Solution": resource_properties["Solution"],
                "UUID": resource_properties["UUID"],
                "TimeStamp": datetime.utcnow().isoformat(),
                **metrics_data
            }
            logger.info(f'Sending payload: {payload}')
            response = requests.post(METRICS_ENDPOINT, json=payload, headers=headers)
            logger.info(f'Response from metrics endpoint: {response.status_code} {response.reason}')
        except requests.exceptions.RequestException:
            logger.exception("Could not send usage data")
        except Exception:
            logger.exception("Unknown error when trying to send usage data")

def handler(event, context):
    try:
        helper(event, context)
        return {"Data": helper.Data}
    except Exception as error:
        logger.exception("[handler] failed: {error}")

