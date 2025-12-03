from tqdm import tqdm
from ollama import AsyncClient
from course_aid.app.models.intructors import Instructor
from course_aid.app.config.db_connection import connect
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
        self.client = AsyncClient()
    async def chat(self, messages: list[dict]):

        content = []

        async for part in await self.client.chat(model=self.model, messages=messages, stream=True,
                                                   options = {
                                                       'system': self.system_prompt
                                                   }):
            content.append(part['message']['content'])

        return "".join(content)

    def create_summary_prompt(self, contents: list[str]):
        messages = []

        messages.append({'role': 'user', 'content': 'Generate only a one or two line summary of the following reviews on a professor.'
                                                   'The intent behind this summary is for the viewer (student) to understand how '
                                                    'professionally good/bad this professor is. Do not add any delimiters'})
        for content in contents[0]:
            messages.append({'role': 'user', 'content': content})

        return messages

    async def generate_consensus_summary(self, instructor_first: str, instructor_last: str):

        comments = Instructor.get_all_comments_for_instructor(self.conn.cursor(), instructor_first, instructor_last)

        if not comments:
            return "No reviews yet"

        else:
            messages = self.create_summary_prompt(comments)

            result = await self.chat(messages)
            return result

    async def process_all_instructors(self,rows):
        results = []
        for row in tqdm(rows, total=len(rows)):
            result = await self.generate_consensus_summary(row[0], row[1])
            results.append({"first": row[0], "last": row[1], "summary": result})
        return results


    def recommend_cirriculum(self):
        pass

    def recommend_professors_by_course(self):
        pass

    def positively_reviewed_professors(self):
        pass


# example usage
if __name__ == '__main__':
    deepseek = AssistantRoles()
    # query = '''
    #         select first_name, last_name \
    #         from instructors \
    #         '''
    #
    # cursor = deepseek.conn.cursor()
    # cursor.execute(query)
    # rows = cursor.fetchall()
    #
    # with open('summary_cache.json', 'r') as outfile:
    #     data = json.load(outfile)
    #
    #
    # new_summaries = asyncio.run(deepseek.process_all_instructors(rows))
    # data["data"].extend(new_summaries)
    #
    # with open('summary_cache.json', 'w') as outfile:
    #     json.dump(data, outfile, indent=2)


