import asyncio
import copy
import boto3
from botocore.config import Config
import json
import os


MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"


class LLMHelper:
    def __init__(self):
        profile_name = os.environ.get("AWS_PROFILE") or "rossum-dev"
        self.session = boto3.Session(profile_name=profile_name)
        config = Config(
            max_pool_connections=100,
            read_timeout=120,
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

    async def run(self, prompt):
        payload = copy.deepcopy(self.payload_basis)
        payload["messages"] = [{"role": "user", "content": prompt}]

        def blocking_call():
            response = self.bedrock_runtime.invoke_model(
                modelId=MODEL_ID, body=json.dumps(payload)
            )
            response_body = json.loads(response["body"].read())
            return response_body["content"][0]["text"]

        try:
            generated_text = await asyncio.to_thread(blocking_call)
            return generated_text
        except Exception as e:
            print(f"An error occurred: {e}")
