import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import TOKEN, CHAT_ID, LOTTERY_API_URL
from analyzer import *
import telegram.error
# 强制CMD打印日志
print("[INFO] 机器人启动成功！")
print("[INFO] 自动推送：5秒/次（稳定极速检测）")
print("[INFO] 等待开奖数据中...")
last_expect = None
def get_data():
    try:
        res = requests.get(LOTTERY_API_URL, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        data = res.json()
        if data and "data" in data and len(data["data"]) > 0:
            item = data["data"][0]
            return str(item["expect"]).strip(), int(item["openCode"].split(",")[-1])
    except Exception:
        return None, None
def build_msg(expect, num):
    # 先算所有的预测项目
    one, three, six = zodiac_recommend()
    wave = wave_analysis()
    size = size_analysis()
    odd = odd_even_analysis()
    # 🔥 均衡版25码+全联动：所有项目都参与，分布均衡
    nums = ultra_predict(one, three, six, wave, size, odd)
    sp = one_special(one)
    current_zodiac = NUM_TO_ZODIAC[num]
    # 🔥 计算下一期的预测期数！
    next_expect = str(int(expect) + 1)
    # 所有项目的战绩
    add_battle("25码", num in nums)
    add_battle("一肖", one == current_zodiac)
    add_battle("三肖", current_zodiac in three)
    add_battle("六肖", current_zodiac in six)
    add_battle("波色", (wave=="红波" and num in RED_WAVE) or (wave=="蓝波" and num in BLUE_WAVE) or (wave=="绿波" and num in GREEN_WAVE))
    add_battle("大小", (size=="大" and num>=25) or (size=="小" and num<25))
    add_battle("单双", (odd=="单" and num%2==1) or (odd=="双" and num%2==0))
    add_history(num)
    msg = f"""
🔥 小泽AI精准预测
━━━━━━━━━━━━━━━━━━━━
📅 上一期：{expect}
🎯 开奖：{num:02d} ({current_zodiac})
━━━━━━━━━━━━━━━━━━━━
📅 下一期预测：{next_expect}
━━━━━━━━━━━━━━━━━━━━
🎯 一肖中特：{one} {sp:02d}
🐲 三肖：{' '.join(three)}
🐲 六肖：{' '.join(six)}
━━━━━━━━━━━━━━━━━━━━
🌈 波色：{wave} | 📈 大小：{size} | ⚖️ 单双：{odd}
━━━━━━━━━━━━━━━━━━━━
📊 连对/连错战绩
25码：{get_streak('25码')} ｜ 一肖：{get_streak('一肖')}
三肖：{get_streak('三肖')} ｜ 六肖：{get_streak('六肖')}
波色：{get_streak('波色')} ｜ 大小：{get_streak('大小')}
单双：{get_streak('单双')}
━━━━━━━━━━━━━━━━━━━━
✅ 近10期战绩：
25码：{get_battle('25码')}
一肖：{get_battle('一肖')}
三肖：{get_battle('三肖')}
六肖：{get_battle('六肖')}
"""
    return msg, nums
async def predict(update: Update, context: ContextTypes):
    expect, num = get_data()
    if expect:
        msg, nums = build_msg(expect, num)
        await update.message.reply_text(msg)
        formatted_nums = [f"{x:02d}" for x in nums]
        await update.message.reply_text(f"🎯 25个精选特码\n{','.join(formatted_nums)}")
async def auto_push(context: ContextTypes.DEFAULT_TYPE):
    global last_expect
    try:
        expect, num = get_data()
        if expect and (last_expect is None or expect != last_expect):
            last_expect = expect
            msg, nums = build_msg(expect, num)
            formatted_nums = [f"{x:02d}" for x in nums]
            
            # 防超时发送消息
            await context.bot.send_message(chat_id=CHAT_ID, text=msg)
            await context.bot.send_message(chat_id=CHAT_ID, text=f"🎯 25个精选特码\n{','.join(formatted_nums)}")
            
            print(f"[SUCCESS] 期数 {expect} 推送完成，预测下一期 {int(expect)+1}")
    
    # 捕获超时错误，程序永不崩溃
    except telegram.error.TimedOut:
        print(f"[WARNING] 网络超时，下次重试！")
    except Exception as e:
        print(f"[ERROR] 运行异常：{str(e)}")
def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("predict", predict))
    # 5秒稳定极速检测
    application.job_queue.run_repeating(auto_push, interval=5, first=5)
    application.run_polling(drop_pending_updates=True)
if __name__ == "__main__":
    main()