import helper
import asyncio
from ollama import chat, AsyncClient
from db_connection import connect
from typing import List
class AssistantRoles:

    def __init__(self):
        self.conn = connect()
        self.model='deepseek-r1:8b'
        self.system_prompt=("You are a helpful assistant for a website that allows students to review and rate their professors."
                            "These are the tasks/questions that you can answer:"
                            "Recommend professors to learn from for a course"
                            "What are some of the positively reviewed professors ?"
                            "Recommend a cirriculum for a field' "
                            )

    async def chat(self, messages: list[dict]):

        async for part in await AsyncClient().chat(model=self.model, messages=messages, stream=True,
                                                   options = {
                                                       'system': self.system_prompt
                                                   }):

            print(part['message']['content'], end='', flush=True)

    def create_summary_prompt(self, contents: list[str]):
        messages = []

        messages.append({'role': 'user', 'content': 'Generate only a one or two line summary of the following reviews on a professor.'
                                                   'The intent behind this summary is for the viewer (student) to understand how '
                                                    'professionally good/bad this professor is. Do not add any delimiters'})
        for content in contents[0]:
            messages.append({'role': 'user', 'content': content})

        return messages

    def generate_consensus_summary(self, instructor_first: str, instructor_last: str):

        comments = helper.get_all_comments_for_instructor(self.conn.cursor(), instructor_first, instructor_last)

        if not comments:
            print('No comments found for this instructor')

        else:
            messages = self.create_summary_prompt(comments)

            asyncio.run(self.chat(messages))

    def recommend_cirriculum(self):
        pass

    def recommend_professors_by_course(self):
        pass

    def positively_reviewed_professors(self):
        pass


# example usage
if __name__ == '__main__':
    deepseek = AssistantRoles()
    deepseek.generate_consensus_summary('Maria', 'Garcia')

