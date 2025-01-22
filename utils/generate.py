import json
import re


def generate(messages, client, model, json_format=False, temperature=0):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format={"type": "text"}
        if not json_format
        else {"type": "json_object"},
    )

    if response.choices is None:
        return str(response.error["metadata"])

    if json_format:
        content = response.choices[0].message.content
        # print(content)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return extract_json(content)

    return response.choices[0].message.content


def extract_json(text):
    # Try to find JSON-like content within triple backticks
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # If no triple backticks, try to find outer-most curly braces
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            return None

    # Try to parse the extracted string as JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("Non-JSON response received:\n", text)
        raise
