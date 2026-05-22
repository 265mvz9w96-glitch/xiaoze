from collections import deque, Counter
import random
import json
import os
# 固定配置
HISTORY = deque(maxlen=40)
BATTLE_RECORD = {}
STREAK = {
    "25码": {"连续": 0, "状态": True},
    "一肖": {"连续": 0, "状态": True},
    "三肖": {"连续": 0, "状态": True},
    "六肖": {"连续": 0, "状态": True},
    "波色": {"连续": 0, "状态": True},
    "大小": {"连续": 0, "状态": True},
    "单双": {"连续": 0, "状态": True},
}
# ==============================================
# 🔥 本地持久化：自动加载/保存历史记录
# ==============================================
DATA_FILE = "local_history.json"
def save_data():
    """把内存里的记录保存到本地文件"""
    save_data = {
        "history": list(HISTORY),
        "battle_record": {k: list(v) for k,v in BATTLE_RECORD.items()},
        "streak": STREAK
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

def load_data():
    """启动的时候加载本地历史记录"""
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        global HISTORY, BATTLE_RECORD, STREAK
        HISTORY = deque(data["history"], maxlen=40)
        BATTLE_RECORD = {k: deque(v, maxlen=10) for k,v in data["battle_record"].items()}
        STREAK = data["streak"]
        
        # 自动补全新增的项目
        new_items = ["三肖", "六肖"]
        for item in new_items:
            if item not in STREAK:
                STREAK[item] = {"连续": 0, "状态": True}
        
        print(f"[INFO] 已加载本地历史记录：{len(HISTORY)}期开奖数据")
    except Exception as e:
        print(f"[WARNING] 加载本地记录失败，将重新开始：{str(e)}")

# 启动的时候自动加载
load_data()
# ==============================================
# 🔥 你的专属生肖表（永久不变）
# ==============================================
ZODIAC_MAP = {
    "鼠": [7,19,31,43],
    "牛": [6,18,30,42],
    "虎": [5,17,29,41],
    "兔": [4,16,28,40],
    "龙": [3,15,27,39],
    "蛇": [2,14,26,38],
    "马": [1,13,25,37,49],
    "羊": [12,24,36,48],
    "猴": [11,23,35,47],
    "鸡": [10,22,34,46],
    "狗": [9,21,33,45],
    "猪": [8,20,32,44]
}
NUM_TO_ZODIAC = {n:z for z,ns in ZODIAC_MAP.items() for n in ns}
# 波色数据 不变
RED_WAVE = {1,2,7,8,12,13,18,19,23,24,29,30,34,35,40,45,46}
BLUE_WAVE = {3,4,9,10,14,15,20,25,26,31,36,37,41,42,47,48}
GREEN_WAVE = {5,6,11,16,17,21,22,27,28,32,33,38,39,43,44,49}
# ==============================================
# 🔥 计算项目的遗漏值
# ==============================================
def get_item_miss(item, check_func):
    """计算某个项目多久没开了"""
    history = list(HISTORY)
    for i, n in enumerate(reversed(history)):
        if check_func(n):
            return i
    return len(history) + 1
# ==============================================
# 🔥 计算整体走势：最近是热号周期还是冷号周期
# ==============================================
def get_trend_adjust():
    if len(HISTORY) <5:
        return 1.0
    # 最近5期的平均遗漏
    recent_miss = []
    for n in list(HISTORY)[-5:]:
        miss = len(HISTORY) +1 if n not in HISTORY else len(HISTORY) - HISTORY.index(n)
        recent_miss.append(miss)
    avg_miss = sum(recent_miss)/len(recent_miss)
    # 如果最近平均遗漏小，说明是热号周期，调整冷号权重
    if avg_miss <3:
        return 0.8  # 热号周期，冷号权重降低
    elif avg_miss >8:
        return 1.2  # 冷号周期，冷号权重提高
    else:
        return 1.0  # 正常周期
# ==============================================
# 🔥 计算每个项目的准确率：结合最近走势！
# ==============================================
def get_accuracy(key):
    records = BATTLE_RECORD.get(key, [])
    if not records:
        return 0.7  # 初始默认70%准确率
    # 1. 近10期的平均准确率
    avg_acc = records.count("✅") / len(records)
    # 2. 最近3期的准确率（走势权重更高）
    recent_records = list(records)[-3:] if len(records)>=3 else records
    recent_acc = recent_records.count("✅") / len(recent_records)
    # 3. 加权：最近3期占60%，历史平均占40%，自动跟上走势
    final_acc = recent_acc * 0.6 + avg_acc * 0.4
    return final_acc
# ==============================================
# 🔥 获取上一期的信息，用来防重肖重号
# ==============================================
def get_last_info():
    if len(HISTORY) ==0:
        return None, None  # 没有上一期
    last_num = HISTORY[-1]
    last_zodiac = NUM_TO_ZODIAC[last_num]
    return last_num, last_zodiac
# ==============================================
# 🔥 终极AI评分：所有联动、防重都保留
# ==============================================
def ai_score(num, predict_one=None, predict_three=None, predict_six=None, predict_wave=None, predict_size=None, predict_odd=None):
    history = list(HISTORY)
    if not history:
        return random.uniform(75, 98)
    
    # 🔥 防重号：上一期的数字，给它加20分的惩罚，让它很难被选到，但是不会完全排除
    last_num, _ = get_last_info()
    repeat_penalty = 0
    if last_num and num == last_num:
        repeat_penalty = 20  # 惩罚20分，正常情况下不会被选到，但是如果其他分够高，还是能上
    
    # 基础遗漏和频率，缩小系数，避免得分过高
    miss = len(history) + 1 if num not in history else len(history) - history.index(num)
    freq = history.count(num)
    consecutive = 0
    for i in reversed(history):
        if i == num:
            consecutive +=1
        else:
            break
    section = 1.0 if 1 <= num <=16 else 1.05 if 17 <= num <=33 else 1.0  # 缩小section系数
    base = 50
    
    # 缩小系数，避免得分过高
    miss_score = miss * 0.8
    freq_score = (10 - freq) * 3
    consec_penalty = consecutive * 2
    lucky = 3 if miss in [7,14,21,28] else 0
    
    # 🔥 全项目联动！所有项目都参与，权重跟着走势的准确率变！
    link_bonus = 0
    
    # 1. 一肖：根据最近走势的准确率调整权重
    acc_one = get_accuracy("一肖")
    if predict_one and num in ZODIAC_MAP[predict_one]:
        link_bonus += 5 * acc_one
    
    # 2. 三肖：根据最近走势的准确率调整权重
    acc_three = get_accuracy("三肖")
    if predict_three and NUM_TO_ZODIAC[num] in predict_three:
        link_bonus += 3 * acc_three
    
    # 3. 六肖：根据最近走势的准确率调整权重
    acc_six = get_accuracy("六肖")
    if predict_six and NUM_TO_ZODIAC[num] in predict_six:
        link_bonus += 1.5 * acc_six
    
    # 4. 波色：根据最近走势的准确率调整权重
    acc_wave = get_accuracy("波色")
    if predict_wave:
        if (predict_wave == "红波" and num in RED_WAVE) or \
           (predict_wave == "蓝波" and num in BLUE_WAVE) or \
           (predict_wave == "绿波" and num in GREEN_WAVE):
            link_bonus += 2 * acc_wave
    
    # 5. 大小：根据最近走势的准确率调整权重
    acc_size = get_accuracy("大小")
    if predict_size:
        if (predict_size == "大" and num >=25) or (predict_size == "小" and num <25):
            link_bonus += 1.5 * acc_size
    
    # 6. 单双：根据最近走势的准确率调整权重
    acc_odd = get_accuracy("单双")
    if predict_odd:
        if (predict_odd == "单" and num%2==1) or (predict_odd == "双" and num%2==0):
            link_bonus += 1.5 * acc_odd
    
    # 总分，减去重号的惩罚
    total = (base + miss_score + freq_score + lucky + link_bonus - consec_penalty - repeat_penalty) * section
    return round(max(total, 10), 2)
# ==============================================
# 🔥 均衡版数字推荐：三个区间各选，保证分布均衡
# ==============================================
def get_balanced_top(p_one=None, p_three=None, p_six=None, p_wave=None, p_size=None, p_odd=None):
    # 把数字分成三个区间，保证均衡分布
    low_nums = list(range(1, 17))    # 1-16，选8个
    mid_nums = list(range(17, 34))   # 17-33，选9个
    high_nums = list(range(34, 50))  # 34-49，选8个
    
    # 每个区间内部，按AI得分排序，选每个区间里得分最高的
    low_sorted = sorted(low_nums, key=lambda x: ai_score(x, p_one, p_three, p_six, p_wave, p_size, p_odd), reverse=True)
    mid_sorted = sorted(mid_nums, key=lambda x: ai_score(x, p_one, p_three, p_six, p_wave, p_size, p_odd), reverse=True)
    high_sorted = sorted(high_nums, key=lambda x: ai_score(x, p_one, p_three, p_six, p_wave, p_size, p_odd), reverse=True)
    
    # 每个区间选前N个，8+9+8=25，刚好均衡
    selected = low_sorted[:8] + mid_sorted[:9] + high_sorted[:8]
    return selected

def hot_numbers(p_one=None, p_three=None, p_six=None, p_wave=None, p_size=None, p_odd=None):
    all_sorted = get_balanced_top(p_one, p_three, p_six, p_wave, p_size, p_odd)
    return all_sorted[:10]
def warm_numbers(p_one=None, p_three=None, p_six=None, p_wave=None, p_size=None, p_odd=None):
    all_sorted = get_balanced_top(p_one, p_three, p_six, p_wave, p_size, p_odd)
    return all_sorted[10:18]
def cold_numbers(p_one=None, p_three=None, p_six=None, p_wave=None, p_size=None, p_odd=None):
    all_sorted = get_balanced_top(p_one, p_three, p_six, p_wave, p_size, p_odd)
    return all_sorted[18:25]
def ultra_predict(p_one=None, p_three=None, p_six=None, p_wave=None, p_size=None, p_odd=None):
    final = hot_numbers(p_one, p_three, p_six, p_wave, p_size, p_odd) + warm_numbers(p_one, p_three, p_six, p_wave, p_size, p_odd) + cold_numbers(p_one, p_three, p_six, p_wave, p_size, p_odd)
    return sorted(final)
# ==============================================
# 🔥 生肖推荐：防重肖只降权重，不排除！
# ==============================================
def zodiac_recommend():
    z_list = list(ZODIAC_MAP.keys())
    # 所有生肖都保留，不会排除上一期的，只是给它降分
    _, last_zodiac = get_last_info()
    
    if len(HISTORY) >= 5:
        zodiac_miss = {}
        history_z = [NUM_TO_ZODIAC[n] for n in HISTORY]
        for z in z_list:
            if z not in history_z:
                m = len(history_z) + 1
            else:
                last_pos = len(history_z) - 1 - history_z[::-1].index(z)
                m = len(history_z) - last_pos - 1
                # 连错超过3期，权重翻倍
                streak = STREAK.get(z, {}).get("连续", 0)
                if streak < 0 and abs(streak) >3:
                    m = m * 2
                # 遗漏超过10期，权重翻倍
                if m > 10:
                    m = m * 2
                # 走势调整
                trend_adjust = get_trend_adjust()
                m = m * trend_adjust
            
            # 🔥 防重肖：上一期的生肖，给它的遗漏权重打5折，让它很难被选到，但是不会完全排除
            if last_zodiac and z == last_zodiac:
                m = m * 0.5
            
            zodiac_miss[z] = m
        
        sorted_z = sorted(zodiac_miss.keys(), key=lambda x: zodiac_miss[x], reverse=True)
        return sorted_z[0], sorted_z[:3], sorted_z[:6]
    else:
        random.shuffle(z_list)
        return z_list[0], z_list[:3], z_list[:6]
# 🔥 一肖特码：选生肖里最久没开的数字，不是随机
def one_special(current_one):
    nums = ZODIAC_MAP[current_one]
    # 走势调整
    trend_adjust = get_trend_adjust()
    nums_sorted = sorted(nums, key=lambda x: ((len(HISTORY) +1 if x not in HISTORY else len(HISTORY) - HISTORY.index(x)) * trend_adjust), reverse=True)
    return nums_sorted[0]
# ==============================================
# 🔥 波色/大小/单双：用遗漏值，连错回补，走势调整
# ==============================================
def wave_analysis():
    h = list(HISTORY)
    if not h: return random.choice(["红波","蓝波","绿波"])
    r_miss = get_item_miss("红波", lambda n: n in RED_WAVE)
    b_miss = get_item_miss("蓝波", lambda n: n in BLUE_WAVE)
    g_miss = get_item_miss("绿波", lambda n: n in GREEN_WAVE)
    
    # 走势调整
    trend_adjust = get_trend_adjust()
    r_miss *= trend_adjust
    b_miss *= trend_adjust
    g_miss *= trend_adjust
    
    # 连错回补
    if STREAK["波色"]["连续"] <0 and abs(STREAK["波色"]["连续"])>3:
        miss_map = {"红波":r_miss, "蓝波":b_miss, "绿波":g_miss}
        return max(miss_map, key=miss_map.get)
    
    return max(["红波","蓝波","绿波"], key=lambda x: {"红波":r_miss,"蓝波":b_miss,"绿波":g_miss}[x])

def size_analysis():
    h = list(HISTORY)
    if not h: return random.choice(["大","小"])
    big_miss = get_item_miss("大", lambda n: n>=25)
    small_miss = get_item_miss("小", lambda n: n<25)
    
    # 走势调整
    trend_adjust = get_trend_adjust()
    big_miss *= trend_adjust
    small_miss *= trend_adjust
    
    if STREAK["大小"]["连续"] <0 and abs(STREAK["大小"]["连续"])>3:
        return "大" if big_miss > small_miss else "小"
    
    return "大" if big_miss > small_miss else "小" if big_miss < small_miss else random.choice(["大","小"])

def odd_even_analysis():
    h = list(HISTORY)
    if not h: return random.choice(["单","双"])
    odd_miss = get_item_miss("单", lambda n: n%2==1)
    even_miss = get_item_miss("双", lambda n: n%2==0)
    
    # 走势调整
    trend_adjust = get_trend_adjust()
    odd_miss *= trend_adjust
    even_miss *= trend_adjust
    
    if STREAK["单双"]["连续"] <0 and abs(STREAK["单双"]["连续"])>3:
        return "单" if odd_miss > even_miss else "双"
    
    return "单" if odd_miss > even_miss else "双" if odd_miss < even_miss else random.choice(["单","双"])
# 战绩记录
def add_battle(key, correct):
    if key not in BATTLE_RECORD:
        BATTLE_RECORD[key] = deque(maxlen=10)
    BATTLE_RECORD[key].append("✅" if correct else "❌")
    d = STREAK[key]
    d["连续"] = d["连续"]+1 if correct==d["状态"] else 1
    d["状态"] = correct
    # 自动保存
    save_data()
def get_streak(key):
    s = STREAK[key]
    return f"连{s['连续']}对" if s["状态"] else f"连{s['连续']}错"
def get_battle(key): return "".join(BATTLE_RECORD.get(key,""))
def add_history(num): 
    HISTORY.append(num)
    # 自动保存
    save_data()
def learn_from_result(num): pass