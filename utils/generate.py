import json

def generate(messages, client, model, json_format=False, temperature=0):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format={"type": "text"} if not json_format else {"type": "json_object"}
    )

    if json_format:
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Print the raw content for debugging
            print("Non-JSON response received:\n", content)
            raise 

    return response.choices[0].message.content