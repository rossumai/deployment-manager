import boto3
import json

session = boto3.Session(profile_name="rossum-dev")

# Initialize the Bedrock Runtime client
bedrock_runtime = session.client('bedrock-runtime', region_name='us-east-1')

# Claude 3 Sonnet model ID (as of March 2024)
model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'

# Define the user prompt
user_message = "Describe the purpose of a 'hello world' program in one line."

# Construct the payload
payload = {
    "anthropic_version": "bedrock-2023-05-31",
    "messages": [{"role": "user", "content": user_message}],
    "max_tokens": 512,
    "temperature": 0.5,
    "top_p": 0.9
}

# Convert to JSON string
body = json.dumps(payload)

# Call the model
try:
    response = bedrock_runtime.invoke_model(modelId=model_id, body=body)
    response_body = json.loads(response['body'].read())
    generated_text = response_body['content'][0]['text']
    print(generated_text)
except Exception as e:
    print(f"An error occurred: {e}")
