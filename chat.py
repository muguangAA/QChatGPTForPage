import eventlet
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from graia.ariadne.app import Ariadne
from graia.ariadne.entry import config
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.model import Friend, Group
from graia.ariadne.message import Source


def timeout_handle():
    driver.refresh()


def new_chat():
    try:
        driver.implicitly_wait(5)
        new_chat = driver.find_element(by=By.XPATH, value='//*[@id="__next"]/div[1]/div[2]/div/div/nav/a[1]')
        new_chat.click()
        driver.implicitly_wait(1)
        driver.switch_to.alert.accept()
        return "创建新会话"
    except Exception:
        return "发生异常，找不到元素"


def select_chat(chat_name: str):
    try:
        driver.implicitly_wait(5)
        frame = driver.find_element(by=By.XPATH, value='//*[@id="__next"]/div[1]/div[2]/div/div/nav/div[3]/div')
        chats = frame.find_elements(by=By.TAG_NAME, value='a')
        for chat in chats:
            target = chat.find_element(by=By.CLASS_NAME, value='flex-1')
            if target.text == chat_name:
                chat.click()
                break
    except Exception:
        return "发生异常，找不到元素"


def list_all_chats():
    try:
        driver.implicitly_wait(5)
        frame = driver.find_element(by=By.XPATH, value='//*[@id="__next"]/div[1]/div[2]/div/div/nav/div[3]/div')
        chats = frame.find_elements(by=By.TAG_NAME, value='a')
        ans = ""
        cur = 1
        for chat in chats:
            target = chat.find_element(by=By.CLASS_NAME, value='flex-1')
            ans += str(cur) + '. ' + target.text + '\n'
            cur += 1
        ans -= '\n'
        return ans
    except Exception:
        return "发生异常，找不到元素"


def find_answer() -> str:
    try:
        driver.implicitly_wait(5)
        while driver.find_elements(by=By.CLASS_NAME, value='result-streaming') != []:
            continue
        return driver.find_elements(by=By.CLASS_NAME, value='markdown')[-1].text
    except Exception:
        return "发生异常，找不到元素"


def send_to_chatGPT(prompt: str) -> str:
    try:
        driver.implicitly_wait(5)
        text_box = driver.find_element(by=By.XPATH,
                                       value='//*[@id="__next"]/div[1]/div[1]/main/div[2]/form/div/div[2]/textarea')
        text_box.send_keys(prompt)
        submit_button = driver.find_element(by=By.XPATH,
                                            value='//*[@id="__next"]/div[1]/div[1]/main/div[2]/form/div/div[2]/button')
        submit_button.click()
    except Exception:
        return "发生未知异常"

    # 超时退出
    timeout = 120
    try:
        with eventlet.Timeout(timeout):
            answer = find_answer()
            return answer
    except eventlet.timeout.Timeout:
        timeout_handle()
        return "请求超时"


def retry(change_text=None):
    try:
        driver.implicitly_wait(5)
        base = driver.find_elements(by=By.CLASS_NAME, value='text-base')[-2]
        edit = base.find_elements(by=By.TAG_NAME, value='button')[-1]
        js = "var q=document.documentElement.scrollTop=10000"  # documentElement表示获取根节点元素
        driver.execute_script(js)
        hover = ActionChains(driver).move_to_element(base)
        hover.perform()
        edit.click()

        # 修改内容
        if change_text is not None:
            text_frame = base.find_element(by=By.TAG_NAME, value='textarea')
            text_frame.clear()
            text_frame.send_keys(change_text)

        driver.implicitly_wait(5)
        submit_button = base.find_elements(by=By.TAG_NAME, value='button')[-2]
        submit_button.click()
        return find_answer()
    except Exception:
        return "发生异常，找不到元素"


# 启动浏览器引擎
options = ChromeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9527")
driver = webdriver.Chrome(options=options)
# QQ 交互框架
app = Ariadne(
    config(
        verify_key="1234567890",  # 填入 VerifyKey
        account=3506836028,  # 你的机器人的 qq 号
    ),
)


# 群聊
# GroupTrigger = Annotated[MessageChain, MentionMe(config.trigger.require_mention != "at"), DetectPrefix(
#     config.trigger.prefix)] if config.trigger.require_mention != "none" else Annotated[
#     MessageChain, DetectPrefix(config.trigger.prefix)]

# @app.broadcast.receiver("GroupMessage")
# async def group_message_listener(group: Group, chain: GroupTrigger):
#     answer = send_to_chatGPT(chain.display)
#     await app.send_message(group, MessageChain([Plain(answer)]))


# 私聊
@app.broadcast.receiver("FriendMessage")
async def friend_message_listener(app: Ariadne, friend: Friend, message: MessageChain):
    text = message.display
    answer = ""
    # 刷新网页
    if text == "!refresh":
        driver.refresh()
        answer = "网页已刷新"
    # 获取最后一条记录
    elif text == "!last":
        answer = driver.find_elements(by=By.CLASS_NAME, value='markdown')[-1].text
    # 列出所有对话
    elif text == "!list":
        answer = list_all_chats()
    # 新建会话
    elif text == "!new chat":
        answer = new_chat()
    # 重试
    elif text.find("!retry") == 0:
        if "!retry" == text:
            answer = retry()
        else:
            answer = retry(text[7:])
    # 向chatGPT发送消息
    elif text.find("!loop") == 0:
        l = text.split(" ")
        for i in range(int(l[2])):
            answer = send_to_chatGPT(l[1])
            await app.send_message(friend, MessageChain([Plain(answer)]))
    else:
        answer = send_to_chatGPT(message.display)
    await app.send_message(friend, MessageChain([Plain(answer)]))
    # 实际上 MessageChain(...) 有没有 "[]" 都没关系


app.launch_blocking()
driver.quit()
