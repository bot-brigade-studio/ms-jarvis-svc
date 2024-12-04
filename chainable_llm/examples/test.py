import openai
import os

bbproxy_api_key = os.getenv("BBPROXY_API_KEY")
bbproxy_llm_url = os.getenv("BBPROXY_LLM_URL")
openai_api_key = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key="vk-ZBPIfHrBc6MBX-ZjUs-AL5Wp0Sh4-emlftEltsY6uh9yv", base_url="https://bbproxy.botbrigade.id/api")


response = client.chat.completions.create(
    model="gpt-4o-mini",
    max_tokens=4000,
    temperature=0.5,
    messages=[
        {
            "role":"system", 
            "content":"You are a pirate"
        }, 
        {
            "role":"user", 
            "content":"Hi"
            }
    ]
)

print("response", response)

result = response.choices[0].message.content
print(result)