import json
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from openai import OpenAI
from bardapi import Bard
import os
import sqlite3
import hashlib
import json

# Tải thông tin cấu hình từ .env
load_dotenv()

# Kết nối tới SQLite DB
conn = sqlite3.connect('fb.db')
c = conn.cursor()

# Tạo bảng để theo dõi bài viết đã xử lý
c.execute('''CREATE TABLE IF NOT EXISTS processed_posts (
             post_id TEXT PRIMARY KEY,
             email TEXT)''')

c.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id SERIAL PRIMARY KEY,
        post_id VARCHAR(255) NOT NULL,
        comment TEXT NOT NULL,
        is_commented BOOLEAN DEFAULT FALSE
    );
''')

conn.commit()

def get_post_id(post_content):
    return hashlib.sha256(post_content.encode()).hexdigest()

def has_been_processed(email, post_id):
    c.execute('SELECT * FROM processed_posts WHERE email=? AND post_id=?', (email, post_id))
    return c.fetchone() is not None

def mark_as_processed(email, post_id):
    c.execute('INSERT INTO processed_posts (post_id, email) VALUES (?, ?)', (post_id, email))
    conn.commit()

def call_ai_api(prompt, post_id):
    # Gọi API và xử lý kết quả
    # Kết quả là một mảng các bình luận
    try:
        client = OpenAI()

        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        return json.loads(completion.choices[0].message.content)

    except Exception as e:
        print("Có lỗi xảy ra khi gọi OpenAI API:", e)
        return []

def get_comment_from_db(post_id):
    # Hàm này sẽ truy vấn cơ sở dữ liệu để tìm bình luận chưa được đăng cho bài đăng
    try:
        c.execute("SELECT id, comment FROM comments WHERE post_id =? AND is_commented = FALSE LIMIT 1", (post_id,))
        result = c.fetchone()
        if result:
            comment_id, comment = result

            # Cập nhật trạng thái của bình luận
            c.execute("UPDATE comments SET is_commented = TRUE WHERE id = ?", (comment_id,))
            conn.commit()

            return comment
        else:
            return None
    except Exception as e:
        print("Có lỗi khi truy vấn cơ sở dữ liệu:", e)
        return None

def insert_comments_to_db(comments, post_id):
    # Hàm này sẽ chèn bình luận mới vào cơ sở dữ liệu
    try:
        for comment in comments:
            c.execute("INSERT INTO comments (post_id, comment, is_commented) VALUES (?, ?, FALSE)", (post_id, comment))
        conn.commit()
    except Exception as e:
        print("Có lỗi khi chèn dữ liệu vào cơ sở dữ liệu:", e)

def get_first_comment(post_id):
    # Hàm này sẽ lấy bình luận đầu tiên chưa được đăng từ cơ sở dữ liệu
    return get_comment_from_db(post_id)


def expand_post_content(driver, post):
    buttons = post.find_elements(By.XPATH, './/div[@role="button"]')
    for button in buttons:
        if button.text in ["Xem thêm", "See more"]:
            button.click()
            # time.sleep(1)
            break

def view_post_images(driver, post):
    images = post.find_elements(By.TAG_NAME, 'img')
    for img in images:
        alt = img.get_attribute('alt')
        if alt:
            driver.execute_script("arguments[0].click();", img)
            # time.sleep(2)
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            # time.sleep(1)

def react_to_post(driver, post):
    reactions = [["Love", "Yêu thích"], ["Care", "Thương thương"], ["Haha", "Haha"], ["Wow", "Wow"]]
    chosen_reaction = random.choice(reactions)

    try:
        like_button = post.find_element(By.XPATH, 
            './/div[not(contains(@class, "xzueoph"))]//div[@aria-label="Thích" or @aria-label="Like" or @aria-label="Remove Like" or @aria-label="Gỡ Thích"]')

        action = ActionChains(driver)
        action.move_to_element(like_button).perform()

        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, 
                f"//div[@role='button' and @aria-label='{chosen_reaction[0]}' or @aria-label='{chosen_reaction[1]}']"))
        )

        reaction_button = driver.find_element(By.XPATH, 
            f"//div[@role='button' and @aria-label='{chosen_reaction[0]}' or @aria-label='{chosen_reaction[1]}']")
        reaction_button.click()
    except Exception as e:
        print(f"Không thể thả reaction {chosen_reaction}: ", e)

def get_post_content(driver, post):
    try:
        post_content_div = post.find_element(By.XPATH, './/div[@dir="auto"]')
        post_content = post_content_div.get_attribute('innerText')
        return post_content
    except Exception as e:
        print("Có lỗi xảy ra khi đọc nội dung bài viết:", e)
        return None

def comment(driver, post):
    post_content = get_post_content(driver, post)
    post_id = get_post_id(post_content)  # Giả sử có hàm này để lấy ID của bài đăng
    if not post_content or not post_id:
        return  # Skip nếu không có nội dung hoặc ID

    comment_to_post = get_comment_from_db(post_id)

    if not comment_to_post:
        comment_prompt = """
Hãy đóng vai một facebook user, đang ở trong 1 group cộng đồng dev việt nam, hãy đọc post sau và viết 8 comments . Yêu cầu:
- response trả về chỉ gồm 1 dòng có format array string: ["cmt1", "cmt2",...]
- comment không hashtag
- comment không được quá 2 câu
- 2 comments liên quan đến bài viết 
- 2 comments không liên quan đến nội dung ví dụ hỏi  technical về blockchain, 
- 2 comments hỏi nhận định thị trường, coin xuất hiện trong bài viết (ví dụ nên bắt đáy k b?, giờ vào con A đc chưa ạ? mn giờ có hold con nào trong bài k ạ?)
- 2 comments chỉ đơn giản khen post hay,
- các comments đảo lộn xộn
- không sử dụng từ "các bạn", "các cậu", xưng "mình" và gọi "mọi người", nói chuyện  càng cộc lốc càng tốt, 
- không sử dụng các từ cảm thán ở cuối câu, 
- được phép nói bậy, sử dụng nhiều từ viết tắt thông dụng như cmnr, vliz, vcl,... 
- cố tình typo như con người, viết thường hết

        """
        comment_texts = call_ai_api(comment_prompt + post_content, post_id)
        if comment_texts:
            insert_comments_to_db(comment_texts, post_id)
            comment_to_post = get_first_comment(post_id)

    if comment_to_post:
        comment_button = post.find_element(By.XPATH, './/div[@role="button" and (@aria-label="Leave a comment" or @aria-label="Viết bình luận")]')
        comment_button.click()
        time.sleep(2)

        comment_field = post.find_element(By.XPATH, './/div[@role="textbox" and (@aria-label="Write an answer…" or @aria-label="Viết bình luận công khai…")]')
        comment_field.send_keys(comment_to_post)
        comment_field.send_keys(Keys.ENTER)

def process_account(email, password):
    options = Options()
    options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})
    driver = webdriver.Chrome(options=options)

    driver.get("https://www.facebook.com")
    driver.find_element(By.ID, "email").send_keys(email)
    driver.find_element(By.ID, "pass").send_keys(password)
    driver.find_element(By.NAME, "login").click()

    time.sleep(15)
    driver.get("https://www.facebook.com/groups/1196099411099406")
    time.sleep(5)

    start_time = time.time()
    count = 0
    while time.time() - start_time < 300 and count < 5:  # Chạy trong 5 phút và tương tác tối đa 5 bài posts
        posts = driver.find_elements(By.CLASS_NAME, "x1yztbdb.x1n2onr6.xh8yej3.x1ja2u2z")
        if count >= len(posts):
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.SPACE)
            continue
        post = posts[count]
        count += 1
        driver.execute_script("arguments[0].scrollIntoView();", post)
        time.sleep(1)
        expand_post_content(driver, post)
        time.sleep(1)
        post_content = get_post_content(driver, post)
        if not post_content:
            continue 
        post_id = get_post_id(post_content)
        if not has_been_processed(email, post_id):
            # Xử lý bài viết...
            view_post_images(driver, post)
            time.sleep(1)
            react_to_post(driver, post)
            time.sleep(1)
            comment_or_not = random.choice([0, 1])
            if comment_or_not:
                comment(driver, post)
                time.sleep(1)
            mark_as_processed(email, post_id) 

        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.SPACE)
        time.sleep(1)

    driver.quit()

import csv

with open('metadata.csv', 'r') as file:
    reader = csv.DictReader(file)
    accounts = list(reader)

for account in accounts:
    process_account(account['email'], account['password'])