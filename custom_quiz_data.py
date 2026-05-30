"""
Custom geographic quiz questions (Uzbek school/university level).
Format: question text in UZ/RU/EN, options list, correct option index (0-based).
"""

# Each question: {uz, ru, en (optional), options: {uz: [...], ru: [...], en: [...]}, correct: int, explanation: {uz, en}}
CUSTOM_QUESTIONS = [
    # ── O'ZBEKISTON GEOGRAFIYASI ──────────────────────────────────────────
    {
        'uz': "O'zbekistonning eng katta ko'li qaysi?",
        'options': {'uz': ["Orol dengizi", "Arnasoy", "Tudakul", "Tuzkon"], 'ru': ["Аральское море", "Арнасай", "Тудакул", "Туzkон"], 'en': ["Aral Sea", "Arnasay", "Tudakul", "Tuzkon"]},
        'correct': 0,
        'explanation': {'uz': "Orol dengizi — O'zbekistondagi eng katta suv havzasi."}
    },
    {
        'uz': "O'zbekistonning eng baland tog' cho'qqisi qaysi?",
        'options': {'uz': ["Hazrati Sulton", "Beshtor", "Adelunga", "Qo'ytosh"], 'ru': ["Хазрати Султон", "Беш Тор", "Аделунга", "Куйташ"], 'en': ["Hazrati Sulton", "Beshtor", "Adelunga", "Koytosh"]},
        'correct': 0,
        'explanation': {'uz': "Hazrati Sulton cho'qqisi 4643 m balandlikda joylashgan."}
    },
    {
        'uz': "Quyidagi daryolardan qaysi biri O'zbekiston hududida oqmaydi?",
        'options': {'uz': ["Volga", "Amudaryo", "Sirdaryo", "Zarafshon"], 'ru': ["Волга", "Амударья", "Сырдарья", "Зарафшан"], 'en': ["Volga", "Amudarya", "Syrdarya", "Zarafshan"]},
        'correct': 0,
        'explanation': {'uz': "Volga daryosi Rossiya hududida oqadi."}
    },
    {
        'uz': "O'zbekiston qaysi qit'ada joylashgan?",
        'options': {'uz': ["Osiyo", "Yevropa", "Afrika", "Avstraliya"], 'ru': ["Азия", "Европа", "Африка", "Австралия"], 'en': ["Asia", "Europe", "Africa", "Australia"]},
        'correct': 0,
        'explanation': {'uz': "O'zbekiston Markaziy Osiyo mintaqasida joylashgan."}
    },
    {
        'uz': "O'zbekiston nechta qo'shni davlat bilan chegaradosh?",
        'options': {'uz': ["5", "4", "6", "3"], 'ru': ["5", "4", "6", "3"], 'en': ["5", "4", "6", "3"]},
        'correct': 0,
        'explanation': {'uz': "Qozog'iston, Qirg'iziston, Tojikiston, Afg'oniston va Turkmaniston — jami 5 ta."}
    },
    {
        'uz': "Qoraqum va Qizilqum cho'llari qaysi mamlakatlarda joylashgan?",
        'options': {'uz': ["Turkmaniston va O'zbekiston", "Qozog'iston va O'zbekiston", "Afg'oniston va Tojikiston", "Eron va Iroq"], 'ru': ["Туркменистан и Узбекистан", "Казахстан и Узбекистан", "Афганистан и Таджикистан", "Иран и Ирак"], 'en': ["Turkmenistan & Uzbekistan", "Kazakhstan & Uzbekistan", "Afghanistan & Tajikistan", "Iran & Iraq"]},
        'correct': 0,
        'explanation': {'uz': "Qoraqum — Turkmanistonda, Qizilqum — O'zbekiston va Qozog'istonda."}
    },
    {
        'uz': "Farg'ona vodiysini qaysi tog' tizimlari o'rab turadi?",
        'options': {'uz': ["Tyanshan va Pomir", "Oltoy va Ural", "Kavkaz va Alp", "Karpat va Balkan"], 'ru': ["Тянь-Шань и Памир", "Алтай и Урал", "Кавказ и Альпы", "Карпаты и Балканы"], 'en': ["Tian Shan & Pamir", "Altai & Ural", "Caucasus & Alps", "Carpathians & Balkans"]},
        'correct': 0,
        'explanation': {'uz': "Farg'ona vodiysi Tyanshan va Pomir tog' tizmalari orasida joylashgan."}
    },
    {
        'uz': "O'zbekistonda nechtadan ortiq aholi yashaydi (taxminan)?",
        'options': {'uz': ["36 million", "20 million", "50 million", "15 million"], 'ru': ["36 млн", "20 млн", "50 млн", "15 млн"], 'en': ["36 million", "20 million", "50 million", "15 million"]},
        'correct': 0,
        'explanation': {'uz': "2024-yil holatiga ko'ra O'zbekiston aholisi 36 milliondan oshgan."}
    },

    # ── ATMOSFERA ─────────────────────────────────────────────────────────
    {
        'uz': "Atmosferaning qaysi qatlamida ob-havo hodisalari sodir bo'ladi?",
        'options': {'uz': ["Troposfera", "Stratosfera", "Mezosfera", "Termosfera"], 'ru': ["Тропосфера", "Стратосфера", "Мезосфера", "Термосфера"], 'en': ["Troposphere", "Stratosphere", "Mesosphere", "Thermosphere"]},
        'correct': 0,
        'explanation': {'uz': "Barcha meteorologik hodisalar troposferada — Yer yuzasidan 8-18 km balandlikda sodir bo'ladi."}
    },
    {
        'uz': "Ozon qavati atmosferaning qaysi qatlamida joylashgan?",
        'options': {'uz': ["Stratosfera", "Troposfera", "Mezosfera", "Ekzosfera"], 'ru': ["Стратосфера", "Тропосфера", "Мезосфера", "Экзосфера"], 'en': ["Stratosphere", "Troposphere", "Mesosphere", "Exosphere"]},
        'correct': 0,
        'explanation': {'uz': "Ozon qavati stratosferada, 15-35 km balandlikda joylashgan va Quyosh ultrabinafsha nurlardan himoya qiladi."}
    },
    {
        'uz': "Havo harorati har 100 metrga ko'tarilganda o'rtacha necha gradusga pasayadi?",
        'options': {'uz': ["0.6°C", "1.2°C", "0.3°C", "2.0°C"], 'ru': ["0.6°C", "1.2°C", "0.3°C", "2.0°C"], 'en': ["0.6°C", "1.2°C", "0.3°C", "2.0°C"]},
        'correct': 0,
        'explanation': {'uz': "Troposferada har 100 metrda harorat o'rtacha 0.6°C ga pasayadi — bu adiabatik gradient deyiladi."}
    },
    {
        'uz': "Quruq havo tarkibida azot qancha foizni tashkil etadi?",
        'options': {'uz': ["78%", "21%", "1%", "50%"], 'ru': ["78%", "21%", "1%", "50%"], 'en': ["78%", "21%", "1%", "50%"]},
        'correct': 0,
        'explanation': {'uz': "Atmosfera havo tarkibi: azot (~78%), kislorod (~21%), boshqa gazlar (~1%)."}
    },

    # ── GIDROSFERA ────────────────────────────────────────────────────────
    {
        'uz': "Dunyo okeanining umumiy suv hajmi Yer yuzasining qancha foizini qoplaydi?",
        'options': {'uz': ["71%", "50%", "80%", "60%"], 'ru': ["71%", "50%", "80%", "60%"], 'en': ["71%", "50%", "80%", "60%"]},
        'correct': 0,
        'explanation': {'uz': "Dunyo okeani Yer yuzasining taxminan 71% ni egallaydi."}
    },
    {
        'uz': "Dunyodagi eng chuqur okean trogi qaysi?",
        'options': {'uz': ["Mariana trogi", "Puerto-Riko trogi", "Java trogi", "Tonga trogi"], 'ru': ["Марианская впадина", "Пуэрто-Рико", "Яванский жёлоб", "Тонга"], 'en': ["Mariana Trench", "Puerto Rico Trench", "Java Trench", "Tonga Trench"]},
        'correct': 0,
        'explanation': {'uz': "Mariana trogi — 11,034 m chuqurligi bilan dunyodagi eng chuqur joy, Tinch okeanida."}
    },
    {
        'uz': "Nil daryosi qaysi okean/dengizga quyiladi?",
        'options': {'uz': ["O'rta yer dengizi", "Qizil dengiz", "Hind okeani", "Atlantika okeani"], 'ru': ["Средиземное море", "Красное море", "Индийский океан", "Атлантический океан"], 'en': ["Mediterranean Sea", "Red Sea", "Indian Ocean", "Atlantic Ocean"]},
        'correct': 0,
        'explanation': {'uz': "Nil daryosi Shimoliy Afrikada oqib, O'rta yer dengiziga quyiladi."}
    },
    {
        'uz': "Dunyodagi eng katta ko'l qaysi?",
        'options': {'uz': ["Kaspiy dengizi", "Baykal", "Viktoriya", "Superyor"], 'ru': ["Каспийское море", "Байкал", "Виктория", "Верхнее"], 'en': ["Caspian Sea", "Baikal", "Victoria", "Superior"]},
        'correct': 0,
        'explanation': {'uz': "Kaspiy dengizi 371,000 km² maydoni bilan dunyodagi eng katta ko'l (dengiz emas — tuz ko'li)."}
    },

    # ── LITOSFERA ─────────────────────────────────────────────────────────
    {
        'uz': "Yer po'stining eng yuqori qatlami nima deyiladi?",
        'options': {'uz': ["Litosfera", "Mantiya", "Yadro", "Astenosfera"], 'ru': ["Литосфера", "Мантия", "Ядро", "Астеносфера"], 'en': ["Lithosphere", "Mantle", "Core", "Asthenosphere"]},
        'correct': 0,
        'explanation': {'uz': "Litosfera — Yer po'sti va mantiyaning yuqori qismidan iborat qattiq qatlam."}
    },
    {
        'uz': "Vulqon otilishi natijasida hosil bo'ladigan tog' jinslari qaysi?",
        'options': {'uz': ["Magmatik", "Cho'kindi", "Metamorfik", "Organogen"], 'ru': ["Магматические", "Осадочные", "Метаморфические", "Органогенные"], 'en': ["Igneous", "Sedimentary", "Metamorphic", "Organogenic"]},
        'correct': 0,
        'explanation': {'uz': "Magmatik tog' jinslari (granit, bazalt) magmaning sovishi natijasida hosil bo'ladi."}
    },
    {
        'uz': "Eng katta tektonik lita plita qaysi?",
        'options': {'uz': ["Tinch okean plitasi", "Yevroosiyo plitasi", "Afrika plitasi", "Hindiston plitasi"], 'ru': ["Тихоокеанская", "Евразийская", "Африканская", "Индийская"], 'en': ["Pacific Plate", "Eurasian Plate", "African Plate", "Indian Plate"]},
        'correct': 0,
        'explanation': {'uz': "Tinch okean plitasi — 103 million km² bilan Yerdagi eng katta tektonik plita."}
    },

    # ── JAHON GEOGRAFIYASI ────────────────────────────────────────────────
    {
        'uz': "Dunyodagi eng uzun tog' tizmasi qaysi?",
        'options': {'uz': ["And tog'lari", "Himoloy", "Rokki tog'lari", "Alp tog'lari"], 'ru': ["Анды", "Гималаи", "Скалистые горы", "Альпы"], 'en': ["Andes", "Himalayas", "Rocky Mountains", "Alps"]},
        'correct': 0,
        'explanation': {'uz': "And tog'lari — 7,000 km uzunligi bilan quruqlikdagi eng uzun tog' tizmasi, Janubiy Amerikada."}
    },
    {
        'uz': "Amazon daryosi qaysi davlatdan manba oladi?",
        'options': {'uz': ["Peru", "Braziliya", "Kolumbiya", "Venesuela"], 'ru': ["Перу", "Бразилия", "Колумбия", "Венесуэла"], 'en': ["Peru", "Brazil", "Colombia", "Venezuela"]},
        'correct': 0,
        'explanation': {'uz': "Amazon daryosi Peru Andlarida boshlanadi va Braziliya orqali Atlantika okeaniga quyiladi."}
    },
    {
        'uz': "Sahara cho'li qaysi qit'ada joylashgan?",
        'options': {'uz': ["Afrika", "Osiyo", "Avstraliya", "Amerika"], 'ru': ["Африка", "Азия", "Австралия", "Америка"], 'en': ["Africa", "Asia", "Australia", "America"]},
        'correct': 0,
        'explanation': {'uz': "Sahara cho'li — 9.2 million km² maydoni bilan dunyodagi eng katta issiq cho'l, Shimoliy Afrikada."}
    },
    {
        'uz': "Dunyo aholisining taxminan qancha foizi Osiyoda istiqomat qiladi?",
        'options': {'uz': ["60%", "40%", "50%", "70%"], 'ru': ["60%", "40%", "50%", "70%"], 'en': ["60%", "40%", "50%", "70%"]},
        'correct': 0,
        'explanation': {'uz': "Osiyo — 4.8 milliard aholisi bilan dunyodagi eng ko'p aholi istiqomat qiladigan qit'a (~60%)."}
    },
    {
        'uz': "Ekvator qaysi qit'alardan o'tadi?",
        'options': {'uz': ["Afrika, Osiyo, Janubiy Amerika", "Yevropa, Afrika, Osiyo", "Shimoliy Amerika, Osiyo, Avstraliya", "Afrika, Shimoliy Amerika, Osiyo"],
                    'ru': ["Африка, Азия, Ю. Америка", "Европа, Африка, Азия", "С. Америка, Азия, Австралия", "Африка, С. Америка, Азия"],
                    'en': ["Africa, Asia, S. America", "Europe, Africa, Asia", "N. America, Asia, Australia", "Africa, N. America, Asia"]},
        'correct': 0,
        'explanation': {'uz': "Ekvator Afrikadan, Osiyodan (Indoneziya) va Janubiy Amerikadan (Braziliya, Ekvador, Kolumbiya) o'tadi."}
    },
    {
        'uz': "Dunyodagi eng katta arhipelag (orollar guruhi) qaysi?",
        'options': {'uz': ["Malayziya arxipelagi", "Britaniya orollari", "Yaponiya orollari", "Karib orollari"],
                    'ru': ["Малайский архипелаг", "Британские острова", "Японские острова", "Карибские острова"],
                    'en': ["Malay Archipelago", "British Isles", "Japanese Islands", "Caribbean Islands"]},
        'correct': 0,
        'explanation': {'uz': "Malayziya arxipelagi — 25,000 dan ortiq orollar bilan dunyodagi eng katta arxipelag."}
    },
    {
        'uz': "Qaysi davlat ikki qit'a (Yevropa va Osiyo) hududida joylashgan?",
        'options': {'uz': ["Rossiya", "Turkiya", "Misr", "Qozog'iston"],
                    'ru': ["Россия", "Турция", "Египет", "Казахстан"],
                    'en': ["Russia", "Turkey", "Egypt", "Kazakhstan"]},
        'correct': 0,
        'explanation': {'uz': "Rossiya ham Yevropa, ham Osiyo qit'asida joylashgan — ikki qit'aga mansub eng katta davlat."}
    },

    # ── IQLIM ─────────────────────────────────────────────────────────────
    {
        'uz': "Ekvatorial iqlim mintaqasida yog'ingarchilik yiliga necha mm bo'ladi?",
        'options': {'uz': ["2000 mm dan ortiq", "500 mm", "100 mm dan kam", "1000 mm"],
                    'ru': ["Более 2000 мм", "500 мм", "Менее 100 мм", "1000 мм"],
                    'en': ["Over 2000 mm", "500 mm", "Under 100 mm", "1000 mm"]},
        'correct': 0,
        'explanation': {'uz': "Ekvatorial iqlimda yil bo'yi yog'in ko'p — 2000-3000 mm va undan ham yuqori."}
    },
    {
        'uz': "Monsun shamollari ko'proq qaysi mintaqada kuzatiladi?",
        'options': {'uz': ["Janubi-Sharqiy Osiyo", "G'arbiy Yevropa", "Markaziy Osiyo", "Arktika"],
                    'ru': ["Юго-Восточная Азия", "Западная Европа", "Центральная Азия", "Арктика"],
                    'en': ["South-East Asia", "Western Europe", "Central Asia", "Arctic"]},
        'correct': 0,
        'explanation': {'uz': "Monsun shamollari Janubi-Sharqiy Osiyo, Hindiston, Xitoy kabi mintaqalarda kuchli namoyon bo'ladi."}
    },
    {
        'uz': "Qaysi omil Yer iqlimiga eng kuchli ta'sir ko'rsatadi?",
        'options': {'uz': ["Quyosh radiatsiyasi", "Dengiz oqimlari", "Rel'ef", "Inson faoliyati"],
                    'ru': ["Солнечная радиация", "Морские течения", "Рельеф", "Деятельность человека"],
                    'en': ["Solar radiation", "Ocean currents", "Relief", "Human activity"]},
        'correct': 0,
        'explanation': {'uz': "Quyosh radiatsiyasi — iqlimga ta'sir qiluvchi asosiy omil, chunki barcha issiqliqning manbai."}
    },

    # ── AHOLI GEOGRAFIYASI ───────────────────────────────────────────────
    {
        'uz': "Dunyo aholisi hozirda taxminan qancha?",
        'options': {'uz': ["8 milliard", "6 milliard", "10 milliard", "5 milliard"],
                    'ru': ["8 миллиардов", "6 миллиардов", "10 миллиардов", "5 миллиардов"],
                    'en': ["8 billion", "6 billion", "10 billion", "5 billion"]},
        'correct': 0,
        'explanation': {'uz': "2023-yil boshida Yer aholisi 8 milliard kishidan oshdi."}
    },
    {
        'uz': "Aholining eng zich joylashgan qit'asi qaysi?",
        'options': {'uz': ["Osiyo", "Yevropa", "Afrika", "Shimoliy Amerika"],
                    'ru': ["Азия", "Европа", "Африка", "Северная Америка"],
                    'en': ["Asia", "Europe", "Africa", "North America"]},
        'correct': 0,
        'explanation': {'uz': "Osiyo qit'asi — 150 kishi/km² o'rtacha zichlik bilan eng ko'p aholiga ega."}
    },

    # ── QO'SHIMCHA SAVOL ─────────────────────────────────────────────────
    {
        'uz': "Qaysi mamlakat dengizga chiqish imkoniyatiga ega emas (ichki davlat)?",
        'options': {'uz': ["O'zbekiston", "Eron", "Pokiston", "Hindiston"],
                    'ru': ["Узбекистан", "Иран", "Пакистан", "Индия"],
                    'en': ["Uzbekistan", "Iran", "Pakistan", "India"]},
        'correct': 0,
        'explanation': {'uz': "O'zbekiston — ikki marta quruqlik bilan o'ralgan (doubly landlocked) davlatlardan biri."}
    },
    {
        'uz': "Markaziy Osiyoda nechta davlat bor?",
        'options': {'uz': ["5", "4", "6", "3"],
                    'ru': ["5", "4", "6", "3"],
                    'en': ["5", "4", "6", "3"]},
        'correct': 0,
        'explanation': {'uz': "Markaziy Osiyo: Qozog'iston, O'zbekiston, Turkmaniston, Tojikiston, Qirg'iziston — jami 5 ta davlat."}
    },
]
