import asyncio
import copy
from dataclasses import dataclass
import boto3
from botocore.config import Config
from botocore.exceptions import (
    UnauthorizedSSOTokenError,
    NoCredentialsError,
    ClientError,
)
import json
import os
import logging

from deployment_manager.utils.consts import display_error, display_info

logging.getLogger("botocore.credentials").setLevel(logging.CRITICAL)

MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

MODEL_PRICING_MAP = {
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0": {"input": 0.003, "output": 0.015}
}


def display_tokens_and_cost(
    message: str, input_tokens_total: int, output_tokens_total: int, price_total: float
):
    display_info(
        f"{message}\nInput tokens used: {input_tokens_total}\nOutput tokens used: {output_tokens_total}\nPricing: {price_total} $"
    )


@dataclass
class ModelResponse:
    text: str
    input_tokens: int
    output_tokens: int


class LLMHelper:
    def __init__(self):
        profile_name = os.environ.get("AWS_PROFILE") or "rossum-dev"
        self.session = boto3.Session(profile_name=profile_name)
        config = Config(
            max_pool_connections=100,
            read_timeout=1200,
            connect_timeout=20,
        )

        self.bedrock_runtime = self.session.client(
            "bedrock-runtime", region_name="us-west-2", config=config
        )

        self.payload_basis = {
            "anthropic_version": "bedrock-2023-05-31",
            "temperature": 0.5,
            "max_tokens": 5000,
            "top_p": 0.9,
        }

    @classmethod
    def calculate_pricing(cls, input_tokens, output_tokens):
        # Assumes Claude 3.7 pricing
        return (input_tokens / 1000) * MODEL_PRICING_MAP[MODEL_ID]["input"] + (
            output_tokens / 1000
        ) * MODEL_PRICING_MAP[MODEL_ID]["output"]

    async def run(self, prompt) -> ModelResponse:
        payload = copy.deepcopy(self.payload_basis)
        payload["messages"] = [{"role": "user", "content": prompt}]

        def blocking_call():
            response = self.bedrock_runtime.invoke_model(
                modelId=MODEL_ID, body=json.dumps(payload)
            )
            response_body = json.loads(response["body"].read())
            usage = response_body["usage"]

            return ModelResponse(
                text=response_body["content"][0]["text"],
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
            )

        try:
            return await asyncio.to_thread(blocking_call)
        except Exception as e:
            print(f"An error occurred: {e}")

    def validate_credentials(self):
        try:
            sts = self.session.client("sts")
            sts.get_caller_identity()
            return True
        except UnauthorizedSSOTokenError:
            display_error(
                "SSO credentials have expired. Run `aws sso login --profile rossum-dev`."
            )
            return False
        except NoCredentialsError:
            display_error(
                "No AWS credentials found. Set AWS_PROFILE or configure SSO. Run `aws sso login --profile rossum-dev`."
            )
            return False
        except ClientError as e:
            display_error(f"Credential error: {e.response['Error']['Message']}")
            return False
