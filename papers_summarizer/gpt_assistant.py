from openai import OpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.thread import Thread
from openai.types.beta.threads.run import Run
from openai.types.file_object import FileObject

import time

client = OpenAI()

assistant_name = "Paper summarizer"
instructions = """You are a PhD in Artificial Intelligence.
Your main hobby that brings you as lot of joy is to summarize and explain scientific AI-related papers to less experienced peers."""


# TODO: do not create assistants, use assistant_id
def create_assistant() -> Assistant:
    assistant = client.beta.assistants.create(
        name=assistant_name,
        instructions=instructions,
        tools=[{"type": "code_interpreter"}, {"type": "retrieval"}],
        model="gpt-4-0125-preview",  # TODO: temperature?
    )
    return assistant


def create_file_from_paper_pdf(path_to_pdf: str) -> FileObject:
    paper_file = client.files.create(file=open(path_to_pdf, "rb"), purpose="assistants")
    return paper_file


def create_thread(paper_file) -> Thread:
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": "I need help with understanding the content of this paper. Could you summarize it for me and answer my questions if I'll have any? In the end of your summary include a list of key takeaways please.",
                "file_ids": [paper_file.id],
            }
        ]
    )
    return thread


def create_run(assistant, thread) -> Run:
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions="Please address the user as Dude. Be patient and adapt to his style of writing.",
    )
    return run


import time


def single_run(assistant: Assistant, thread: Thread):
    run = create_run(assistant, thread)
    while run.status in ["queued", "in_progress", "cancelling"]:
        time.sleep(1)  # Wait for 1 second
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        return messages
    else:
        print(run.status)


def conversate(path_to_paper: str):
    assistant = create_assistant()
    paper_file = create_file_from_paper_pdf(path_to_paper)
    thread = create_thread(paper_file)
    while True:
        messages = single_run(assistant, thread)
        for enum, msg in enumerate(messages.data[::-1]):
            if enum % 2 == 0:
                print(f"You:\n{msg.content[0].text.value}")
            else:
                print(f"Assistant:\n{msg.content[0].text.value}")
        your_response = input("wdyt?")
        if your_response.lower().strip() == "end":
            break
        else:
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=your_response,
            )
    return messages


if __name__ == "__main__":
    # assistant = create_assistant()
    path_to_paper = "database/daily_papers/2024-03-14/2403.07918.pdf"
    # paper_file = create_file_from_paper_pdf(path_to_paper)
    # thread = create_thread(paper_file)
    # messages = single_run(assistant, thread)
#    run("database/daily_papers/2024-03-14/2403.07918.pdf")
