"""Сайт «Инвестиции и уровень жизни в России» на Flask.

Запуск:
    pip install -r requirements.txt
    python app.py
Потом откройте http://localhost:5000

Все тексты и цифры лежат в этом файле. Меняете значения, перезапускаете, страница обновляется.
Чтобы получить один готовый файл для хостинга без Python, выполните: python build_static.py
"""
import calendar
import datetime as dt
from zoneinfo import ZoneInfo

from flask import Flask, render_template

import live_data

app = Flask(__name__)

# ======================================================================
# 1. О команде: замените заглушки своими текстами
# ======================================================================
TEAM = {
    "name": "[Название команды]",
    "signer": "[Имя подписанта]",
    "email": "[электронная почта]",
    "phone": "[телефон]",
    "year": 2026,
    "services": [
        ("[Направление 1]", "Например, обзоры рынка и аналитика по российской экономике."),
        ("[Направление 2]", "Например, подбор инвестиционной стратегии под цели клиента."),
        ("[Направление 3]", "Например, сопровождение бизнеса при выходе на новые рынки."),
    ],
    "advantages": [
        ("[Преимущество 1]", "Например, опыт команды и число реализованных проектов."),
        ("[Преимущество 2]", "Например, прозрачные условия и отчёты на понятном языке."),
        ("[Преимущество 3]", "Например, работаем только с проверенными данными из открытых источников."),
        ("[Преимущество 4]", "Например, индивидуальный подход к каждому клиенту."),
    ],
}

# ======================================================================
# 2. Текущие показатели по России (на 21 октября 2026)
# ======================================================================
UPDATED = "21.10.2026"   # дата, когда вы последний раз вручную обновляли показатели ниже

# Даты заседаний Банка России, по которым нужен показ «ближайшего заседания».
# Когда дата пройдёт, фраза пропадёт сама. Добавляйте новые даты по календарю ЦБ.
MEETINGS = [dt.date(2026, 10, 23)]

KEY_RATE = 14.0          # ключевая ставка, % (с 24 июля 2026)
INFLATION = 6.35         # годовая инфляция, сентябрь 2026, %
AVG_WAGE = 109_524       # средняя начисленная зарплата, июль 2026, ₽
AVG_WAGE_APR = 109_052   # то же за апрель 2026, для сравнения регионов (данные региональной таблицы за апрель)

GLANCE = [
    ("Ключевая ставка", "14%"),
    ("Инфляция за год", "6,35%"),
    ("Безработица", "2,3%"),
    ("Доллар (ЦБ)", "82,85 ₽"),
    ("Индекс МосБиржи", "2 426"),
]

PEOPLE = [
    {"k": "Средняя начисленная зарплата, июль", "v": "109 524", "unit": "₽", "tone": "",
     "n": "К июлю 2025 года +9,5%. В июне было 114 743 ₽, реальные зарплаты выросли на 3,4%."},
    {"k": "Безработица, июль", "v": "2,3", "unit": "%", "tone": "",
     "n": "Минимум за всю историю наблюдений был в мае, 2,1%. Власти оценивают нехватку работников в 3,1 млн человек к 2030 году."},
    {"k": "Доля населения ниже границы бедности, II кв.", "v": "7,0", "unit": "%", "tone": "",
     "n": "Граница бедности 17 816 ₽ в месяц. Год назад доля была на 0,4 п. п. выше."},
    {"k": "Инфляция за 12 месяцев, сентябрь", "v": "6,35", "unit": "%", "tone": "",
     "n": "Минэкономразвития ждёт 6,8% по итогам 2026 года и возврата к цели в 4% к концу 2027 года."},
]

INVEST = [
    {"k": "Инвестиции в основной капитал, I полугодие", "v": "−9,9", "unit": "%", "tone": "neg",
     "n": "К прошлому году: −14,3% в первом квартале и −6,6% во втором. Минэкономразвития ждёт −5,4% за весь 2026 год."},
    {"k": "Рост ВВП в 2026 году, прогнозы", "v": "0,5–1,1", "unit": "%", "tone": "",
     "n": "Опрос экономистов Банка России даёт 0,5%, Минэкономразвития 0,6%, МВФ 1,1%."},
    {"k": "Индекс МосБиржи, 16 октября", "v": "2 426", "unit": "", "tone": "",
     "n": "На 6,4% выше, чем 1 октября (2 280 пунктов). Индекс РТС закрылся на 914."},
    {"k": "Доллар по курсу ЦБ, 20 октября", "v": "82,85", "unit": "₽", "tone": "",
     "n": "Юань 12,39 ₽, евро 93,23 ₽. В мае доллар стоил около 71 ₽."},
]

BARS = [
    {"label": "Рыночная ипотека, новостройки", "value": 21.28, "alt": True},
    {"label": "Ключевая ставка", "value": 14.00, "alt": False},
    {"label": "Вклады, максимальные ставки", "value": 13.06, "alt": False},
    {"label": "Инфляция за год", "value": 6.35, "alt": True},
]
BAR_MAX = 25
AXIS = [0, 5, 10, 15, 20, 25]

# ======================================================================
# 3. Динамика (графики)
# ======================================================================
# Ключевая ставка на конец месяца и годовая инфляция (г/г). Источники: Банк России, Росстат, СберCIB.
# Год и месяц для каждой точки графика. Добавляя месяц в MONTHS_RATE, добавляйте его и сюда,
# а также значения в KEY_SERIES (запасное) и INFL_SERIES.
RATE_YM = [(2025, 12), (2026, 1), (2026, 2), (2026, 3), (2026, 4), (2026, 5), (2026, 6), (2026, 7), (2026, 8), (2026, 9)]
MONTHS_RATE = [
    ("Дек", "декабрь 2025"), ("Янв", "январь 2026"), ("Фев", "февраль 2026"),
    ("Мар", "март 2026"), ("Апр", "апрель 2026"), ("Май", "май 2026"),
    ("Июн", "июнь 2026"), ("Июл", "июль 2026"), ("Авг", "август 2026"), ("Сен", "сентябрь 2026"),
]
KEY_SERIES = [16.0, 16.0, 15.5, 15.0, 14.5, 14.5, 14.25, 14.0, 14.0, 14.0]
INFL_SERIES = [5.59, 6.0, 5.91, 5.86, 5.58, 5.31, 6.02, 5.98, 6.33, 6.35]

# Средняя начисленная зарплата, тыс. ₽. None: значение не найдено в источниках.
MONTHS_WAGE = [
    ("Окт", "октябрь 2025"), ("Ноя", "ноябрь 2025"), ("Дек", "декабрь 2025"),
    ("Янв", "январь 2026"), ("Фев", "февраль 2026"), ("Мар", "март 2026"),
    ("Апр", "апрель 2026"), ("Май", "май 2026"), ("Июн", "июнь 2026"), ("Июл", "июль 2026"),
]
WAGE_SERIES = [99.707, 98.192, 139.727, None, None, None, 109.052, 110.216, 114.743, 109.524]

# ======================================================================
# 4. Регионы
# ======================================================================
# wage: средняя начисленная зарплата за апрель 2026, ₽
# unemp: безработица, среднее за май–июль 2026, %
# infl: годовая инфляция в сентябре 2026, %
# None: показателя нет в использованных источниках, на странице будет прочерк
REGIONS = [
    {"name": "Москва", "wage": 196_825, "unemp": 1.1, "infl": None},
    {"name": "Московская область", "wage": 130_556, "unemp": 1.9, "infl": None},
    {"name": "Санкт-Петербург", "wage": 128_509, "unemp": 1.5, "infl": 6.03},
    {"name": "Татарстан", "wage": 98_316, "unemp": 1.7, "infl": None},
    {"name": "Свердловская область", "wage": 94_807, "unemp": None, "infl": None},
    {"name": "Новосибирская область", "wage": 92_457, "unemp": None, "infl": None},
    {"name": "Краснодарский край", "wage": 85_171, "unemp": None, "infl": None},
    {"name": "Башкортостан", "wage": None, "unemp": 1.4, "infl": 5.18},
]
RUSSIA_ROW = {"name": "Россия в целом", "wage": AVG_WAGE_APR, "unemp": 2.2, "infl": 6.35}

# Для справки под таблицей
REGION_NOTES = [
    "Самые высокие зарплаты в мае 2026: Чукотка 260 700 ₽, Магаданская область 214 400 ₽, Ямало-Ненецкий округ 205 300 ₽.",
    "Инфляция по регионам различается более чем вдвое: в сентябре годовая была 13,26% в Крыму и 12,03% в Туве, а в Карелии 5,21% и в Башкортостане 5,18%.",
]

# ======================================================================
# 5. Калькуляторы
# ======================================================================
# Средние максимальные ставки по рублёвым вкладам в крупнейших банках, октябрь 2026 (Банк России).
DEPOSIT_RATES = [
    {"upto_months": 3, "rate": 12.55, "label": "до 90 дней"},
    {"upto_months": 6, "rate": 12.87, "label": "91–180 дней"},
    {"upto_months": 12, "rate": 12.73, "label": "181 день – 1 год"},
    {"upto_months": 999, "rate": 11.75, "label": "свыше 1 года"},
]

# Рыночная ипотека: средняя полная стоимость кредита (ПСК), октябрь 2026; льготная ставка до 6%.
MORTGAGE_PRESETS = [
    {"label": "Рынок, новостройки (ПСК 21,28%)", "rate": 21.28},
    {"label": "Рынок, вторичное жильё (ПСК 21,83%)", "rate": 21.83},
    {"label": "Льготная ипотека (до 6%)", "rate": 6.0},
]


def deposit_income(amount, months, rate, capitalize=False):
    """Доход по вкладу до налогов. Без капитализации проценты простые."""
    if capitalize:
        final = amount * (1 + rate / 100 / 12) ** months
    else:
        final = amount * (1 + rate / 100 * months / 12)
    return final - amount


def real_gain(amount, months, rate, inflation=INFLATION):
    """Доход по вкладу в сегодняшних рублях, с учётом инфляции."""
    final = amount + deposit_income(amount, months, rate)
    return final / (1 + inflation / 100) ** (months / 12) - amount


def annuity_payment(loan, years, rate):
    """Аннуитетный платёж в месяц."""
    n = years * 12
    i = rate / 100 / 12
    if i == 0:
        return loan / n
    return loan * i / (1 - (1 + i) ** -n)


def rub(x):
    return f"{round(x):,}".replace(",", " ") + " ₽"


# ======================================================================
# 6. Что это значит для вас
# ======================================================================
def build_scenarios(key_rate=KEY_RATE, next_meeting=None):
    dep = 1_000_000
    dep_rate = 12.73
    inc = deposit_income(dep, 12, dep_rate)
    real = real_gain(dep, 12, dep_rate)

    loan = 6_000_000 * 0.8
    pay_mkt = annuity_payment(loan, 20, 21.28)
    pay_pref = annuity_payment(loan, 20, 6.0)
    share = pay_mkt / AVG_WAGE * 100

    return [
        {
            "title": "Если у вас есть накопления",
            "lead": (f"Вклады сейчас дают до 13,06% годовых при инфляции {str(INFLATION).replace('.', ',')}%. "
                     f"Пример: {rub(dep)} на год под {str(dep_rate).replace('.', ',')}% приносят около {rub(inc)} "
                     f"до налогов, а в сегодняшних рублях около {rub(real)}."),
            "points": [
                "Ставки по вкладам зависят от решений Банка России." + (f" Ближайшее заседание: {next_meeting}." if next_meeting else ""),
                "Максимальные ставки часто действуют только на ограниченный срок или при условиях.",
                "Доход считается до налогов. Проверьте налог на проценты по вкладам для вашей суммы.",
            ],
            "link": ("#kalkulyatory", "Посчитать вклад"),
        },
        {
            "title": "Если вы берёте ипотеку",
            "lead": (f"Рыночная ипотека стоит около 21% ПСК, льготные программы до 6%. На квартиру за 6 млн ₽ "
                     f"с взносом 20% на 20 лет платёж составит около {rub(pay_mkt)} в месяц на рынке "
                     f"и около {rub(pay_pref)} по ставке 6%."),
            "points": [
                f"Рыночный платёж в этом примере равен примерно {round(share)}% средней зарплаты по России.",
                "С 1 октября 2026 года ставка и лимит семейной ипотеки зависят от числа детей.",
                "Банки снижают ипотечные ставки медленнее, чем Банк России ключевую.",
            ],
            "link": ("#kalkulyatory", "Посчитать ипотеку"),
        },
        {
            "title": "Если у вас бизнес",
            "lead": (f"Кредиты остаются дорогими: ключевая ставка {fmt_num(key_rate)}%, а средняя рентабельность бизнеса в России, "
                     "по оценкам экспертов, не выше 10–12%. Инвестиции в основной капитал за полугодие упали на 9,9%."),
            "points": [
                "Безработица 2,3% и нехватка работников: зарплаты растут быстрее цен, издержки на персонал увеличиваются.",
                "Спрос поддерживают доходы населения, а не инвестиции: реальные зарплаты в июне выросли на 3,4%.",
                "Власти ждут возобновления роста инвестиций в 2027 году, прогнозы расходятся.",
            ],
            "link": ("#dinamika", "Смотреть динамику"),
        },
        {
            "title": "Если вы работаете по найму",
            "lead": ("Номинальная зарплата в июле выросла на 9,5% за год при инфляции около 6,4%, "
                     "поэтому покупательная способность растёт. Безработица около 2,2–2,3%."),
            "points": [
                "Средняя зарплата по стране не показывает типичную: сильно влияют высокие доходы.",
                "Различия между регионами большие: в Москве зарплата почти вдвое выше средней по России.",
                "Власти прогнозируют рост реальных доходов на 3–5% в год до 2030 года.",
            ],
            "link": ("#regiony", "Сравнить регионы"),
        },
    ]


SOURCES = [
    ("Банк России: инфляция в сентябре", "https://www.cbr.ru/press/reginfl/?id=70297"),
    ("Банк России: инфляция в Санкт-Петербурге", "https://cbr.ru/press/reginfl/?id=70242"),
    ("Банк России: инфляция в Башкортостане", "https://www.cbr.ru/press/reginfl/?id=70237"),
    ("Ключевая ставка: история решений", "https://brobank.ru/klyuchevaya-stavka-cb-rf/"),
    ("Решение по ключевой ставке, 11 сентября", "https://ru.themoscowtimes.com/2026/09/11/tekst-soobschenie-tsbr-o-klyuchevoy-stavke-a205851"),
    ("Инфляция по месяцам 2026", "https://sbercib.ru/publication/inflyatsiya-v-rossii-v-2026-godu-dinamika-i-prognozi"),
    ("Реальные зарплаты, июнь", "https://ru.themoscowtimes.com/2026/09/02/rost-realnykh-zarplat-v-rf-v-iyune-26g-zamedlilsya-do-34-gg-a205127"),
    ("Средняя зарплата, июль", "https://www.amic.ru/news/srednyaya-zarplata-v-rossii-vyrosla-do-110-tysyach-rubley-593552"),
    ("Средняя зарплата, декабрь 2025", "https://expert.ru/news/srednyaya-zarplata-v-rossii-v-dekabre-povysilas-na-40-tysyach-rubley"),
    ("Зарплаты по регионам, апрель 2026", "https://finance.mail.ru/article/srednyaya-zarplata-v-rossii-432/"),
    ("Зарплаты в регионах-лидерах, май", "https://abnews.ru/news/2026/8/4/gde-v-rossii-poluchayut-bolshe-200-tysyach-rosstat-nazval-tri-regiona"),
    ("Безработица по регионам, май–июль", "https://finance.mail.ru/article/analitiki-raskryli-v-kakih-regionah-rf-pobedili-bezraboticu-69228580/"),
    ("Безработица, июль", "https://www.finmarket.ru/news/6698655"),
    ("Уровень бедности, II квартал", "https://fomag.ru/news-streem/uroven-bednosti-vo-ii-kvartale-2026-goda-v-rf-sostavil-7-0-rosstat/"),
    ("Инвестиции в основной капитал, II квартал", "https://ru.themoscowtimes.com/2026/09/02/investitsii-v-rf-vo-2-kv-26g-prodolzhili-padenie-za-polugodie-upali-pochti-na-10-a205129"),
    ("Прогноз Минэкономразвития по инвестициям", "https://kurs.com.ua/ru/novost/1481356-rosija-pogirshila-prognoz-promislovosti-ta-ochikue-padinnja-investicii"),
    ("Прогноз роста ВВП, опрос экономистов", "https://www.tks.ru/politics/2026/09/03/0008/ekonomistyi-ozhidayut-rost-vvp-rossii-vsego-na-0-5-procent-v-2026-godu/"),
    ("Московская биржа: индексы 16 октября", "https://www.moex.com/n105203?nt=108"),
    ("Курсы ЦБ на 20 октября", "https://investfuture.ru/articles/obzor-valyut-2026-10-20"),
    ("Ставки по вкладам, октябрь", "https://investfuture.ru/articles/bank-rossii-nazval-maksimalnuyu-stavku-po-rublevym-vkladam-13-06-8eb248a33aa0bca8"),
    ("Стоимость ипотеки, октябрь", "https://brobank.ru/stoimost-ipoteki-oktyabr-2026-goda/"),
]


def fmt(x: float) -> str:
    """21.28 -> '21,28' (запятая как десятичный разделитель)."""
    return f"{x:.2f}".replace(".", ",")


def fmt_num(x: float) -> str:
    """14.0 -> '14', 14.25 -> '14,25'."""
    return f"{x:g}".replace(".", ",")


def fmt_int(x: float) -> str:
    return f"{round(x):,}".replace(",", "\u00a0")


MONTHS_GEN = ["января", "февраля", "марта", "апреля", "мая", "июня",
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
MSK = ZoneInfo("Europe/Moscow")


def date_ru(d: dt.date) -> str:
    return f"{d.day} {MONTHS_GEN[d.month - 1]}"


def next_meeting(today: dt.date):
    future = [m for m in MEETINGS if m >= today]
    return date_ru(min(future)) if future else None


def region_rows():
    rows = []
    for r in REGIONS:
        row = dict(r)
        row["ratio"] = round(r["wage"] / AVG_WAGE_APR, 2) if r["wage"] else None
        rows.append(row)
    rows.sort(key=lambda r: (r["wage"] is None, -(r["wage"] or 0)))
    return rows


def moved(a: float, b: float, up: str, down: str) -> str:
    if abs(a - b) < 1e-9:
        return "не изменилась"
    return up if b > a else down


def live_view(now: dt.datetime | None = None) -> dict:
    """Собирает всё, что зависит от автоматически получаемых данных, с запасными значениями."""
    now = now or dt.datetime.now(MSK)
    live = live_data.get_live()
    status = live.get("status", {})

    key = live.get("key_rate", KEY_RATE)
    key_since = None
    if live.get("key_since"):
        key_since = date_ru(dt.date.fromisoformat(live["key_since"]))

    # помесячный ряд ставки для графика: на конец каждого месяца
    key_series = list(KEY_SERIES)
    hist = [tuple(r) for r in live.get("key_history", [])]
    if hist:
        for idx, (y, m) in enumerate(RATE_YM):
            last_day = min(dt.date(y, m, calendar.monthrange(y, m)[1]), now.date())
            v = live_data.rate_on(hist, last_day)
            if v is not None:
                key_series[idx] = v

    glance = list(GLANCE)
    invest = [dict(c) for c in INVEST]
    bars = [dict(b) for b in BARS]

    glance[0] = ("Ключевая ставка", f"{fmt_num(key)}%")
    for b in bars:
        if b["label"] == "Ключевая ставка":
            b["value"] = key

    rates = live.get("rates")
    if rates:
        glance[3] = ("Доллар (ЦБ)", f"{fmt(rates['USD'])}\u00a0₽")
        d = dt.date.fromisoformat(rates["date"])
        invest[3] = {"k": f"Доллар по курсу ЦБ на {date_ru(d)}", "v": fmt(rates["USD"]), "unit": "₽", "tone": "",
                     "n": f"Юань {fmt(rates['CNY'])} ₽, евро {fmt(rates['EUR'])} ₽."}

    imoex = live.get("imoex")
    if imoex:
        glance[4] = ("Индекс МосБиржи", fmt_int(imoex["value"]))
        chg = imoex.get("change_pct")
        parts = []
        if chg is not None:
            sign = "+" if chg > 0 else ("−" if chg < 0 else "")
            parts.append(f"К предыдущему закрытию {sign}{fmt(abs(chg))}%.")
        rtsi = live.get("rtsi")
        if rtsi:
            parts.append(f"Индекс РТС {fmt_int(rtsi['value'])}.")
        invest[2] = {"k": "Индекс МосБиржи", "v": fmt_int(imoex["value"]), "unit": "", "tone": "",
                     "n": " ".join(parts) or "Значение на момент последнего обновления."}

    # пометка об автообновлении
    sources_ok = [n for n in live_data.SOURCES if status.get(n, {}).get("ok")]
    failed = [live_data.SOURCES[n][0] for n in live_data.SOURCES if n in status and not status[n]["ok"]]
    stamp = live.get("checked_at")
    if sources_ok and stamp:
        t = dt.datetime.fromisoformat(stamp).astimezone(MSK).strftime("%d.%m.%Y %H:%M")
        live_note = f"Курсы валют, ключевая ставка и индексы биржи обновляются автоматически, последняя проверка {t} МСК."
        if failed:
            live_note += f" Не удалось обновить: {', '.join(failed).lower()}, показаны последние известные значения."
        asof = now.strftime("%d.%m.%Y")
    elif failed:
        live_note = "Автообновление курсов, ставки и индексов сейчас недоступно, показаны значения на " + UPDATED + "."
        asof = UPDATED
    else:
        live_note = "Курсы валют, ключевая ставка и индексы биржи обновляются автоматически."
        asof = UPDATED

    nm = next_meeting(now.date())
    scale_sub = (f"Ключевая ставка {fmt_num(key)}% действует с {key_since}." if key_since
                 else f"Текущая ключевая ставка {fmt_num(key)}%.") + (
        f" Следующее заседание Банка России назначено на {nm}." if nm else "")

    first_month = MONTHS_GEN[RATE_YM[0][1] - 1]
    dyn_lead = (
        f"С {first_month} ключевая ставка {moved(key_series[0], key, 'выросла', 'снизилась')} "
        f"с {fmt_num(key_series[0])}% до {fmt_num(key)}%, а инфляция за 12 месяцев "
        f"{moved(INFL_SERIES[0], INFL_SERIES[-1], 'выросла', 'снизилась')} "
        f"с {fmt_num(round(INFL_SERIES[0], 1))}% до {fmt_num(INFL_SERIES[-1])}%. "
        f"Разрыв между ними сейчас {fmt(key - INFLATION)} п. п."
    )

    return {"key": key, "key_series": key_series, "glance": glance, "invest": invest, "bars": bars,
            "live_note": live_note, "asof": asof, "scale_sub": scale_sub, "dyn_lead": dyn_lead, "next_meeting": nm}


@app.route("/")
def index():
    v = live_view()
    bars = [
        {**b, "width": round(b["value"] / BAR_MAX * 100, 1), "text": fmt(b["value"])}
        for b in v["bars"]
    ]
    # Данные для скриптов страницы (графики и калькуляторы)
    site_data = {
        "keyRate": v["key"],
        "inflation": INFLATION,
        "avgWage": AVG_WAGE,
        "rate": {
            "labels": [m[0] for m in MONTHS_RATE],
            "full": [m[1] for m in MONTHS_RATE],
            "key": v["key_series"],
            "infl": INFL_SERIES,
        },
        "wage": {
            "labels": [m[0] for m in MONTHS_WAGE],
            "full": [m[1] for m in MONTHS_WAGE],
            "values": WAGE_SERIES,
        },
        "depositRates": DEPOSIT_RATES,
    }
    return render_template(
        "index.html",
        team=TEAM, updated=UPDATED, glance=v["glance"],
        people=PEOPLE, invest=v["invest"],
        bars=bars, axis=AXIS, sources=SOURCES,
        regions=region_rows(), russia=RUSSIA_ROW, region_notes=REGION_NOTES,
        mortgage_presets=MORTGAGE_PRESETS, deposit_rates=DEPOSIT_RATES,
        scenarios=build_scenarios(v["key"], v["next_meeting"]),
        infl_now=fmt(INFLATION), real_rate=fmt(v["key"] - INFLATION),
        live_note=v["live_note"], asof=v["asof"], scale_sub=v["scale_sub"], dyn_lead=v["dyn_lead"],
        site_data=site_data,
    )


if __name__ == "__main__":
    live_data.refresh()          # при запуске сразу берём свежие данные
    # debug=True удобно при разработке; на реальном сервере его выключают
    app.run(host="0.0.0.0", port=5000, debug=True)
