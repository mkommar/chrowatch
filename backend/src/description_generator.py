import openai
import boto3
import ollama
import litellm
import json
import base64
from botocore.exceptions import ClientError
from datetime import datetime
from config import OPENAI_API_KEY, AWS_REGION

openai.api_key = OPENAI_API_KEY

class BedrockLanguageModel:
    def __init__(self, model_id, region=AWS_REGION):
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=region
        )
        self.model_id = model_id

    def generate(self, prompt, image_path=None):
        print(f"DEBUG: Generating response for prompt: {prompt}")
        try:
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 20000,
                "temperature": 0.7,
                "top_p": 0.9,
                "messages": [
                    {
                        "role": "user",
                        "content": []
                    }
                ]
            }

            if image_path:
                with open(image_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                request_body["messages"][0]["content"].append({
                    "type": "image",
                    "image": {
                        "format": "png",
                        "source": {
                            "bytes": base64_image
                        }
                    }
                })

            request_body["messages"][0]["content"].append({
                "type": "text",
                "text": prompt
            })

            json_payload = json.dumps(request_body)

            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json_payload
            )

            response_body = json.loads(response['body'].read())
            print(f"DEBUG: Raw response from Bedrock: {response_body}")

            content_array = response_body.get('content', [])
            if content_array and isinstance(content_array, list):
                generated_text = content_array[0].get('text', '')
                if not generated_text:
                    print(f"WARNING: Generated text is empty. Full response: {response_body}")
                    return "No response generated"
                print(f"DEBUG: Generated text: {generated_text}")
                return generated_text
            else:
                print(f"WARNING: Unexpected response format. Full response: {response_body}")
                return "Unexpected response format"

        except ClientError as e:
            print(f"ERROR: Failed to generate text with Bedrock: {str(e)}")
            return f"Error: {str(e)}"
        except Exception as e:
            print(f"ERROR: An unexpected error occurred: {str(e)}")
            return f"Error: {str(e)}"

# Initialize the Bedrock model
bedrock_model = BedrockLanguageModel("anthropic.claude-3-sonnet-20240229-v1:0")

def generate_temporal_description(events, model_type='gpt', model_name='gpt-3.5-turbo'):
    if not events:
        return None

    prompt = "Analyze the following sequence of events in a video segment, focusing on object detection, motion, and positioning. Pay special attention to any suspicious activities that might indicate theft:\n\n"
    for event in events:
        timestamp = f"{event['timestamp']:.2f}"
        if event['type'] == 'object_detected':
            prompt += f"- At {timestamp}s: {event['description']}\n"
        elif event['type'] == 'object_motion':
            prompt += f"- At {timestamp}s: {event['description']}\n"
        elif event['type'] in ['motion_detected', 'bright_scene', 'dark_scene', 'color_dominance']:
            prompt += f"- At {timestamp}s: {event['type']} - {event['description']}\n"

    prompt += "\nProvide a concise description of what's happening in this video segment, interpreting the events as if they might be showing security camera activity. Consider the following points:\n"
    prompt += "1. The number and types of objects (especially people) detected\n"
    prompt += "2. The movement and positioning of these objects over time\n"
    prompt += "3. Any suspicious patterns of movement or behavior\n"
    prompt += "4. Changes in lighting or scene composition that might be relevant\n"
    prompt += "Description:"
    try:
        if model_type == 'gpt':
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()

        elif model_type == 'bedrock':
            return bedrock_model.generate(prompt)

        elif model_type == 'ollama':
            response = ollama.generate(model=model_name, prompt=prompt)
            return response['response'].strip()

        elif model_type == 'litellm':
            response = litellm.completion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()

        else:
            raise ValueError("Unsupported model type")

    except Exception as e:
        print(f"Error generating description: {str(e)}")
        return None