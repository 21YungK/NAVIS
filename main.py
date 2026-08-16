from ollama import chat

from tools import list_files


MODEL = "qwen3.5:9b"
ASSISTANT_NAME = "NAVIS"

SYSTEM_PROMPT = f"""
You are {ASSISTANT_NAME}, a personal AI assistant running locally
on the user's computer.

You have access to controlled local tools.

Use tools when they are necessary to answer the user's request.
Do not claim that you inspected files unless you actually used a tool.

Be helpful, concise, accurate, and practical.
If you are unsure, say so clearly.
"""


TOOLS = [
    list_files,
]


AVAILABLE_TOOLS = {
    "list_files": list_files,
}


def get_response(messages):
    try:
        while True:
            response = chat(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                think=False,
                keep_alive="30m",
            )

            assistant_message = response.message

            messages.append(assistant_message)

            if not assistant_message.tool_calls:
                return assistant_message.content

            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                arguments = tool_call.function.arguments

                print(
                    f"\n[Tool] {function_name}({arguments})"
                )

                tool_function = AVAILABLE_TOOLS.get(function_name)

                if tool_function is None:
                    tool_result = {
                        "success": False,
                        "error": f"Unknown tool: {function_name}",
                    }

                else:
                    try:
                        tool_result = tool_function(**arguments)

                    except Exception as e:
                        tool_result = {
                            "success": False,
                            "error": str(e),
                        }

                messages.append(
                    {
                        "role": "tool",
                        "tool_name": function_name,
                        "content": str(tool_result),
                    }
                )

    except Exception as e:
        print(f"\n[Error] {e}\n")
        return None


def main():
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    print("=" * 40)
    print(f"  {ASSISTANT_NAME}")
    print(f"  Model: {MODEL}")
    print("=" * 40)
    print("Commands: /clear, /exit\n")

    while True:
        try:
            user_input = input("You: ").strip()

        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{ASSISTANT_NAME}: Goodbye.")
            break

        if not user_input:
            continue

        command = user_input.lower()

        if command in {"/exit", "exit", "quit", "/quit"}:
            print(f"{ASSISTANT_NAME}: Goodbye.")
            break

        if command == "/clear":
            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                }
            ]

            print("Conversation cleared.\n")
            continue

        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        assistant_message = get_response(messages)

        if assistant_message:
            print(f"\n{ASSISTANT_NAME}: {assistant_message}\n")


if __name__ == "__main__":
    main()