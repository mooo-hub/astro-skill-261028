#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
西方占星本命盘排盘脚本
基于 Swiss Ephemeris (pyswisseph) 天文计算库，精确计算行星位置、宫位配置
支持多种分宫制: 阿卡比特制(默认), Placidus, 整宫制

用法: python astro_calc.py YYYY MM DD HH MM 经度 纬度 [时区] [分宫制]
示例:
  python astro_calc.py 1997 2 18 13 34 118.5 37.4 8           # 默认阿卡比特制
  python astro_calc.py 1997 2 18 13 34 118.5 37.4 8 placidus   # Placidus分宫制
  python astro_calc.py 1997 2 18 13 34 118.5 37.4 8 whole       # 整宫制
"""
import sys
import math
import json
import io

# Windows 控制台 UTF-8 编码修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import swisseph as swe
except ImportError:
    print("ERROR: pyswisseph库未安装，请运行: pip install pyswisseph")
    sys.exit(1)

# ===== 常量定义 =====
SIGNS_CN = ['白羊座','金牛座','双子座','巨蟹座','狮子座','处女座',
            '天秤座','天蝎座','射手座','摩羯座','水瓶座','双鱼座']
SIGNS_EN = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
            'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGNS_ELEMENT = ['火','土','风','水','火','土','风','水','火','土','风','水']
SIGNS_NATURE = ['基本','固定','变动','基本','固定','变动','基本','固定','变动','基本','固定','变动']

# 现代守护关系（仅参考）
SIGNS_RULER_MODERN = ['火星','金星','水星','月亮','太阳','水星','金星','冥王星','木星','土星','天王星','海王星']

# ★ 古典守护关系（古典占星必须使用）★
# 水瓶座→土星（非天王星），双鱼座→木星（非海王星），天蝎座→火星（非冥王星）
SIGNS_RULER_CLASSICAL = ['火星','金星','水星','月亮','太阳','水星','金星','火星','木星','土星','土星','木星']

PLANETS_CN = {
    'Sun': '太阳', 'Moon': '月亮', 'Mercury': '水星', 'Venus': '金星',
    'Mars': '火星', 'Jupiter': '木星', 'Saturn': '土星',
    'Uranus': '天王星', 'Neptune': '海王星', 'Pluto': '冥王星'
}

# Swiss Ephemeris 行星ID
PLANET_IDS = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mercury': swe.MERCURY,
    'Venus': swe.VENUS,
    'Mars': swe.MARS,
    'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN,
    'Uranus': swe.URANUS,
    'Neptune': swe.NEPTUNE,
    'Pluto': swe.PLUTO
}

# 行星庙旺落陷表
DIGNITIES = {
    'Sun':    {'入庙': ['狮子座'], '入旺': ['白羊座'], '失势': ['水瓶座'], '落陷': ['天秤座']},
    'Moon':   {'入庙': ['巨蟹座'], '入旺': ['金牛座'], '失势': ['摩羯座'], '落陷': ['天蝎座']},
    'Mercury':{'入庙': ['双子座','处女座'], '入旺': ['水瓶座'], '失势': ['射手座','双鱼座'], '落陷': ['狮子座']},
    'Venus':  {'入庙': ['金牛座','天秤座'], '入旺': ['双鱼座'], '失势': ['天蝎座','白羊座'], '落陷': ['处女座']},
    'Mars':   {'入庙': ['白羊座','天蝎座'], '入旺': ['摩羯座'], '失势': ['天秤座','金牛座'], '落陷': ['巨蟹座']},
    'Jupiter':{'入庙': ['射手座','双鱼座'], '入旺': ['巨蟹座'], '失势': ['双子座','处女座'], '落陷': ['摩羯座']},
    'Saturn': {'入庙': ['摩羯座','水瓶座'], '入旺': ['天秤座'], '失势': ['巨蟹座','狮子座'], '落陷': ['白羊座']},
    'Uranus': {'入庙': ['水瓶座'], '入旺': ['天蝎座'], '失势': ['狮子座'], '落陷': ['金牛座']},
    'Neptune':{'入庙': ['双鱼座'], '失势': ['处女座']},
    'Pluto':  {'入庙': ['天蝎座'], '失势': ['金牛座']},
}

# ★ 行星力量评分表（古典占星标准）★
DIGNITY_SCORES = {
    '入庙': 5,     # 行星回到自己守护的星座
    '入旺': 4,     # 行星在旺宫星座
    '三分性': 3,   # 行星在日生/夜生的三分主星座（需要额外判断）
    '界': 2,       # 行星在所主管的界区间（需要精确度数判断）
    '面': 1,       # 行星在所主管的十度区间
    '入闲(中性)': 0, # 无必然尊贵
    '失势': -5,    # 行星在自己主管星座的正对面
    '落陷': -4,    # 行星在旺宫星座的正对面
}

# 日生盘/夜生盘三分性守护星表
TRIPLICITY_RULERS = {
    '火': {'日': ['太阳', '木星', '土星'], '夜': ['木星', '太阳', '土星']},
    '土': {'日': ['金星', '月亮', '火星'], '夜': ['月亮', '金星', '火星']},
    '风': {'日': ['土星', '水星', '木星'], '夜': ['水星', '土星', '木星']},
    '水': {'日': ['金星', '月亮', '火星'], '夜': ['月亮', '金星', '火星']},
}

# 分宫制代码映射
HOUSE_SYSTEMS = {
    'alcabitius': {'code': b'B', 'name': '阿卡比特制', 'name_en': 'Alcabitius'},
    'placidus': {'code': b'P', 'name': 'Placidus', 'name_en': 'Placidus'},
    'koch': {'code': b'K', 'name': 'Koch', 'name_en': 'Koch'},
    'regiomontanus': {'code': b'R', 'name': '雷吉奥蒙塔努斯制', 'name_en': 'Regiomontanus'},
    'campanus': {'code': b'C', 'name': '坎帕努斯制', 'name_en': 'Campanus'},
    'equal': {'code': b'A', 'name': '等宫制', 'name_en': 'Equal'},
    'whole': {'code': None, 'name': '整宫制', 'name_en': 'Whole Sign'},  # 需要特殊处理
}


def get_sign(ecl_lon_deg):
    """根据黄经度数获取星座名称和星座内度数"""
    sign_idx = int(ecl_lon_deg / 30) % 12
    sign_deg = ecl_lon_deg % 30
    return sign_idx, sign_deg


def get_dignity(planet_name, sign_name):
    """判断行星在星座中的庙旺落陷状态"""
    dignities = DIGNITIES.get(planet_name, {})
    for status, signs in dignities.items():
        if sign_name in signs:
            return status
    return '入闲(中性)'


def compute_whole_sign_houses(asc_lon):
    """计算整宫制宫位(每宫30度, 从上升星座开始)"""
    asc_sign_idx = int(asc_lon / 30) % 12
    houses = {}
    for i in range(12):
        # 1宫从上升星座开始
        sign_idx = (asc_sign_idx + i) % 12
        cusp_lon = sign_idx * 30  # 宫头在该星座0度
        houses[i + 1] = {
            'cusp_lon': round(cusp_lon, 2),
            'sign_cn': SIGNS_CN[sign_idx],
            'sign_en': SIGNS_EN[sign_idx],
            'cusp_deg': 0.0,
        }
    return houses


def compute_natal_chart(year, month, day, hour, minute, longitude, latitude, timezone=8, house_system='alcabitius', classical_only=True, use_planet_orbs=True):
    """
    计算本命盘所有数据
    使用Swiss Ephemeris和指定分宫制

    参数:
        house_system: 分宫制类型
            - 'alcabitius' (默认): 阿卡比特制, 古典占星推荐
            - 'placidus': Placidus分宫制, 现代占星默认
            - 'whole': 整宫制, 古典占星辅助
            - 'koch': Koch分宫制
            - 'equal': 等宫制
        classical_only: 是否只计算七大古典行星之间的相位 (默认True, 古典占星推荐)
        use_planet_orbs: 是否使用行星容许度 (默认True, 古典占星推荐; False为固定容许度)

    返回包含行星位置, 宫位配置, 相位等的字典
    """
    # 计算Julian Day (UTC时间)
    # UTC = 本地时间 - 时区
    hour_decimal = hour + minute / 60.0
    hour_utc_decimal = hour_decimal - timezone

    # 处理跨日情况
    day_adj = day
    month_adj = month
    year_adj = year

    if hour_utc_decimal < 0:
        hour_utc_decimal += 24
        day_adj -= 1
        if day_adj < 1:
            month_adj -= 1
            if month_adj < 1:
                month_adj = 12
                year_adj -= 1
            # 获取上月天数
            import calendar
            if month_adj == 12:
                day_adj = 31
            else:
                day_adj = calendar.monthrange(year_adj, month_adj)[1]
    elif hour_utc_decimal >= 24:
        hour_utc_decimal -= 24
        day_adj += 1
        import calendar
        days_in_month = calendar.monthrange(year_adj, month_adj)[1]
        if day_adj > days_in_month:
            day_adj = 1
            month_adj += 1
            if month_adj > 12:
                month_adj = 1
                year_adj += 1

    # swe.julday需要整数参数
    jd = swe.julday(int(year_adj), int(month_adj), int(day_adj), hour_utc_decimal)

    # 获取分宫制信息
    hs_info = HOUSE_SYSTEMS.get(house_system, HOUSE_SYSTEMS['alcabitius'])

    # 计算分宫制
    if house_system == 'whole':
        # 整宫制需要特殊处理：先计算上升，再按整宫划分
        # 使用Placidus计算上升点
        houses_result = swe.houses(jd, latitude, longitude, b'P')
        asc_lon = houses_result[1][0]
        mc_lon = houses_result[0][9]  # MC从Placidus获取

        # 计算整宫制宫位
        houses = compute_whole_sign_houses(asc_lon)
        houses_cusps = [houses[i+1]['cusp_lon'] for i in range(12)]
    else:
        # 使用指定分宫制
        houses_result = swe.houses(jd, latitude, longitude, hs_info['code'])
        houses_cusps = houses_result[0]  # 12宫位宫头
        asc_lon = houses_result[1][0]  # ASC黄经
        mc_lon = houses_cusps[9]  # MC从10宫宫头获取

        # 构建宫位字典（增加宫主星信息）
        houses = {}
        for i in range(12):
            cusp = houses_cusps[i]
            sign_idx, sign_deg = get_sign(cusp)
            houses[i + 1] = {
                'cusp_lon': round(cusp, 2),
                'sign_cn': SIGNS_CN[sign_idx],
                'sign_en': SIGNS_EN[sign_idx],
                'cusp_deg': round(sign_deg, 2),
                'ruler_classical': SIGNS_RULER_CLASSICAL[sign_idx],  # ★ 古典守护星
                'ruler_modern': SIGNS_RULER_MODERN[sign_idx],        # 现代守护星（参考）
                'planets_in_house': [],  # ★ 宫内行星列表（稍后填充）
            }

    # 四轴
    dsc_lon = (asc_lon + 180) % 360
    ic_lon = (mc_lon + 180) % 360

    # 计算行星位置
    planets = {}
    for name, planet_id in PLANET_IDS.items():
        result = swe.calc_ut(jd, planet_id)
        lon_deg = result[0][0]  # 黄经
        lat_deg = result[0][1]  # 黄纬
        speed = result[0][3]    # 每日速度（负数为逆行）

        sign_idx, sign_deg = get_sign(lon_deg)
        sign_name = SIGNS_CN[sign_idx]
        dignity = get_dignity(name, sign_name)
        retrograde = speed < 0

        # ★ 计算行星力量评分
        base_score = DIGNITY_SCORES.get(dignity, 0)
        # 逆行减2分
        if retrograde:
            base_score -= 2

        planets[name] = {
            'name_cn': PLANETS_CN[name],
            'sign_cn': sign_name,
            'sign_en': SIGNS_EN[sign_idx],
            'sign_deg': round(sign_deg, 2),
            'ecl_lon': round(lon_deg, 2),
            'ecl_lat': round(lat_deg, 2),
            'element': SIGNS_ELEMENT[sign_idx],
            'nature': SIGNS_NATURE[sign_idx],
            'dignity': dignity,
            'retrograde': retrograde,
            'speed': round(speed, 4),  # 每日黄经速度（负数为逆行）
            'score': base_score,  # ★ 行星力量评分
        }

    # 分配行星到宫位，同时填充宫内行星列表
    for pname, pdata in planets.items():
        house_num = assign_house(pdata['ecl_lon'], houses, house_system)
        pdata['house'] = house_num
        # ★ 填充宫内行星列表
        if house_num in houses:
            houses[house_num]['planets_in_house'].append(pdata['name_cn'])

    # 计算主要相位
    aspects = compute_aspects(planets, classical_only=classical_only, use_planet_orbs=use_planet_orbs)

    # 元素统计
    element_count = {'火': 0, '土': 0, '风': 0, '水': 0}
    nature_count = {'基本': 0, '固定': 0, '变动': 0}
    for pname in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']:
        p = planets[pname]
        element_count[p['element']] += 1
        nature_count[p['nature']] += 1

    # 四轴星座信息
    asc_sign_idx, asc_sign_deg = get_sign(asc_lon)
    mc_sign_idx, mc_sign_deg = get_sign(mc_lon)
    dsc_sign_idx, dsc_sign_deg = get_sign(dsc_lon)
    ic_sign_idx, ic_sign_deg = get_sign(ic_lon)

    result = {
        'birth_info': {
            'date': f'{year}年{month}月{day}日 {hour}:{minute:02d}',
            'location': f'东经{longitude}° 北纬{latitude}°',
            'timezone': f'UTC+{timezone}',
            'julian_day': round(jd, 6),
            'house_system': hs_info['name'],
            'house_system_en': hs_info['name_en'],
            'mode': '古典占星' if classical_only else '现代占星',
            'classical_only': classical_only,
            'use_planet_orbs': use_planet_orbs,
        },
        'angles': {
            'ASC': {
                'sign_cn': SIGNS_CN[asc_sign_idx],
                'sign_en': SIGNS_EN[asc_sign_idx],
                'deg': round(asc_sign_deg, 2),
                'ecl_lon': round(asc_lon, 2),
                'element': SIGNS_ELEMENT[asc_sign_idx],
            },
            'MC': {
                'sign_cn': SIGNS_CN[mc_sign_idx],
                'sign_en': SIGNS_EN[mc_sign_idx],
                'deg': round(mc_sign_deg, 2),
                'ecl_lon': round(mc_lon, 2),
                'element': SIGNS_ELEMENT[mc_sign_idx],
            },
            'DSC': {
                'sign_cn': SIGNS_CN[dsc_sign_idx],
                'deg': round(dsc_sign_deg, 2),
            },
            'IC': {
                'sign_cn': SIGNS_CN[ic_sign_idx],
                'deg': round(ic_sign_deg, 2),
            },
        },
        'planets': planets,
        'houses': houses,
        'aspects': aspects,
        'element_distribution': element_count,
        'nature_distribution': nature_count,
    }

    return result


def assign_house(ecl_lon, houses, house_system='alcabitius'):
    """将行星分配到宫位"""
    if house_system == 'whole':
        # 整宫制：直接按星座划分
        sign_idx = int(ecl_lon / 30) % 12
        asc_sign_idx = int(houses[1]['cusp_lon'] / 30) % 12
        house_num = (sign_idx - asc_sign_idx) % 12 + 1
        return house_num
    else:
        # 其他分宫制：按宫头划分
        for i in range(1, 13):
            next_i = i + 1 if i < 12 else 1
            cusp = houses[i]['cusp_lon']
            cusp_next = houses[next_i]['cusp_lon']

            if cusp < cusp_next:
                if cusp <= ecl_lon < cusp_next:
                    return i
            else:  # 跨0度
                if ecl_lon >= cusp or ecl_lon < cusp_next:
                    return i
        return 1  # 默认


def compute_aspects(planets, classical_only=True, use_planet_orbs=True):
    """
    计算主要相位(合相, 六分, 四分, 三分, 对分)

    参数:
        classical_only: 是否只计算七大古典行星之间的相位(默认True, 古典占星推荐)
        use_planet_orbs: 是否使用行星容许度(默认True, 古典占星推荐; False为固定容许度)

    古典占星相位判断标准:
    1. 使用行星容许度(Orb by planet), 而非固定容许度
    2. 两行星相位容许度 = (行星1容许度 + 行星2容许度) / 2
    3. 入相位/出相位判断基于行星相对速度

    现代占星相位判断标准:
    1. 使用固定容许度(不同相位类型不同容许度)
    2. 包含三王星的相位计算
    """
    # 相位类型定义（现代占星固定容许度）
    ASPECT_TYPES = [
        (0, '合相', 10),      # 合相容许度10°
        (60, '六分相', 6),    # 六分相容许度6°
        (90, '四分相', 8),    # 四分相容许度8°
        (120, '三分相', 8),   # 三分相容许度8°
        (180, '对分相', 10),  # 对分相容许度10°
    ]

    # 古典占星行星容许度（William Lilly标准）
    PLANET_ORBS = {
        'Sun': 15,
        'Moon': 12,
        'Mercury': 7,
        'Venus': 7,
        'Mars': 8,
        'Jupiter': 12,
        'Saturn': 9,
        'Uranus': 5,   # 现代行星，古典占星不使用
        'Neptune': 5,
        'Pluto': 5,
    }

    # 行星速度顺序（用于入相位/出相位判断）
    # 数值越大速度越快
    PLANET_SPEED_RANK = {
        'Moon': 13,      # 月亮最快，约13°/天
        'Mercury': 2,
        'Venus': 1.6,
        'Sun': 1,        # 太阳约1°/天（实际是地球绕太阳）
        'Mars': 0.52,
        'Jupiter': 0.08,
        'Saturn': 0.03,
        'Uranus': 0.01,
        'Neptune': 0.006,
        'Pluto': 0.004,
    }

    aspects = []

    # 确定参与相位计算的行星列表
    if classical_only:
        # 古典占星：只用七大行星
        classical_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']
        planet_names = [p for p in classical_planets if p in planets]
    else:
        planet_names = list(planets.keys())

    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            p1 = planet_names[i]
            p2 = planet_names[j]

            lon1 = planets[p1]['ecl_lon']
            lon2 = planets[p2]['ecl_lon']

            # 计算角度差（短弧）
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff

            # 计算该对行星的相位容许度
            if use_planet_orbs:
                # 古典占星：行星容许度
                orb1 = PLANET_ORBS.get(p1, 5)
                orb2 = PLANET_ORBS.get(p2, 5)
                combined_orb = (orb1 + orb2) / 2
            # 现代占星：固定容许度在相位类型中定义

            for angle, name, fixed_orb in ASPECT_TYPES:
                actual_orb = abs(diff - angle)
                # 判断是否在容许度范围内
                if use_planet_orbs:
                    in_orb = actual_orb <= combined_orb
                else:
                    in_orb = actual_orb <= fixed_orb

                if in_orb:
                    # 判断入相位/出相位
                    # 使用实际速度判断（考虑逆行）
                    # 原理：计算角度差的变化趋势
                    actual_speed1 = planets[p1].get('speed', 0)
                    actual_speed2 = planets[p2].get('speed', 0)

                    # 计算相对速度（p2相对于p1）
                    # 如果relative_speed > 0，表示p2正在"追赶"p1（正向）
                    relative_speed = actual_speed2 - actual_speed1

                    # 计算从p1到p2的正向距离（考虑黄道方向）
                    forward_dist = (lon2 - lon1) % 360
                    if forward_dist > 180:
                        forward_dist = forward_dist - 360  # 转为-180到180范围

                    # 计算目标相位距离（在正向方向上）
                    # 对于合相(0°)，目标是0或360
                    # 对于六分(60°)，目标是60或-300
                    # 对于四分(90°)，目标是90或-270
                    # 对于三分(120°)，目标是120或-240
                    # 对于对分(180°)，目标是180或-180

                    # 判断入相位：relative_speed与forward_dist方向一致，且正在接近目标
                    # 即：相对速度方向正向距离方向相同，且正向距离正在接近相位角度

                    # 简化方法：模拟下一步的偏离度变化
                    # 当前偏离度 = actual_orb = |diff - angle|
                    # 下一步偏离度 = |next_diff - angle|
                    # 入相位：偏离度变小（更接近精确相位）
                    # 出相位：偏离度变大（远离精确相位）
                    # 注意：不能直接比较diff，因为对于180°相位，diff变小反而意味着远离精确点

                    next_lon1 = lon1 + actual_speed1 * 0.1  # 模拟0.1天后的位置
                    next_lon2 = lon2 + actual_speed2 * 0.1
                    next_diff = abs(next_lon1 - next_lon2)
                    if next_diff > 180:
                        next_diff = 360 - next_diff

                    next_orb = abs(next_diff - angle)
                    applying = next_orb < actual_orb

                    aspects.append({
                        'planet1': PLANETS_CN[p1],
                        'planet2': PLANETS_CN[p2],
                        'aspect': name,
                        'angle': angle,
                        'orb': round(actual_orb, 2),
                        'applying': applying,
                        'harmonious': angle in [0, 60, 120],
                        'combined_orb': round(combined_orb, 1) if use_planet_orbs else fixed_orb,  # 记录使用的容许度
                    })
                    break  # 一个相位类型匹配后就跳出

    return aspects


def format_report(result):
    """格式化输出报告"""
    lines = []
    lines.append(f"# 西方占星本命盘排盘结果")
    lines.append('')
    lines.append(f"**出生信息**：{result['birth_info']['date']}")
    lines.append(f"**出生地点**：{result['birth_info']['location']}")
    lines.append(f"**时区**：{result['birth_info']['timezone']}")
    lines.append(f"**分宫制**：{result['birth_info']['house_system']}（{result['birth_info']['house_system_en']}）")
    lines.append('')

    # 四轴
    lines.append('## 四轴配置')
    lines.append('')
    lines.append('| 轴点 | 星座 | 度数 | 元素 |')
    lines.append('|------|------|------|------|')
    asc = result['angles']['ASC']
    mc = result['angles']['MC']
    lines.append(f"| **上升(ASC)** | {asc['sign_cn']} | {asc['deg']:.2f}° | {asc['element']} |")
    lines.append(f"| **中天(MC)** | {mc['sign_cn']} | {mc['deg']:.2f}° | {mc['element']} |")
    lines.append(f"| **下降(DSC)** | {result['angles']['DSC']['sign_cn']} | {result['angles']['DSC']['deg']:.2f}° | — |")
    lines.append(f"| **天底(IC)** | {result['angles']['IC']['sign_cn']} | {result['angles']['IC']['deg']:.2f}° | — |")
    lines.append('')

    # 行星配置（★增加评分列★）
    lines.append('## 行星配置')
    lines.append('')
    lines.append('| 行星 | 星座 | 度数 | 宫位 | 庙旺落陷 | 逆行 | 评分 |')
    lines.append('|------|------|------|------|----------|------|------|')
    for pname in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
                   'Uranus', 'Neptune', 'Pluto']:
        p = result['planets'][pname]
        retro = 'R' if p['retrograde'] else ''
        score = p.get('score', 0)
        lines.append(f"| **{p['name_cn']}** | {p['sign_cn']} | {p['sign_deg']:.2f}° | {p['house']}宫 | {p['dignity']} | {retro} | {score} |")
    lines.append('')

    # ★ 新增：七大古典行星力量评分汇总 ★
    lines.append('## 七大古典行星力量评分（★数据核对表★）')
    lines.append('')
    lines.append('| 行星 | 庙旺落陷 | 逆行 | 基础分 | 逆行调整 | **总分** |')
    lines.append('|------|----------|------|--------|----------|----------|')
    for pname in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']:
        p = result['planets'][pname]
        base = DIGNITY_SCORES.get(p['dignity'], 0)
        retro_adj = -2 if p['retrograde'] else 0
        lines.append(f"| {p['name_cn']} | {p['dignity']} | {'是' if p['retrograde'] else '否'} | {base} | {retro_adj} | **{p.get('score', 0)}** |")
    lines.append('')

    # 十二宫位（★增加古典宫主星和宫内行星★）
    lines.append(f"## 十二宫位配置（{result['birth_info']['house_system']}）")
    lines.append('')
    lines.append('| 宫位 | 宫头星座 | 宫头度数 | 古典宫主星 | 宫内行星 |')
    lines.append('|------|----------|----------|------------|----------|')
    for i in range(1, 13):
        h = result['houses'][i]
        label = f"**{i}宫**"
        if i == 1: label = "**1宫（自我）**"
        elif i == 2: label = "**2宫（财务）**"
        elif i == 4: label = "**4宫（家庭）**"
        elif i == 6: label = "**6宫（健康）**"
        elif i == 7: label = "**7宫（婚姻）**"
        elif i == 10: label = "**10宫（事业）**"
        ruler = h.get('ruler_classical', '-')
        planets_in = ', '.join(h.get('planets_in_house', [])) or '无'
        lines.append(f"| {label} | {h['sign_cn']} | {h['cusp_deg']:.2f}° | {ruler} | {planets_in} |")
    lines.append('')

    # 元素分布
    lines.append('## 元素与性质分布')
    lines.append('')
    lines.append('| 元素 | 行星数 | 判断 |')
    lines.append('|------|--------|------|')
    for elem in ['火', '土', '风', '水']:
        count = result['element_distribution'][elem]
        max_e = max(result['element_distribution'].values())
        marker = ' ★ 强' if count == max_e and count >= 3 else ''
        lines.append(f"| **{elem}象** | {count} |{marker}|")
    lines.append('')
    lines.append('| 性质 | 行星数 | 判断 |')
    lines.append('|------|--------|------|')
    for nat in ['基本', '固定', '变动']:
        count = result['nature_distribution'][nat]
        max_n = max(result['nature_distribution'].values())
        marker = ' ★ 强' if count == max_n and count >= 3 else ''
        lines.append(f"| **{nat}宫** | {count} |{marker}|")
    lines.append('')

    # 主要相位
    lines.append('## 主要相位')
    lines.append('')
    lines.append('| 行星1 | 行星2 | 相位 | 容许度 | 性质 |')
    lines.append('|-------|-------|------|--------|------|')
    for a in result['aspects']:
        harm = '和谐' if a['harmonious'] else '紧张'
        lines.append(f"| {a['planet1']} | {a['planet2']} | {a['aspect']} | {a['orb']}° | {harm} |")
    lines.append('')

    # JSON数据
    lines.append('## 原始数据（JSON）')
    lines.append('')
    lines.append('```json')
    json_data = {
        'birth_info': result['birth_info'],
        'angles': result['angles'],
        'planets': {k: {kk: vv for kk, vv in v.items() if kk != 'house'} for k, v in result['planets'].items()},
        'houses': result['houses'],
    }
    lines.append(json.dumps(json_data, ensure_ascii=False, indent=2))
    lines.append('```')

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 7:
        print("用法: python astro_calc.py 年 月 日 时 分 经度 纬度 [时区] [分宫制] [模式]")
        print("")
        print("示例:")
        print("  python astro_calc.py 1997 2 18 13 34 118.5 37.4 8                      # 古典占星（默认）")
        print("  python astro_calc.py 1997 2 18 13 34 118.5 37.4 8 alcabitius             # 古典占星（明确指定）")
        print("  python astro_calc.py 1997 2 18 13 34 118.5 37.4 8 placidus modern        # 现代占星")
        print("  python astro_calc.py 1997 2 18 13 34 118.5 37.4 8 whole                  # 整宫制+古典占星")
        print("")
        print("支持的分宫制:")
        print("  alcabitius  - 阿卡比特制（默认，古典占星推荐）")
        print("  placidus    - Placidus（现代占星默认）")
        print("  whole       - 整宫制（古典占星辅助）")
        print("  koch        - Koch分宫制")
        print("  equal       - 等宫制")
        print("")
        print("模式:")
        print("  classical   - 古典占星（默认）：七大行星+行星容许度+阿卡比特制")
        print("  modern      - 现代占星：十大行星+固定容许度+Placidus")
        print("")
        print("精度: Swiss Ephemeris")
        sys.exit(1)

    year = int(sys.argv[1])
    month = int(sys.argv[2])
    day = int(sys.argv[3])
    hour = int(sys.argv[4])
    minute = int(sys.argv[5])
    longitude = float(sys.argv[6])
    latitude = float(sys.argv[7])
    timezone = int(sys.argv[8]) if len(sys.argv) > 8 else 8
    house_system = sys.argv[9].lower() if len(sys.argv) > 9 else 'alcabitius'
    mode = sys.argv[10].lower() if len(sys.argv) > 10 else 'classical'

    # 根据模式设置参数
    if mode == 'modern':
        classical_only = False
        use_planet_orbs = False
        if house_system == 'alcabitius':
            house_system = 'placidus'  # 现代占星默认Placidus
    else:
        classical_only = True
        use_planet_orbs = True

    # 验证分宫制参数
    if house_system not in HOUSE_SYSTEMS:
        print(f"警告: 未知的分宫制 '{house_system}'，使用默认阿卡比特制")
        house_system = 'alcabitius'

    result = compute_natal_chart(year, month, day, hour, minute, longitude, latitude, timezone, house_system, classical_only, use_planet_orbs)
    report = format_report(result)
    print(report)


if __name__ == '__main__':
    main()
