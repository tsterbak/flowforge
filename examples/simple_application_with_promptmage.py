from dotenv import load_dotenv
from openai import OpenAI

from promptmage import PromptMage, Prompt
from promptmage.storage import (
    InMemoryPromptBackend,
    InMemoryDataBackend,
    PromptStore,
    DataStore,
)


load_dotenv()


client = OpenAI(
    # base_url="http://192.168.0.51:11434/v1",
    # api_key="ollama",  # required, but unused
)

# Setup the prompt store and data store
prompt_store = PromptStore(backend=InMemoryPromptBackend())
# prompt_store.store_prompt(
#     Prompt(
#         prompt_id="extract_facts",
#         template_vars=["article"],
#         system="You are a helpful assistant.",
#         user="Extract the facts from this article and return the results as a markdown list:\n\n<article>{article}</article> Make sure to include all the important details and don't make up any information.",
#     )
# )
# prompt_store.store_prompt(
#     Prompt(
#         prompt_id="summarize_facts",
#         template_vars=["facts"],
#         system="You are a helpful assistant.",
#         user="Summarize the following facts into a single sentence:\n\n{facts}",
#     )
# )
data_store = DataStore(backend=InMemoryDataBackend())

# Create a new PromptMage instance
mage = PromptMage(
    name="fact-extraction", prompt_store=prompt_store, data_store=data_store
)


# Application code


@mage.step(name="extract", prompt_id="extract_facts")
def extract_facts(article: str, prompt: Prompt) -> str:
    """Extract the facts as a bullet list from an article."""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",  # "llama3:instruct",
        messages=[
            {"role": "system", "content": prompt.system},
            {
                "role": "user",
                "content": prompt.user.format(article=article),
            },
        ],
    )
    return response.choices[0].message.content


@mage.step(name="summarize", prompt_id="summarize_facts")
def summarize_facts(facts: str, prompt: Prompt) -> str:
    """Summarize the given facts as a single sentence."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",  # "llama3:instruct",
        messages=[
            {"role": "system", "content": prompt.system},
            {
                "role": "user",
                "content": prompt.user.format(facts=facts),
            },
        ],
    )
    return response.choices[0].message.content
