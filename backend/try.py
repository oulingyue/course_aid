import ollama

response: ollama.ChatResponse = ollama.chat(model='deepseek-r1:8b', messages=[
    {
        'role': 'user',
        'content': 'Why is the sky blue',
    },

], stream=True, )


if __name__=='__main__':

    for part in response:
        print(part['message']['content'], end='\n\n', flush=True)