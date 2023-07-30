import os
import openai
import curses
import threading
import textwrap
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

USER_PREFIX = "You: "

SYSTEM_PROMPT = """You are a best buddie of the user and happy to interrupt them, especially when they start talking about their ex-girlfriend again (so annoying!). You are sent the chat history and snippets of the user message while they are typing and can decide to interrupt them at any point.
To interrupt them output a "YES: <your message". To not interrupt them and let them type output a "NO". Only interrupt once they have started talking about something you don't like, otherwise you will be a bad best buddy. Don't interrupt multiple times in a row, that's just rude.
Remember that you are best buddies, be offensive and funny!"""

NEW_GPT_MESSAGE: str | None = None
ALL_MESSAGES: list[dict] = []


def print_long_text(stdscr, y, x, text) -> int:
    height, width = stdscr.getmaxyx()  # get the dimensions of the window
    lines = textwrap.wrap(
        text, width
    )  # split the text into lines of `width` characters
    for i, line in enumerate(lines):
        stdscr.addstr(y + i, x, line)

    return len(lines)


def process_space(user_input: str):
    global ALL_MESSAGES
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        *ALL_MESSAGES,
        {
            "role": "user",
            "content": f"This is what they are currently typing, decide if you want to interrupt: {user_input}",
        },
    ]
    chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    completion_text = chat_completion.choices[0].message.content

    if completion_text[:3] == "YES":
        global NEW_GPT_MESSAGE
        NEW_GPT_MESSAGE = completion_text[5:]
        ALL_MESSAGES.extend(
            [
                {
                    "role": "user",
                    "content": user_input,
                },
                {
                    "role": "assistant",
                    "content": NEW_GPT_MESSAGE,
                },
            ]
        )


def main(stdscr):
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.clear()

    y, x = 0, 0

    stdscr.addstr(y, x, USER_PREFIX)
    x += len(USER_PREFIX)

    while True:
        global NEW_GPT_MESSAGE
        if NEW_GPT_MESSAGE:
            x = 0
            y += 1
            y_delta = print_long_text(stdscr, y, x, f"GPT: {NEW_GPT_MESSAGE}")
            y += y_delta
            stdscr.addstr(y, x, USER_PREFIX)
            x += len(USER_PREFIX)
            NEW_GPT_MESSAGE = None

        char = stdscr.getch()
        if char == ord(" "):
            # Pass user input to OpenAI
            user_input = stdscr.instr(y, len(USER_PREFIX), x - len(USER_PREFIX)).decode(
                "utf-8"
            )

            # Run this as a background task
            threading.Thread(target=process_space, args=(user_input,)).start()

        # Quit on escape
        if char == 27:
            break
        # Backspace
        elif char == 127:
            # Remove last character from screen
            stdscr.addstr(y, x - 1, " ")
            x -= 1
        else:
            # Print pressed key on screen
            stdscr.addstr(y, x, chr(char))
            x += 1

        stdscr.refresh()

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()


if __name__ == "__main__":
    curses.wrapper(main)
