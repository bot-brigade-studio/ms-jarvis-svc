from botbrigade_llm import LLMClient
import asyncio

client = LLMClient(api_key="prj_MyqCC5ZwSm6zjVSQ71Pw8Pa62AXGAORl")

# models = client.list_models()

# print(models)

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Tell me a joke"},
]

# response = client.responses.create(
#     model="claudia-1",
#     messages=messages,
#     max_tokens=100,
#     temperature=0.7,
# )
# print(response)


# async def stream_response():
#     async for chunk in await client.responses.acreate(
#         model="claudia-1",
#         messages=[{"role": "user", "content": "Tell me a story"}],
#         stream=True,
#     ):
#         print(chunk)


# asyncio.run(stream_response())

response = client.responses.create(
    model="claudia-1",
    messages=messages,
    max_tokens=100,
    temperature=0.7,
)
print("RESPONSE", response)
from app.utils.debug import debug_print

print("type", type(response))

content = response["choices"][0]["message"]["content"]

debug_print("content", content)
