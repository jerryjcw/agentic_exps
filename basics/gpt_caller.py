import os
from openai import OpenAI
import sys

# Use english comments only, don't use chinese comments.
# The api key is stored in a file, given as sys.argv[1], read it out and set it as the OpenAI API key.
def check_file_validity(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} does not exist, please check the path.")
    if not os.path.isfile(file_path):
        raise ValueError(f"Path {file_path} is not a file, please provide a valid file path.")


# If file path is none or there's an exception reading the api key file, use the environment variable OPENAI_API_KEY to be the api key.
# If the file reading is unsuccessful and the environment variable is not set, raise an exception with a message to the user.
def get_api_key(file_path: str):
    # Get current working directory
    current_dir = os.getcwd()
    # If file_path is None, use the environment variable OPENAI_API_KEY
    if file_path is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("No API key provided. Please set the OPENAI_API_KEY environment variable or provide a valid file path.")
        return api_key
    # Check if the file exists and is a valid file
    check_file_validity(file_path)
    # Read the API key from the file
    try:
        with open(file_path, 'r') as file:
            api_key = file.read().strip()
            if not api_key:
                raise ValueError("API key file is empty. Please provide a valid API key.")
            return api_key
    except Exception as e:
        raise ValueError(f"Error reading API key file: {e}")


# Create a function to return an openAI client instance, input parameters is the api key file path.
def get_openai_client(key_file_path) -> OpenAI:
    api_key = get_api_key(key_file_path if key_file_path else None)
    return OpenAI(api_key=api_key)


# Create a wrapper function to answer a question using a chatgpt model, default to gpt-4o.
# The inputs are 1) the model type string, and 2) the question string.
# It will return the answer string.
def ask_chatgpt(key_file: str = None, model_type: str = "gpt-4o", question: str = "Answer 123 + 456") -> str:
    client = get_openai_client(key_file_path=key_file)
    response = client.chat.completions.create(
        model=model_type,                  # Specify the model to use
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ],
        temperature=0.7,              # Randomness of the response (0.0 ~ 1.0)
        max_tokens=500,               # Maximum number of tokens to return
        n=1,                           # Number of responses to return
        stop=None                      # Stop sequence (optional)
    )
    # Get the response text
    return response.choices[0].message.content


# Initialize OpenAI client
def run(question: str):
    return ask_chatgpt(key_file=sys.argv[1] if len(sys.argv) > 1 else None, question=question)


if __name__ == "__main__":
    # Example usage:
    question = "請簡要說明 GPT-4o 模型的新功能有哪些？" if len(sys.argv) < 3 else sys.argv[2]
    answer = run(question)
    print("User Prompt:", question)
    print("GPT-4o Response:", answer)
