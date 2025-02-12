import json
import re


def generate(messages, client, model, temperature=0, top_p=1, json_format=False):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format={"type": "text"}
        if not json_format
        else {"type": "json_object"},
        top_p=top_p,
    )

    if response.choices is None:
        return str(response.error)

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
