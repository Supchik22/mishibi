import json
import os
import random
from webview.errors import JavascriptException
import webview
from groq import Groq
import webview.js



# Глобальні змінні
levenshtein_cache = {}

def load_all_messages(folder: str) -> list:
    files = os.listdir(folder)
    all_messages = []

    for filename in files:
        path = os.path.join(folder, filename)
        with open(path, 'r', encoding='utf-8') as file:
            all_messages.extend(json.load(file)["messages"])

    print(f"Загальна кількість повідомлень: {len(all_messages)}")
    return all_messages

def levenshtein_distance(str1, str2):
    key = (str1, str2)
    if key in levenshtein_cache:
        return levenshtein_cache[key]
    
    len_str1, len_str2 = len(str1), len(str2)
    dp = [[0] * (len_str2 + 1) for _ in range(len_str1 + 1)]

    for i in range(len_str1 + 1):
        dp[i][0] = i
    for j in range(len_str2 + 1):
        dp[0][j] = j

    for i in range(1, len_str1 + 1):
        for j in range(1, len_str2 + 1):
            cost = 0 if str1[i - 1] == str2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost
            )

    distance = dp[len_str1][len_str2]
    levenshtein_cache[key] = distance
    return distance

def build_reply_cache(messages: list) -> dict:
    reply_cache = {}
    id_to_msg = {msg["id"]: msg for msg in messages}

    for idx, msg in enumerate(messages):
        if msg.get("type") != "service":
            reply_id = msg.get("reply_to_message_id")
            replied_msg = id_to_msg.get(reply_id)
            
            if replied_msg and replied_msg.get("text"):
                if type(replied_msg["from"]) != str:
                    replied_msg["from"] = "No name"
                reply_cache[msg["id"]] = str(replied_msg["from"])+" каже невідомим голосом на це  : "+str(replied_msg["text"])
            else:
                
                if idx + 1 < len(messages):
                    next_msg = messages[idx + 1]
                    if next_msg.get("text"):
                        if type(next_msg["from"]) != str:
                            next_msg["from"] = "No name"
                        reply_cache[msg["id"]] = str(next_msg["from"])+" каже невідомим голосом на це : "+str(next_msg["text"])
                        
    return reply_cache


def find_closest_message(user_input: str, messages: list, max_distance: int = 10):
    closest_msg = None
    min_distance = max_distance

    for msg in messages:
        rishi = []
        if type(msg.get("text")) != str:

            continue
        


        distance = levenshtein_distance(msg["text"].lower(), user_input.lower())

        if distance < min_distance:
            min_distance = distance
            closest_msg = msg

        #print("інфо і прогрес : ", msg["id"], " ", distance, " ", min_distance, " ", closest_msg["id"] if closest_msg else None)

    return closest_msg

def prompt(user_input: str):
    print("User input:", user_input)
    messages = load_all_messages("info")
    reply_cache = build_reply_cache(messages)

    closest_msg = find_closest_message(user_input, messages)

    if closest_msg:
        msg_text = closest_msg["text"]
        msg_id = closest_msg["id"]
        reply_text = reply_cache.get(msg_id)

        if reply_text is None or reply_text == "No reply found":
            # Якщо немає відповіді — беремо початок оригінального повідомлення
            reply_text = generate_completion(msg_text, user_input)
        else:
            reply_text = generate_completion(reply_text, user_input) 
            
        
        window.run_js(f"receiveMessage(`{reply_text}`)")
        print("\tЙОу\n "+reply_text,"\t Орігінал: \n",msg_text )
    else:
        reply_text = generate_completion(message_text=str(messages[random.randrange(1,len(messages)-1)]["text"]), user_input=user_input)
        
        window.run_js(f"receiveMessage(`{reply_text}`)")
        

    with open("messages_repl_cache.json", "w", encoding="utf-8") as cache_file:
        json.dump(reply_cache, cache_file, ensure_ascii=False, indent=2)

import difflib

from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))
chat_history = []  # Історія чату зберігається тут

def generate_completion(message_text: str, user_input: str) -> str:
    global chat_history  # Щоб змінювати глобальну історію
    print("\n \n"+ str(message_text)+  "\n \n")
    # Спочатку додамо системне повідомлення лише один раз
    if not chat_history:
        chat_history.append({
            "role": "system",
            "content": "ти на українській спілкуєшся! ",
        })

    # Додаємо нове повідомлення користувача до історії
    chat_history.append({
        "role": "user",
        "content": user_input + ". Можлива ваша відповідь: " + message_text,
    })

    stream = client.chat.completions.create(
        messages=chat_history,
        model="llama-3.3-70b-versatile",
        temperature=0.5,
        top_p=1,
        stop=None,
        stream=True,
    )

    r = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            r += str(chunk.choices[0].delta.content)

    # Після відповіді бота додаємо її теж до історії
    chat_history.append({
        "role": "assistant",
        "content": r,
    })

    return r



class Api:
    def send_prompt(self, name):
        prompt(name)



html_file = os.path.abspath('main.html')
file_url = f'file://{html_file}'

window = webview.create_window('Chat Mishibi', file_url,js_api=Api())
webview.start()


if __name__ == "__main__":
    pass
