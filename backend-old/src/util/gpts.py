import os
import openai
import aiolimiter

import asyncio
import anthropic
from typing import Any, List, Dict, Union
from tqdm.asyncio import tqdm_asyncio
import time
import dotenv
from anthropic import AsyncAnthropic

dotenv.load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]
OPENAI_CLIENT = openai.AsyncOpenAI()

async def _throttled_anthropic_chat_completion_acreate(
    client,   
    model: str,    
    messages: List[Dict[str, str]],    
    temperature: float,    
    max_tokens: int,    
    top_p: float,    
    stop: Union[str, List[str]],    
    limiter: aiolimiter.AsyncLimiter, ) -> Dict[str, Any]:      
    
    async with limiter:
        trial = 0
        while trial < 5:
            rate_limit = False
            try:                
                return await client.messages.create(                    
                    model=model,                    
                    messages=messages,                    
                    temperature=temperature,                    
                    max_tokens=max_tokens,                    
                    top_p=top_p
                    # response_format={"type": "json_object"}              
                )
            except anthropic.APIConnectionError as e:
                print("The server could not be reached")
                print(e.__cause__)  # an underlying Exception, likely raised within httpx.
            except anthropic.RateLimitError:
                print("A 429 status code was received; we should back off a bit.")
                rate_limit = True
            except anthropic.APIStatusError as e:
                print("Another non-200-range status code was received")
                print(e.status_code)
                print(e.response)
            trial += 1
            print("Retrying")
            if rate_limit:
                await asyncio.sleep(60)
            else:
                await asyncio.sleep(5)
            print("Start trial ", trial)
        return {"message": {"content": ""}} 


async def generate_from_anthropic_chat_completion(
    messages_list: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    stop: Union[str, List[str]],
    requests_per_minute: int = 300,
) -> List[str]:
    client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY")).with_options(max_retries=1)
    limiter = aiolimiter.AsyncLimiter(requests_per_minute)
    async_responses = [
        _throttled_anthropic_chat_completion_acreate(
            client=client,
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=stop,
            limiter=limiter,
        )
        for messages in messages_list
    ]
    responses = await tqdm_asyncio.gather(*async_responses)
    # return [x["choices"][0]["message"]["content"] for x in responses]
    return responses

async def _throttled_openai_chat_completion_acreate(
    client: openai.AsyncOpenAI,   
    model: str,    
    messages: List[Dict[str, str]],    
    temperature: float,    
    max_tokens: int,    
    top_p: float,    
    stop: Union[str, List[str]],    
    limiter: aiolimiter.AsyncLimiter, ) -> Dict[str, Any]:      
    
    async with limiter:
        trial = 0
        while trial < 5:
            try:                
                return await client.chat.completions.create(                    
                    model=model,                    
                    messages=messages,                    
                    temperature=temperature,                    
                    max_tokens=max_tokens,                    
                    top_p=top_p
                    # response_format={"type": "json_object"}              
                )
            except Exception as e:
                print(e)
                await asyncio.sleep(30*(trial+2))
            trial += 1
        return {"choices": [{"message": {"content": ""}}]}  


async def generate_from_openai_chat_completion(
    messages_list: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    stop: Union[str, List[str]],
    requests_per_minute: int = 300,
) -> List[str]:
    if model.startswith("gpt-4"):
        requests_per_minute = 200
    if "OPENAI_API_KEY" not in os.environ:
        raise ValueError(
            "OPENAI_API_KEY environment variable must be set when using OpenAI API."
        )
    limiter = aiolimiter.AsyncLimiter(requests_per_minute)
    
    async_responses = [
        _throttled_openai_chat_completion_acreate(
            client=OPENAI_CLIENT,
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=stop,
            limiter=limiter,
        )
        for messages in messages_list
    ]
    responses = await tqdm_asyncio.gather(*async_responses)
    # return [x["choices"][0]["message"]["content"] for x in responses]
    return responses

def _throttled_openai_chat_completion_create_sync(   
    model: str,    
    messages: List[Dict[str, str]],    
    temperature: float,    
    max_tokens: int,    
    top_p: float,    
    stop: Union[str, List[str]] ) -> Dict[str, Any]:      
        trial = 0
        while trial < 5:
            try:                
                return openai.ChatCompletion.create(                    
                    model=model,                    
                    messages=messages,                    
                    temperature=temperature,                    
                    max_tokens=max_tokens,                    
                    top_p=top_p,                    
                    stop=stop,                
                )            
            except Exception as e:
                print(e)
                time.sleep(30*(trial+2))
            trial += 1
        return {"choices": [{"message": {"content": ""}}]}  


def generate_from_openai_chat_completion_sync(
    messages_list: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    stop: Union[str, List[str]],
    requests_per_minute: int = 300,
) -> List[str]:
    if model == "gpt-4":
        requests_per_minute = 200
    if "OPENAI_API_KEY" not in os.environ:
        raise ValueError(
            "OPENAI_API_KEY environment variable must be set when using OpenAI API."
        )
    openai.api_key = os.environ["OPENAI_API_KEY"]
    # session = ClientSession()
    # openai.aiosession.set(session)
    sync_responses = [
        _throttled_openai_chat_completion_create_sync(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=stop
        )
        for messages in messages_list
    ]
    responses = sync_responses
    # await session.close()
    # return [x["choices"][0]["message"]["content"] for x in responses]
    return responses

def gpt(prompt, model="gpt-4", temperature=0, max_tokens=4096, n=1, stop=None) -> list:
    return gpts([prompt] * n, model=model, temperature=temperature, max_tokens=max_tokens, stop=stop)[0]

def gpts(prompts, model="gpt-4", temperature=0, max_tokens=4096, stop=None) -> list:
    messages_list = [[{"role": "user", "content": prompt}] for prompt in prompts]
    return chatgpts(messages_list, model=model, temperature=temperature, max_tokens=max_tokens, stop=stop)

def claude(prompts, model="claude-3-haiku-20240307", temperature=0, max_tokens=4096, stop=None, max_messages=200) -> list:
    messages_list = [[{"role": "user", "content": prompt}] for prompt in prompts]
    texts = []
    for i in range(0, len(messages_list), max_messages):
        responses =  asyncio.run(generate_from_anthropic_chat_completion(model=model, messages_list=messages_list[i: i + max_messages], temperature=temperature, max_tokens=max_tokens, top_p=1, stop=stop))
        texts.extend([x.content[0].text for x in responses])
    return texts

def chatgpt(messages, model="gpt-4", temperature=0.7, max_tokens=4096, n=1, stop=None) -> list:
    return chatgpts([messages] * n, model=model, temperature=temperature, max_tokens=max_tokens, stop=stop)[0]

def chatgpts(messages_list, model="gpt-4", temperature=0.7, max_tokens=4096, stop=None, max_messages=200) -> list:
    texts = []
    for i in range(0, len(messages_list), max_messages):
        responses =  asyncio.run(generate_from_openai_chat_completion(model=model, messages_list=messages_list[i: i + max_messages], temperature=temperature, max_tokens=max_tokens, top_p=1, stop=stop))
        texts.extend([x.choices[0].message.content for x in responses])
    return texts

def gpts_sync(prompts, model="gpt-4", temperature=0.7, max_tokens=4096, stop=None) -> list:
    messages_list = [[{"role": "user", "content": prompt}] for prompt in prompts]
    return chatgpts_sync(messages_list, model=model, temperature=temperature, max_tokens=max_tokens, stop=stop)


# def chatgpts(messages_list, model="gpt-4", temperature=0.7, max_tokens=1000, stop=None, max_messages=200) -> list:
#     texts = []
#     for i in range(0, len(messages_list), max_messages):
#         responses =  asyncio.run(generate_from_openai_chat_completion(model=model, messages_list=messages_list[i: i + max_messages], temperature=temperature, max_tokens=max_tokens, top_p=1, stop=stop))
#         texts.extend([x["choices"][0]["message"]["content"] for x in responses])

def chatgpts_sync(messages_list, model="gpt-4", temperature=0.7, max_tokens=1000, stop=None, max_messages=200) -> list:
    texts = []
    for i in range(0, len(messages_list), max_messages):
        responses =  generate_from_openai_chat_completion_sync(model=model, messages_list=messages_list[i: i + max_messages], temperature=temperature, max_tokens=max_tokens, top_p=1, stop=stop)
        texts.extend([x["choices"][0]["message"]["content"] for x in responses])
    # print(responses)
    # global completion_tokens, prompt_tokens
    # completion_tokens[model] += sum(x["usage"]["completion_tokens"] for x in responses if "usage" in x and "completion_tokens" in x["usage"])
    # prompt_tokens[model] += sum(x["usage"]["prompt_tokens"] for x in responses if "usage" in x and "prompt_tokens" in x["usage"])
    return texts

# def gpt_usage():
#     global completion_tokens, prompt_tokens, inference_time
#     cost = completion_tokens["gpt-4"] / 1000 * 0.06 + prompt_tokens["gpt-4"] / 1000 * 0.03
#     cost += completion_tokens["gpt-3.5-turbo"] / 1000 * 0.002 + prompt_tokens["gpt-3.5-turbo"] / 1000 * 0.0015
#     cost += completion_tokens["ft:gpt-3.5-turbo-0613:princeton-nlp::7tfMZt3A"] / 1000 * 0.012 + prompt_tokens["ft:gpt-3.5-turbo-0613:princeton-nlp::7tfMZt3A"] / 1000 * 0.016
#     return {"completion_tokens": completion_tokens, "prompt_tokens": prompt_tokens, "cost": cost, "time": inference_time}