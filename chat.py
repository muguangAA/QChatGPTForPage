import asyncio
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from graia.ariadne.app import Ariadne
from graia.ariadne.entry import config
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.model import Friend


def send_to_chatGPT(prompt: str) -> str:
    text_box = driver.find_element(by=By.XPATH, value='//*[@id="__next"]/div[1]/div/main/div[2]/form/div/div[1]/textarea')
    text_box.send_keys(prompt)
    submit_button = driver.find_element(by=By.XPATH, value='//*[@id="__next"]/div[1]/div/main/div[2]/form/div/div[1]/button')
    submit_button.click()
    while driver.find_elements(by=By.CLASS_NAME, value='result-streaming') != []:
        continue
    answer = driver.find_elements(by=By.CLASS_NAME, value='markdown')[-1]
    return answer.text


options = ChromeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9527")
driver = webdriver.Chrome(options=options)
app = Ariadne(
    config(
        verify_key="1234567890",  # 填入 VerifyKey
        account=3506836028,  # 你的机器人的 qq 号
    ),
)

@app.broadcast.receiver("FriendMessage")
async def friend_message_listener(app: Ariadne, friend: Friend, message: MessageChain):
    answer = send_to_chatGPT(message.display)
    await app.send_message(friend, MessageChain([Plain(answer)]))
    # 实际上 MessageChain(...) 有没有 "[]" 都没关系


app.launch_blocking()
driver.quit()
