import asyncio
from playwright.async_api import async_playwright
import os
import csv
import json

# 文件名配置
AUTH_FILE = "zhihu_auth.json"
CSV_FILE = "zhihu_data.csv"
JSON_FILE = "zhihu_data.json"

async def run():
    async with async_playwright() as p:
        # 1. 启动浏览器
        browser = await p.chromium.launch(headless=False)
        
        if not os.path.exists(AUTH_FILE):
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://www.zhihu.com/signin")
            print("请在浏览器窗口中完成登录...")
            await page.wait_for_selector(".AppHeader-profileAvatar", timeout=0) 
            await context.storage_state(path=AUTH_FILE)
            print("登录状态已保存！")
        else:
            context = await browser.new_context(storage_state=AUTH_FILE)
            page = await context.new_page()
            
            # 跳转到关注页/动态页 这里我用我自己的账号来测试，你可以换成自己的
            await page.goto("https://www.zhihu.com/people/ooo_ooo_ooo")
            await page.wait_for_load_state("networkidle")

            # 准备 CSV 文件：写入表头
            with open(CSV_FILE, mode='w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['标题', '链接', '点赞数', '评论数', '发布时间'])
                items = [] #动态列表
                item_last = 0 #旧动态数量

                print("--- 正在获取动态并写入 CSV 和 JSON ---")
                #设置一个“持续相等”的计数器,如果动态数量在连续5波的抓取中不变,则认为已经加载完成
                count = 0
                # 抓取波数
                i = 0
                while True:
                    i += 1
                    await page.mouse.wheel(0, 3000)
                    await page.wait_for_timeout(2000)

                    # 获取动态数量
                    items = await page.query_selector_all(".List-item") #获取动态列表
                    print(f"正在处理第 {i+1} 波数据,当前检测到 {len(items)} 条动态...")
                    
                    #如果动态数量在连续3波的抓取中不变,则认为已经加载完成
                    if item_last!=len(items): #新旧数量不等,则认为有新动态
                        item_last = len(items) #把新数量赋值给旧数量
                        count = 0 #相同次数清零
                        continue
                    else:
                        if(count < 5): #如果相同次数大于5,则认为已经加载完成
                            count += 1 #相同次数自增
                            continue
                        else:
                            break #如果相同次数大于5,则认为已经加载完成,退出循环
                
                for item in items: #遍历动态列表
                    # --- 提取逻辑 ---
                    title_el = await item.query_selector(".ContentItem-title a, .QuestionItem-title")
                    title = (await title_el.inner_text()).strip() if title_el else "（无标题）"

                    link = ""
                    if title_el:
                        raw_link = await title_el.get_attribute("href")
                        if raw_link:
                            link = raw_link if raw_link.startswith("http") else f"https:{raw_link}"

                    upvote_el = await item.query_selector('meta[itemprop="upvoteCount"]')
                    upvote_count = await upvote_el.get_attribute("content") if upvote_el else "0"

                    comment_el = await item.query_selector(".ContentItem-action:has-text('评论')")
                    comment_text = await comment_el.inner_text() if comment_el else "0"
                    comment_count = "".join(filter(str.isdigit, comment_text)) or "0"

                    display_time_el = await item.query_selector(".ActivityItem-meta span:nth-child(2)")
                    display_time = await display_time_el.inner_text() if display_time_el else "时间未知"

                    # --- 在 CSV 和 JSON 中写入数据 ---
                    writer.writerow([title, link, upvote_count, comment_count, display_time])
                    json.dump([title, link, upvote_count, comment_count, display_time], open(JSON_FILE, 'a', encoding='utf-8'), ensure_ascii=False)
                print(f"🎉 完成！数据已保存至 {CSV_FILE} 和 {JSON_FILE}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())