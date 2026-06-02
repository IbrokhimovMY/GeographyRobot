"""
Date-based geographic facts in Uzbek.
Each entry: (month, day, year, text_uz, text_ru, text_en)
year=0 means the year is already in the text.
"""

# Format: (month, day, year, uz_text, ru_text, en_text)
UZ_DATE_FACTS = [
    # YANVAR
    (1, 1, 1804, "Gaiti mustaqil davlatga aylandi. U Amerika qit'asidagi birinchi respublika va dunyodagi birinchi qora tanli aholisi boshqargan mamlakat bo'ldi.",
     "Гаити стала независимым государством — первой республикой в Америке под управлением чернокожего населения.",
     "Haiti became independent — the first republic in the Americas governed by Black people."),

    (1, 14, 1907, "O'zbekiston hududida kuchli Qaratog' zilzilasi sodir bo'ldi. 12 000 dan ortiq kishi halok bo'ldi, shahar va qishloqlar vayron etildi.",
     "На территории Узбекистана произошло мощное Каратагское землетрясение, унёсшее жизни более 12 000 человек.",
     "A powerful earthquake struck Central Asia near Karatag, killing over 12,000 people."),

    (1, 24, 1857, "Ulkan Shimoliy Muzli okean eskpeditsiyasi yakunlandi. Olimlar dengizning xaritasini tuzishda yangi kashfiyotlar qildilar.",
     "Завершилась крупная экспедиция по Северному Ледовитому океану с новыми географическими открытиями.",
     "A major Arctic Ocean expedition concluded with new geographic discoveries."),

    (1, 31, 1990, "Moskvada McDonald's birinchi doʻkoni ochildi va bir kunda 30 000 nafar tashrif buyuruvchi keldi. Bu Sovyet Ittifoqidagi yirik madaniy oʻzgarishning belgisi boʻldi.",
     "В Москве открылся первый McDonald's, посетили которого 30 000 человек за один день.",
     "McDonald's opened its first Moscow location, drawing 30,000 visitors in one day."),

    # FEVRAL
    (2, 4, 1948, "Shri-Lanka (o'sha paytda Seylon) Buyuk Britaniyadan mustaqillikka erishdi. Hind okeanidagi bu orol davlat o'z yo'lini boshladi.",
     "Шри-Ланка (тогда Цейлон) получила независимость от Великобритании.",
     "Sri Lanka (then Ceylon) gained independence from Britain."),

    (2, 11, 1990, "Nelson Mandela Janubiy Afrika qamoqxonasidan ozod qilindi. Bu voqea Janubiy Afrika tarixida yangi sahifani ochdi.",
     "Нельсон Мандела был освобождён из южноафриканской тюрьмы.",
     "Nelson Mandela was released from a South African prison."),

    (2, 20, 1962, "Amerikalik astronavt John Glenn Yer atrofini uchta orbitada aylanib o'tdi. Bu AQSH kosmik tadqiqotlarida muhim qadam bo'ldi.",
     "Американский астронавт Джон Гленн совершил три витка вокруг Земли.",
     "American astronaut John Glenn orbited Earth three times."),

    (2, 27, 1991, "Quvayt iroqlik kuchlardan ozod qilindi. Ikki haftalik urushdan so'ng Quvayt o'z mustaqilligini tikladi.",
     "Кувейт был освобождён от иракских войск после двухнедельной войны.",
     "Kuwait was liberated from Iraqi forces after a two-week war."),

    # MART
    (3, 5, 1963, "Patrice Lumumba g'oyalari asosida Kongo Demokratik Respublikasi ilk bor dunyo e'tirofiga sazovor bo'ldi.",
     "Демократическая Республика Конго получила международное признание.",
     "The Democratic Republic of Congo gained international recognition."),

    (3, 12, 1912, "Girl Scouts (Qizlar skautlar) tashkiloti AQSH da tashkil etildi. Hozir u dunyoning 150 dan ortiq mamlakatida faoliyat yuritadi.",
     "В США основана организация Girl Scouts, ныне действующая в 150+ странах.",
     "Girl Scouts of America was founded; now active in 150+ countries."),

    (3, 21, 1960, "Janubiy Afrikada Sharpevil qirg'ini sodir bo'ldi. Apartheid tizimiga qarshi tinch namoyishchilar otib o'ldirildi.",
     "Произошла резня в Шарпевиле: расстрел мирных демонстрантов против апартеида в ЮАР.",
     "The Sharpeville massacre occurred in South Africa; peaceful anti-apartheid protesters were shot."),

    (3, 28, 1979, "Tri Mayl Aylend (Pensilvaniya, AQSH) atom elektr stantsiyasida avaria sodir bo'ldi. Bu katta ekologik inqirozga olib keldi.",
     "Произошла авария на АЭС Три-Майл-Айленд в США — крупнейшая экологическая катастрофа.",
     "The Three Mile Island nuclear accident occurred in Pennsylvania — the worst US nuclear disaster."),

    # APREL
    (4, 12, 1961, "Yuriy Gagarin kosmosga uchgan birinchi inson bo'ldi. U Yer atrofini 108 daqiqada aylanib qaytdi.",
     "Юрий Гагарин стал первым человеком в космосе, облетев Землю за 108 минут.",
     "Yuri Gagarin became the first human in space, orbiting Earth in 108 minutes."),

    (4, 18, 1906, "San-Fransisko shahri kuchli zilzila va yong'in natijasida deyarli butunlay vayron bo'ldi. 3 000 dan ortiq kishi halok bo'ldi.",
     "Сан-Франциско был почти полностью разрушен землетрясением и пожарами, погибло более 3 000 человек.",
     "San Francisco was devastated by earthquake and fire, killing over 3,000 people."),

    (4, 22, 1970, "Birinchi Yer kuni (Earth Day) nishonlandi. Bu atrof-muhitni muhofaza qilish harakatining boshlanishi bo'ldi.",
     "Отмечен первый День Земли, ставший началом экологического движения.",
     "The first Earth Day was celebrated, launching the global environmental movement."),

    (4, 26, 1986, "Ukrainada (o'sha paytda SSSR) Chernobil atom elektr stantsiyasida portlash sodir bo'ldi. Bu eng katta texnogen falokatlardan biri bo'ldi.",
     "На Чернобыльской АЭС в Украине произошёл взрыв — одна из крупнейших техногенных катастроф.",
     "The Chernobyl nuclear plant exploded in Ukraine — one of the worst industrial disasters ever."),

    # MAY
    (5, 1, 1884, "Nyu-Yorkda dunyo bo'yicha birinchi osma ko'prik — Bruklin ko'prigi ochildi. U o'sha davrning muhandislik mo'jizasi edi.",
     "В Нью-Йорке открылся Бруклинский мост — первый подвесной мост в мире.",
     "The Brooklyn Bridge opened in New York — the world's first suspension bridge."),

    (5, 9, 1945, "Ikkinchi Jahon urushi Yevropa teatrida tugadi. Germaniya so'zsiz taslim bo'ldi va Yevropa ozod bo'ldi.",
     "Завершилась Вторая мировая война в Европе — Германия капитулировала.",
     "World War II ended in Europe as Germany surrendered unconditionally."),

    (5, 29, 1953, "Edmund Hillary va Tenzing Norgay Everest cho'qqisiga birinchi bo'lib ko'tarildilar. Bu insoniytning 8849 metr balandlikdagi g'alabasi edi.",
     "Эдмунд Хиллари и Тенцинг Норгей первыми покорили вершину Эверест (8849 м).",
     "Edmund Hillary and Tenzing Norgay became the first to summit Everest (8,849 m)."),

    (5, 31, 1859, "London'dagi mashhur Big Ben soat minorasi birinchi marta chindi. U Temza daryosi bo'yida Britaniya ramziga aylandi.",
     "Знаменитый Биг-Бен в Лондоне впервые пробил часы над берегом Темзы.",
     "London's iconic Big Ben chimed for the first time on the banks of the Thames."),

    # IYUN
    (6, 5, 1981, "AQSHda birinchi SPID holati qayd etildi. Bu kasallik keyinchalik butun dunyoga tarqalib yuz minglab hayotni oʻchirib yubordi.",
     "В США зафиксирован первый случай СПИДа — болезни, унёсшей жизни миллионов по всему миру.",
     "The first AIDS case was recorded in the US — a disease that would claim millions of lives worldwide."),

    (6, 6, 1944, "D-Day — Ittifoqchi kuchlar Normandiya (Fransiya) qirg'oqlariga qariyb 156 000 askar bilan tushdi. Bu urushning burilish nuqtasi bo'ldi.",
     "День Д: войска союзников высадились в Нормандии — переломный момент Второй мировой.",
     "D-Day: Allied forces landed in Normandy with 156,000 troops — a turning point in WWII."),

    (6, 21, 1788, "AQSH Konstitutsiyasi kuchga kirdi. Bu federal respublika tuzilishini rasmiy tartibga solgan birinchi hujjat edi.",
     "Конституция США вступила в силу, официально закрепив структуру федеральной республики.",
     "The US Constitution went into effect, officially establishing the federal republic."),

    # IYUL
    (7, 4, 1776, "Amerika Qo'shma Shtatlari mustaqilligini e'lon qildi. 13 ta koloniya Britaniya imperiyasidan ajralib o'z yo'lini boshladi.",
     "США провозгласили независимость. 13 колоний отделились от Британской империи.",
     "The United States declared independence, with 13 colonies breaking from Britain."),

    (7, 14, 1789, "Fransiya inqilobi boshlanishi — Bastiliya qal'asi egallab olindi. Bu Yevropada yangi siyosiy davrning boshlanishi edi.",
     "Началась Французская революция: взятие Бастилии — начало новой политической эры в Европе.",
     "The French Revolution began with the storming of the Bastille."),

    (7, 20, 1969, "Nil Armstrong Oyga qadam qo'ygan birinchi inson bo'ldi. 'Bu inson uchun kichik qadam, insoniyat uchun ulkan sakrash' dedi u.",
     "Нил Армстронг стал первым человеком на Луне: 'Маленький шаг человека — гигантский прыжок человечества'.",
     "Neil Armstrong became the first human on the Moon: 'One small step for man...'"),

    # AVGUST
    (8, 6, 1945, "AQSH Yaponiyaning Xirosima shahriga atom bombasi tashladi. Bir lahzada 80 000 kishi halok bo'ldi.",
     "США сбросили атомную бомбу на японский город Хиросима. Мгновенно погибли 80 000 человек.",
     "The US dropped an atomic bomb on Hiroshima, Japan, instantly killing 80,000 people."),

    (8, 24, 79, "Vezuviy vulqoni otilishi natijasida Rimning Pompey shahri kulga ko'mildi. Bu voqea arxeologiya tarixidagi eng muhim topilmalardan biriga aylandi.",
     "Извержение Везувия уничтожило Помпею. Этот город стал важнейшей археологической находкой.",
     "Mount Vesuvius erupted, burying the Roman city of Pompeii in ash."),

    (8, 31, 1991, "O'zbekiston Sovet Ittifoqidan mustaqilligini e'lon qildi. Bu Markaziy Osiyoda yangi tarixning boshlanishi edi.",
     "Узбекистан объявил о независимости от Советского Союза — начало новой истории Центральной Азии.",
     "Uzbekistan declared independence from the Soviet Union."),

    # SENTABR
    (9, 1, 1939, "Germaniya Polshaga hujum qildi va Ikkinchi Jahon urushi boshlandi. Dunyo tarixidagi eng dahshatli mojaro 6 yil davom etdi.",
     "Германия напала на Польшу, начав Вторую мировую войну — самый разрушительный конфликт в истории.",
     "Germany invaded Poland, starting World War II — the deadliest conflict in human history."),

    (9, 11, 2001, "AQSH'da terroristik hujumlar sodir bo'ldi. Nyu-York, Vashington va Pensilvaniyada 3 000 dan ortiq kishi halok bo'ldi.",
     "В США произошли теракты. В Нью-Йорке, Вашингтоне и Пенсильвании погибли более 3 000 человек.",
     "Terrorist attacks struck the US. Over 3,000 people were killed in New York, Washington, and Pennsylvania."),

    (9, 16, 1920, "Nyu-York moliyaviy markazi yaqinida portlash yuz berdi. Bu AQSH tarixidagi birinchi katta terroristik hujumlardan biri edi.",
     "Взрыв у финансового центра Нью-Йорка — один из первых крупных терактов в истории США.",
     "A bomb exploded near New York's financial district — one of the first major terrorist attacks in US history."),

    (9, 21, 1991, "Armaniston mustaqilligini e'lon qildi. Kavkaz tog'lari orasida joylashgan bu mamlakat yangi tarixini boshladi.",
     "Армения провозгласила независимость — горная страна Южного Кавказа начала новую историю.",
     "Armenia declared independence — the mountain country of the South Caucasus began a new era."),

    # OKTABR
    (10, 4, 1957, "Sovet Ittifoqi birinchi sun'iy Yer yo'ldoshi — Sputnik-1'ni kosmosga chiqardi. Kosmik musobaqa boshlanishi shu kundan hisoblangan.",
     "СССР запустил первый искусственный спутник Земли — Спутник-1, начав космическую гонку.",
     "The USSR launched Sputnik-1, the first artificial satellite, starting the Space Race."),

    (10, 12, 1492, "Xristofor Kolumb Amerika qit'asining qirg'oqlariga yetib keldi. Bu voqea dunyo tarixidagi buyuk geografik kashfiyotlardan biri bo'ldi.",
     "Христофор Колумб достиг берегов Америки — одно из величайших географических открытий в истории.",
     "Christopher Columbus reached the Americas — one of the greatest geographic discoveries in history."),

    (10, 24, 1945, "Birlashgan Millatlar Tashkiloti (BMT) rasman tashkil etildi. Hozir unga 193 ta davlat a'zo.",
     "Официально основана ООН. Сегодня её членами являются 193 государства.",
     "The United Nations was officially founded. Today it has 193 member states."),

    # NOYABR
    (11, 9, 1989, "Berlin devori qulatildi. Sharqiy va G'arbiy Germaniyani 28 yil ajratib turgan bu devor tarix sahnasidan ketdi.",
     "Берлинская стена пала. Стена, 28 лет разделявшая Германию, была снесена.",
     "The Berlin Wall fell, ending 28 years of division between East and West Germany."),

    (11, 22, 1963, "AQSH prezidenti Jon F. Kennedi Dallas shahrida otib o'ldirildi. Bu mamlakatni chuqur qayg'uga botirdi.",
     "Президент США Джон Ф. Кеннеди был убит в Далласе, повергнув страну в глубокий траур.",
     "US President John F. Kennedy was assassinated in Dallas, plunging the nation into grief."),

    (11, 30, 1835, "Amerikalik yozuvchi Mark Tven tug'ildi. Missisipi daryosi bo'ylarida o'sgan u keyinchalik Amerika adabiyotining klassigiga aylandi.",
     "Родился американский писатель Марк Твен, выросший на берегах Миссисипи.",
     "American writer Mark Twain was born, who grew up along the Mississippi River."),

    # DEKABR
    (12, 7, 1941, "Yaponiya AQSH'ning Pearl Harbor dengiz bazasiga hujum qildi. Bu AQSH'ning Ikkinchi Jahon urushiga qo'shilishiga sabab bo'ldi.",
     "Япония атаковала американскую военно-морскую базу Пёрл-Харбор, втянув США во Вторую мировую.",
     "Japan attacked the US naval base at Pearl Harbor, drawing America into World War II."),

    (12, 10, 1898, "Ispan-Amerika urushi tugadi. Ispaniya Kuba, Puerto-Riko, Guam va Filippinni AQSH'ga berdi.",
     "Закончилась Испано-американская война. Испания уступила Кубу, Пуэрто-Рико, Гуам и Филиппины.",
     "The Spanish-American War ended. Spain ceded Cuba, Puerto Rico, Guam, and Philippines to the US."),

    (12, 25, 1991, "Sovet Ittifoqi rasman tarqatib yuborildi va Gorbachev prezidentlikdan iste'fo berdi. 15 ta yangi mustaqil davlat tashkil topdi.",
     "СССР официально прекратил существование. Горбачёв ушёл в отставку, образовав 15 независимых государств.",
     "The Soviet Union officially dissolved. 15 new independent states were formed."),

    (12, 26, 2004, "Hind okeanida kuchli zilzila natijasida tsunami sodir bo'ldi. 14 ta mamlakatda 230 000 dan ortiq kishi halok bo'ldi.",
     "Цунами в Индийском океане унесло жизни более 230 000 человек в 14 странах.",
     "An Indian Ocean tsunami killed over 230,000 people across 14 countries."),
]
