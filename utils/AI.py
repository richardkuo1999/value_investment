from groq import Groq
import yaml

def escape_markdown_v2(text: str) -> str:
    escape_chars = r'_*\[\]()~`>#+-=|{}.!'
    return ''.join(['\\' + c if c in escape_chars else c for c in text])

class GroqAI:
    def __init__(self):
        api_key = yaml.safe_load(open('token.yaml'))["GROQ_API_KEY"][0]
        self.groq = Groq(api_key=api_key)
        self.model = 'deepseek-r1-distill-qwen-32b' # Default model

    def switch_model(self):
        print()
        model_list = self.groq.models.list().data
        for idx, model in enumerate(model_list):
            model = model.to_dict()
            print(idx, f", Model: {model['id']}, owner: {model['owned_by']}, active: {model['active']}, Max Token: {model['max_completion_tokens']}")
        
        model_id = input("Enter the model index you want to use: ")
        self.model = model_list[int(model_id)].to_dict()['id']

    def talk(self, prompt, content, reasoning=False):   
        """
        Generate text using the Groq API.
        """
        response = self.groq.chat.completions.create(
        model = self.model,
        messages=[
            {"role": "user", "content": prompt + " " + content}
        ]
    )
        response = response.choices[0].message.content
        if reasoning:
            response = response.split("</think>")[-1]

        return response