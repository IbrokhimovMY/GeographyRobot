import random
import telegram
from telegram import ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, JobQueue
from typing import List, Dict, Set
import json

# Comprehensive list of countries in Uzbek
COUNTRIES = [
    "Afgʻoniston", "Albaniya", "Jazoir", "Andorra", "Angola", "Antigua va Barbuda",
    "Argentina", "Armaniston", "Avstraliya", "Avstriya", "Ozarbayjon", "Bagama orollari",
    "Bahrayn", "Bangladesh", "Barbados", "Belarus", "Belgiya", "Beliz", "Benin",
    "Butan", "Boliviya", "Bosniya va Gertsegovina", "Botsvana", "Braziliya", "Bruney",
    "Bolgariya", "Burkina Faso", "Burundi", "Kabo Verde", "Kambodja", "Kamerun",
    "Kanada", "Markaziy Afrika Respublikasi", "Chad", "Chili", "Xitoy", "Kolumbiya",
    "Komor orollari", "Kongo Demokratik Respublikasi", "Kongo Respublikasi",
    "Kosta Rika", "Xorvatiya", "Kuba", "Qibris", "Chexiya", "Daniya", "Jibuti",
    "Dominika", "Dominikan Respublikasi", "Ekvador", "Misr", "Salvador",
    "Ekvatorial Gvineya", "Eritreya", "Estoniya", "Esvatini", "Efiopiya", "Fiji",
    "Finlandiya", "Fransiya", "Gabon", "Gambiya", "Gruziya", "Germaniya", "Gana",
    "Gretsiya", "Grenada", "Gvatemala", "Gvineya", "Gvineya-Bisau", "Gayana",
    "Gaiti", "Gonduras", "Vengriya", "Islandiya", "Hindiston", "Indoneziya", "Eron",
    "Iroq", "Irlandiya", "Isroil", "Italiya", "Yamayka", "Yaponiya", "Iordaniya",
    "Qozogʻiston", "Keniya", "Kiribati", "Kuvayt", "Qirgʻiziston", "Laos", "Latviya",
    "Livan", "Lesoto", "Liberiya", "Liviya", "Lixtenshteyn", "Litva", "Lyuksemburg",
    "Madagaskar", "Malavi", "Malayziya", "Maldiv orollari", "Mali", "Malta",
    "Marshall orollari", "Mavritaniya", "Mavrikiy", "Meksika", "Mikroneziya",
    "Moldova", "Monako", "Moʻgʻuliston", "Chernogoriya", "Marokash", "Mozambik",
    "Myanma", "Namibiya", "Nauru", "Nepal", "Niderlandiya", "Yangi Zelandiya",
    "Nikaragua", "Niger", "Nigeriya", "Shimoliy Koreya", "Shimoliy Makedoniya",
    "Norvegiya", "Ummon", "Pokiston", "Palau", "Falastin", "Panama",
    "Papua Yangi Gvineya", "Paragvay", "Peru", "Filippin", "Polsha", "Portugaliya",
    "Qatar", "Ruminiya", "Rossiya", "Ruanda", "Sent Kitts va Nevis", "Sent Lusiya",
    "Sent Vinsent va Grenadinlar", "Samoa", "San Marino", "San-Tome va Prinsipi",
    "Saudiya Arabistoni", "Senegal", "Serbiya", "Seyshell orollari", "Syerra Leone",
    "Singapur", "Slovakiya", "Sloveniya", "Solomon orollari", "Somali", "Janubiy Afrika",
    "Janubiy Koreya", "Janubiy Sudan", "Ispaniya", "Shri Lanka", "Sudan", "Surinam",
    "Shvetsiya", "Shveytsariya", "Suriya", "Tayvan", "Tojikiston", "Tanzaniya",
    "Tailand", "Sharqiy Timor", "Togo", "Tonga", "Trinidad va Tobago", "Tunis",
    "Turkiya", "Turkmaniston", "Tuvalu", "Uganda", "Ukraina", "Birlashgan Arab Amirliklari",
    "Buyuk Britaniya", "Amerika Qoʻshma Shtatlari", "Urugvay", "Oʻzbekiston",
    "Vanuatu", "Vatikan", "Venesuela", "Vyetnam", "Yaman", "Zambiya", "Zimbabve"
]

# Dictionary of countries and their capitals in Uzbek
countries_capitals = {
    "Afgʻoniston": "Kobul",
    "Albaniya": "Tirana",
    "Jazoir": "Jazoir",
    "Andorra": "Andorra la Vella",
    "Angola": "Luanda",
    "Antigua va Barbuda": "Sent-Jons",
    "Argentina": "Buenos-Ayres",
    "Armaniston": "Yerevan",
    "Avstraliya": "Kanberra",
    "Avstriya": "Vena",
    "Ozarbayjon": "Boku",
    "Bagama orollari": "Nassau",
    "Bahrayn": "Manama",
    "Bangladesh": "Dakka",
    "Barbados": "Bridjtaun",
    "Belarus": "Minsk",
    "Belgiya": "Bryussel",
    "Beliz": "Belmopan",
    "Benin": "Porto-Novo",
    "Butan": "Thimphu",
    "Boliviya": "Sukre",
    "Bosniya va Gertsegovina": "Sarayevo",
    "Botsvana": "Gaborone",
    "Braziliya": "Brazilia",
    "Bruney": "Bandar Seri Begavon",
    "Bolgariya": "Sofiya",
    "Burkina Faso": "Uagadugu",
    "Burundi": "Gitega",
    "Kabo Verde": "Praya",
    "Kambodja": "Pnompen",
    "Kamerun": "Yaunde",
    "Kanada": "Ottava",
    "Markaziy Afrika Respublikasi": "Bangui",
    "Chad": "Njamena",
    "Chili": "Santyago",
    "Xitoy": "Pekin",
    "Kolumbiya": "Bogota",
    "Komor orollari": "Moroni",
    "Kongo Demokratik Respublikasi": "Kinshasa",
    "Kongo Respublikasi": "Brazzavil",
    "Kosta Rika": "San-Xose",
    "Xorvatiya": "Zagreb",
    "Kuba": "Gavana",
    "Qibris": "Nikosiya",
    "Chexiya": "Praga",
    "Daniya": "Kopengagen",
    "Jibuti": "Jibuti",
    "Dominika": "Rozo",
    "Dominikan Respublikasi": "Santo-Domingo",
    "Ekvador": "Kito",
    "Misr": "Qohira",
    "Salvador": "San-Salvador",
    "Ekvatorial Gvineya": "Malabo",
    "Eritreya": "Asmara",
    "Estoniya": "Tallin",
    "Esvatini": "Mbabane",
    "Efiopiya": "Addis-Abeba",
    "Fiji": "Suva",
    "Finlandiya": "Xelsinki",
    "Fransiya": "Parij",
    "Gabon": "Librevil",
    "Gambiya": "Banjul",
    "Gruziya": "Tbilisi",
    "Germaniya": "Berlin",
    "Gana": "Akkra",
    "Gretsiya": "Afina",
    "Grenada": "Sent-Jorj",
    "Gvatemala": "Gvatemala Siti",
    "Gvineya": "Konakri",
    "Gvineya-Bisau": "Bisau",
    "Gayana": "Jorjtaun",
    "Gaiti": "Port-o-Prens",
    "Gonduras": "Tegusigalpa",
    "Vengriya": "Budapesht",
    "Islandiya": "Reykyavik",
    "Hindiston": "Yangi Dehli",
    "Indoneziya": "Jakarta",
    "Eron": "Tehron",
    "Iroq": "Bagʻdod",
    "Irlandiya": "Dublin",
    "Isroil": "Tel Aviv",
    "Italiya": "Rim",
    "Yamayka": "Kingston",
    "Yaponiya": "Tokio",
    "Iordaniya": "Ammon",
    "Qozogʻiston": "Astana",
    "Keniya": "Nayrobi",
    "Kiribati": "Tarava",
    "Kuvayt": "Kuvayt Siti",
    "Qirgʻiziston": "Bishkek",
    "Laos": "Vientian",
    "Latviya": "Riga",
    "Livan": "Bayrut",
    "Lesoto": "Maseru",
    "Liberiya": "Monroviya",
    "Liviya": "Tripoli",
    "Lixtenshteyn": "Vaduz",
    "Litva": "Vilnyus",
    "Lyuksemburg": "Lyuksemburg",
    "Madagaskar": "Antananarivo",
    "Malavi": "Lilongve",
    "Malayziya": "Kuala-Lumpur",
    "Maldiv orollari": "Male",
    "Mali": "Bamako",
    "Malta": "Valletta",
    "Marshall orollari": "Majuro",
    "Mavritaniya": "Nuakshot",
    "Mavrikiy": "Port-Lui",
    "Meksika": "Mexiko Siti",
    "Mikroneziya": "Palikir",
    "Moldova": "Kishinyov",
    "Monako": "Monako",
    "Moʻgʻuliston": "Ulan-Bator",
    "Chernogoriya": "Podgoritsa",
    "Marokash": "Rabat",
    "Mozambik": "Maputo",
    "Myanma": "Naypyido",
    "Namibiya": "Vindhuk",
    "Nauru": "Yaren",
    "Nepal": "Katmandu",
    "Niderlandiya": "Amsterdam",
    "Yangi Zelandiya": "Vellington",
    "Nikaragua": "Managua",
    "Niger": "Niamey",
    "Nigeriya": "Abuja",
    "Shimoliy Koreya": "Pxenyan",
    "Shimoliy Makedoniya": "Skopye",
    "Norvegiya": "Oslo",
    "Ummon": "Maskat",
    "Pokiston": "Islomobod",
    "Palau": "Ngerulmud",
    "Falastin": "Sharqiy Quddus",
    "Panama": "Panama Siti",
    "Papua Yangi Gvineya": "Port-Moresbi",
    "Paragvay": "Asunsion",
    "Peru": "Lima",
    "Filippin": "Manila",
    "Polsha": "Varshava",
    "Portugaliya": "Lissabon",
    "Qatar": "Doha",
    "Ruminiya": "Buxarest",
    "Rossiya": "Moskva",
    "Ruanda": "Kigali",
    "Sent Kitts va Nevis": "Baster",
    "Sent Lusiya": "Kastri",
    "Sent Vinsent va Grenadinlar": "Kingstaun",
    "Samoa": "Apia",
    "San Marino": "San Marino",
    "San-Tome va Prinsipi": "San-Tome",
    "Saudiya Arabistoni": "Riyod",
    "Senegal": "Dakar",
    "Serbiya": "Belgrad",
    "Seyshell orollari": "Viktoriya",
    "Syerra Leone": "Fritaun",
    "Singapur": "Singapur",
    "Slovakiya": "Bratislava",
    "Sloveniya": "Lyublyana",
    "Solomon orollari": "Honiara",
    "Somali": "Mogadishu",
    "Janubiy Afrika": "Pretoriya",
    "Janubiy Koreya": "Seul",
    "Janubiy Sudan": "Juba",
    "Ispaniya": "Madrid",
    "Shri Lanka": "Shri Jayavardenepura Kotte",
    "Sudan": "Xartum",
    "Surinam": "Paramaribo",
    "Shvetsiya": "Stokgolm",
    "Shveytsariya": "Bern",
    "Suriya": "Damashq",
    "Tayvan": "Taypey",
    "Tojikiston": "Dushanbe",
    "Tanzaniya": "Dodoma",
    "Tailand": "Bangkok",
    "Sharqiy Timor": "Dili",
    "Togo": "Lome",
    "Tonga": "Nukualofa",
    "Trinidad va Tobago": "Port-of-Speyn",
    "Tunis": "Tunis",
    "Turkiya": "Anqara",
    "Turkmaniston": "Ashxobod",
    "Tuvalu": "Funafuti",
    "Uganda": "Kampala",
    "Ukraina": "Kiyev",
    "Birlashgan Arab Amirliklari": "Abu-Dabi",
    "Buyuk Britaniya": "London",
    "Amerika Qoʻshma Shtatlari": "Vashington, D.C.",
    "Urugvay": "Montevideo",
    "Oʻzbekiston": "Toshkent",
    "Vanuatu": "Port-Vila",
    "Vatikan": "Vatikan Siti",
    "Venesuela": "Karakas",
    "Vyetnam": "Xanoy",
    "Yaman": "Sano",
    "Zambiya": "Lusaka",
    "Zimbabve": "Harare"
}

# Dictionary of hints for countries in Uzbek
country_hints = {
    "Afgʻoniston": "Bu davlat Osiyoda joylashgan, poytaxti Kobul.",
    "Albaniya": "Yevropaning janubi-sharqida, Adriatik dengizi sohilida, poytaxti Tirana.",
    "Jazoir": "Afrikada eng katta maydonga ega, poytaxti Jazoir.",
    "Andorra": "Pireney togʻlarida kichik knyazlik, poytaxti Andorra la Vella.",
    "Angola": "Janubiy Afrikada, neft va olmos resurslari, poytaxti Luanda.",
    "Antigua va Barbuda": "Karib dengizidagi orollar, poytaxti Sent-Jons.",
    "Argentina": "Janubiy Amerikada, tango va futbol, poytaxti Buenos-Ayres.",
    "Armaniston": "Kavkazda, qadimiy monastirlar, poytaxti Yerevan.",
    "Avstraliya": "Okeaniyada, kenguru va koala, poytaxti Kanberra.",
    "Avstriya": "Yevropada, Alplar va klassik musiqa, poytaxti Vena.",
    "Ozarbayjon": "Kavkazda, Xazar dengizi, poytaxti Boku.",
    "Bagama orollari": "Karib dengizida, sayyohlik maskani, poytaxti Nassau.",
    "Bahrayn": "Fors koʻrfazidagi orol, poytaxti Manama.",
    "Bangladesh": "Janubiy Osiyoda, Ganges deltasi, poytaxti Dakka.",
    "Barbados": "Karib dengizida, reggae va plyajlar, poytaxti Bridjtaun.",
    "Belarus": "Yevropada, keng oʻrmonlar, poytaxti Minsk.",
    "Belgiya": "Yevropada, shokolad va vafli, poytaxti Bryussel.",
    "Beliz": "Markaziy Amerikada, Marjon riflari, poytaxti Belmopan.",
    "Benin": "Gʻarbiy Afrikada, Vudu dini, poytaxti Porto-Novo.",
    "Butan": "Himolaylarda, baxt indeksi, poytaxti Thimphu.",
    "Boliviya": "Janubiy Amerikada, And togʻlari, poytaxti Sukre.",
    "Bosniya va Gertsegovina": "Balkanda, tarixiy koʻpriklar, poytaxti Sarayevo.",
    "Botsvana": "Janubiy Afrikada, Okavango deltasi, poytaxti Gaborone.",
    "Braziliya": "Janubiy Amerikada, Amazon oʻrmonlari, poytaxti Brazilia.",
    "Bruney": "Janubi-Sharqiy Osiyoda, neft boyliklari, poytaxti Bandar Seri Begavon.",
    "Bolgariya": "Yevropada, Qora dengiz sohilida, poytaxti Sofiya.",
    "Burkina Faso": "Gʻarbiy Afrikada, savanna, poytaxti Uagadugu.",
    "Burundi": "Sharqiy Afrikada, Tanganyika koʻli, poytaxti Gitega.",
    "Kabo Verde": "Atlantika okeanida, orollar, poytaxti Praya.",
    "Kambodja": "Janubi-Sharqiy Osiyoda, Angkor Vat, poytaxti Pnompen.",
    "Kamerun": "Markaziy Afrikada, 'Afrikaning miniatyurasi', poytaxti Yaunde.",
    "Kanada": "Shimoliy Amerikada, xokkey, poytaxti Ottava.",
    "Markaziy Afrika Respublikasi": "Afrika markazida, resurslar, poytaxti Bangui.",
    "Chad": "Afrikada, Saxara choʻli, poytaxti Njamena.",
    "Chili": "Janubiy Amerikada, uzun sohil, poytaxti Santyago.",
    "Xitoy": "Osiyoda, Buyuk Xitoy devori, poytaxti Pekin.",
    "Kolumbiya": "Janubiy Amerikada, kofe, poytaxti Bogota.",
    "Komor orollari": "Hind okeanida, vanil, poytaxti Moroni.",
    "Kongo Demokratik Respublikasi": "Afrikada, Kongo daryosi, poytaxti Kinshasa.",
    "Kongo Respublikasi": "Markaziy Afrikada, tropik oʻrmonlar, poytaxti Brazzavil.",
    "Kosta Rika": "Markaziy Amerikada, ekoturizm, poytaxti San-Xose.",
    "Xorvatiya": "Yevropada, Adriatik orollari, poytaxti Zagreb.",
    "Kuba": "Karib dengizida, salsa raqsi, poytaxti Gavana.",
    "Qibris": "Oʻrta yer dengizida, ikkiga boʻlingan, poytaxti Nikosiya.",
    "Chexiya": "Yevropada, pivo va qal’alar, poytaxti Praga.",
    "Daniya": "Yevropada, Vikinglar merosi, poytaxti Kopengagen.",
    "Jibuti": "Afrika shoxida, Qizil dengiz, poytaxti Jibuti.",
    "Dominika": "Karib dengizida, vulqonlar, poytaxti Rozo.",
    "Dominikan Respublikasi": "Karib dengizida, merenge, poytaxti Santo-Domingo.",
    "Ekvador": "Janubiy Amerikada, Galapagos, poytaxti Kito.",
    "Misr": "Afrikada, Nil daryosi, poytaxti Qohira.",
    "Salvador": "Markaziy Amerikada, kichik davlat, poytaxti San-Salvador.",
    "Ekvatorial Gvineya": "Afrikada, neft resurslari, poytaxti Malabo.",
    "Eritreya": "Afrika shoxida, Qizil dengiz, poytaxti Asmara.",
    "Estoniya": "Yevropada, raqamli innovatsiyalar, poytaxti Tallin.",
    "Esvatini": "Janubiy Afrikada, monarxiya, poytaxti Mbabane.",
    "Efiopiya": "Afrikada, qahva vatani, poytaxti Addis-Abeba.",
    "Fiji": "Tinch okeanida, marjon riflari, poytaxti Suva.",
    "Finlandiya": "Yevropada, koʻllar va sauna, poytaxti Xelsinki.",
    "Fransiya": "Yevropada, Eyfel minorasi, poytaxti Parij.",
    "Gabon": "Afrikada, tropik oʻrmonlar, poytaxti Librevil.",
    "Gambiya": "Afrikada, kichik materik davlati, poytaxti Banjul.",
    "Gruziya": "Kavkazda, sharob an’analari, poytaxti Tbilisi.",
    "Germaniya": "Yevropada, Oktoberfest, poytaxti Berlin.",
    "Gana": "Gʻarbiy Afrikada, oltin va kakao, poytaxti Akkra.",
    "Gretsiya": "Yevropada, qadimiy xarobalar, poytaxti Afina.",
    "Grenada": "Karib dengizida, muskat yongʻogʻi, poytaxti Sent-Jorj.",
    "Gvatemala": "Markaziy Amerikada, Maya xarobalari, poytaxti Gvatemala Siti.",
    "Gvineya": "Gʻarbiy Afrikada, mineral resurslar, poytaxti Konakri.",
    "Gvineya-Bisau": "Gʻarbiy Afrikada, kaju yongʻogʻi, poytaxti Bisau.",
    "Gayana": "Janubiy Amerikada, Karib sohilida, poytaxti Jorjtaun.",
    "Gaiti": "Karib dengizida, kreol madaniyati, poytaxti Port-o-Prens.",
    "Gonduras": "Markaziy Amerikada, banan eksporti, poytaxti Tegusigalpa.",
    "Vengriya": "Yevropada, termal buloqlar, poytaxti Budapesht.",
    "Islandiya": "Yevropada, vulqonlar, poytaxti Reykyavik.",
    "Hindiston": "Janubiy Osiyoda, Taj Mahal, poytaxti Yangi Dehli.",
    "Indoneziya": "Janubi-Sharqiy Osiyoda, minglab orollar, poytaxti Jakarta.",
    "Eron": "Osiyoda, Fors madaniyati, poytaxti Tehron.",
    "Iroq": "Yaqin Sharqda, Mesopotamiya, poytaxti Bagʻdod.",
    "Irlandiya": "Yevropada, yashil landshaftlar, poytaxti Dublin.",
    "Isroil": "Yaqin Sharqda, diniy joylar, poytaxti Tel Aviv.",
    "Italiya": "Yevropada, Rim xarobalari, poytaxti Rim.",
    "Yamayka": "Karib dengizida, reggae musiqa, poytaxti Kingston.",
    "Yaponiya": "Osiyoda, sushi va samuraylar, poytaxti Tokio.",
    "Iordaniya": "Yaqin Sharqda, Petra shahri, poytaxti Ammon.",
    "Qozogʻiston": "Markaziy Osiyoda, keng dashtlar, poytaxti Astana.",
    "Keniya": "Sharqiy Afrikada, safari, poytaxti Nayrobi.",
    "Kiribati": "Tinch okeanida, kichik orollar, poytaxti Tarava.",
    "Kuvayt": "Fors koʻrfazida, neft iqtisodiyoti, poytaxti Kuvayt Siti.",
    "Qirgʻiziston": "Markaziy Osiyoda, togʻli landshaftlar, poytaxti Bishkek.",
    "Laos": "Janubi-Sharqiy Osiyoda, Mekong daryosi, poytaxti Vientian.",
    "Latviya": "Yevropada, Boltiqboʻyi, poytaxti Riga.",
    "Livan": "Yaqin Sharqda, Finikiya merosi, poytaxti Bayrut.",
    "Lesoto": "Janubiy Afrikada, togʻli mamlakat, poytaxti Maseru.",
    "Liberiya": "Gʻarbiy Afrikada, AQSh muhojirlari, poytaxti Monroviya.",
    "Liviya": "Shimoliy Afrikada, Saxara choʻli, poytaxti Tripoli.",
    "Lixtenshteyn": "Yevropada, kichik knyazlik, poytaxti Vaduz.",
    "Litva": "Yevropada, Boltiqboʻyi, poytaxti Vilnyus.",
    "Lyuksemburg": "Yevropada, moliyaviy markaz, poytaxti Lyuksemburg.",
    "Madagaskar": "Afrikada, lemurlar vatani, poytaxti Antananarivo.",
    "Malavi": "Sharqiy Afrikada, Malavi koʻli, poytaxti Lilongve.",
    "Malayziya": "Janubi-Sharqiy Osiyoda, Petronas minoralari, poytaxti Kuala-Lumpur.",
    "Maldiv orollari": "Hind okeanida, dam olish maskanlari, poytaxti Male.",
    "Mali": "Gʻarbiy Afrikada, Timbuktu, poytaxti Bamako.",
    "Malta": "Oʻrta yer dengizida, tarixiy qal’alar, poytaxti Valletta.",
    "Marshall orollari": "Tinch okeanida, kichik orollar, poytaxti Majuro.",
    "Mavritaniya": "Afrikada, Saxara choʻli, poytaxti Nuakshot.",
    "Mavrikiy": "Hind okeanida, koʻp madaniyatli, poytaxti Port-Lui.",
    "Meksika": "Shimoliy Amerikada, Maya xarobalari, poytaxti Mexiko Siti.",
    "Mikroneziya": "Tinch okeanida, orollar federatsiyasi, poytaxti Palikir.",
    "Moldova": "Yevropada, sharob ishlab chiqarish, poytaxti Kishinyov.",
    "Monako": "Yevropada, kazinolar, poytaxti Monako.",
    "Moʻgʻuliston": "Osiyoda, keng dashtlar, poytaxti Ulan-Bator.",
    "Chernogoriya": "Balkanda, Kotor koʻrfazi, poytaxti Podgoritsa.",
    "Marokash": "Afrikada, Atlas togʻlari, poytaxti Rabat.",
    "Mozambik": "Sharqiy Afrikada, Hind okeani sohilida, poytaxti Maputo.",
    "Myanma": "Janubi-Sharqiy Osiyoda, buddist pagodalar, poytaxti Naypyido.",
    "Namibiya": "Janubiy Afrikada, Namib choʻli, poytaxti Vindhuk.",
    "Nauru": "Tinch okeanida, kichik orol, poytaxti Yaren.",
    "Nepal": "Osiyoda, Everest choʻqqisi, poytaxti Katmandu.",
    "Niderlandiya": "Yevropada, lola va shamol tegirmonlari, poytaxti Amsterdam.",
    "Yangi Zelandiya": "Okeaniyada, Maori madaniyati, poytaxti Vellington.",
    "Nikaragua": "Markaziy Amerikada, vulqonlar, poytaxti Managua.",
    "Niger": "Afrikada, Saxara choʻli, poytaxti Niamey.",
    "Nigeriya": "Afrikada, koʻp aholiga ega, poytaxti Abuja.",
    "Shimoliy Koreya": "Osiyoda, izolyatsiya qilingan, poytaxti Pxenyan.",
    "Shimoliy Makedoniya": "Balkanda, Ohrid koʻli, poytaxti Skopye.",
    "Norvegiya": "Yevropada, fyordlar, poytaxti Oslo.",
    "Ummon": "Yaqin Sharqda, Arab yarim oroli, poytaxti Maskat.",
    "Pokiston": "Janubiy Osiyoda, Indus daryosi, poytaxti Islomobod.",
    "Palau": "Tinch okeanida, marjon riflari, poytaxti Ngerulmud.",
    "Falastin": "Yaqin Sharqda, diniy joylar, poytaxti Sharqiy Quddus.",
    "Panama": "Markaziy Amerikada, Panama kanali, poytaxti Panama Siti.",
    "Papua Yangi Gvineya": "Okeaniyada, koʻp tillar, poytaxti Port-Moresbi.",
    "Paragvay": "Janubiy Amerikada, Guarani madaniyati, poytaxti Asunsion.",
    "Peru": "Janubiy Amerikada, Machu Pikchu, poytaxti Lima.",
    "Filippin": "Janubi-Sharqiy Osiyoda, minglab orollar, poytaxti Manila.",
    "Polsha": "Yevropada, Amber yoʻli, poytaxti Varshava.",
    "Portugaliya": "Yevropada, fado musiqasi, poytaxti Lissabon.",
    "Qatar": "Fors koʻrfazida, zamonaviy arxitektura, poytaxti Doha.",
    "Ruminiya": "Yevropada, Drakula afsonasi, poytaxti Buxarest.",
    "Rossiya": "Yevropa va Osiyoda, eng katta maydon, poytaxti Moskva.",
    "Ruanda": "Sharqiy Afrikada, ming tepaliklar, poytaxti Kigali.",
    "Sent Kitts va Nevis": "Karib dengizida, kichik orollar, poytaxti Baster.",
    "Sent Lusiya": "Karib dengizida, Piton togʻlari, poytaxti Kastri.",
    "Sent Vinsent va Grenadinlar": "Karib dengizida, yelkanli sport, poytaxti Kingstaun.",
    "Samoa": "Tinch okeanida, Polineziya madaniyati, poytaxti Apia.",
    "San Marino": "Yevropada, qadimiy respublika, poytaxti San Marino.",
    "San-Tome va Prinsipi": "Afrikada, Gvineya koʻrfazi, poytaxti San-Tome.",
    "Saudiya Arabistoni": "Yaqin Sharqda, Makka va Madina, poytaxti Riyod.",
    "Senegal": "Gʻarbiy Afrikada, Dakar rallisi, poytaxti Dakar.",
    "Serbiya": "Balkanda, pravoslav cherkovlari, poytaxti Belgrad.",
    "Seyshell orollari": "Hind okeanida, plyajlar, poytaxti Viktoriya.",
    "Syerra Leone": "Gʻarbiy Afrikada, olmos konlari, poytaxti Fritaun.",
    "Singapur": "Janubi-Sharqiy Osiyoda, shahar-davlat, poytaxti Singapur.",
    "Slovakiya": "Yevropada, Karpat togʻlari, poytaxti Bratislava.",
    "Sloveniya": "Yevropada, Bled koʻli, poytaxti Lyublyana.",
    "Solomon orollari": "Tinch okeanida, urush yodgorliklari, poytaxti Honiara.",
    "Somali": "Afrika shoxida, Hind okeani, poytaxti Mogadishu.",
    "Janubiy Afrika": "Afrikada, Nelson Mandela, poytaxti Pretoriya.",
    "Janubiy Koreya": "Osiyoda, K-pop, poytaxti Seul.",
    "Janubiy Sudan": "Afrikada, eng yosh davlat, poytaxti Juba.",
    "Ispaniya": "Yevropada, flamenko, poytaxti Madrid.",
    "Shri Lanka": "Hind okeanida, choy plantatsiyalari, poytaxti Shri Jayavardenepura Kotte.",
    "Sudan": "Afrikada, Nil daryosi, poytaxti Xartum.",
    "Surinam": "Janubiy Amerikada, koʻp madaniyatli, poytaxti Paramaribo.",
    "Shvetsiya": "Yevropada, IKEA va Nobel, poytaxti Stokgolm.",
    "Shveytsariya": "Yevropada, Alp togʻlari, poytaxti Bern.",
    "Suriya": "Yaqin Sharqda, qadimiy Damashq, poytaxti Damashq.",
    "Tayvan": "Osiyoda, tungi bozorlar, poytaxti Taypey.",
    "Tojikiston": "Markaziy Osiyoda, Pamir togʻlari, poytaxti Dushanbe.",
    "Tanzaniya": "Sharqiy Afrikada, Zanzibar, poytaxti Dodoma.",
    "Tailand": "Janubi-Sharqiy Osiyoda, buddist ibodatxonalari, poytaxti Bangkok.",
    "Sharqiy Timor": "Janubi-Sharqiy Osiyoda, yosh davlat, poytaxti Dili.",
    "Togo": "Gʻarbiy Afrikada, Atlantika sohilida, poytaxti Lome.",
    "Tonga": "Tinch okeanida, Polineziya qirolligi, poytaxti Nukualofa.",
    "Trinidad va Tobago": "Karib dengizida, karnaval, poytaxti Port-of-Speyn.",
    "Tunis": "Shimoliy Afrikada, Karfagen xarobalari, poytaxti Tunis.",
    "Turkiya": "Yevropa va Osiyoda, Bosfor boʻgʻozi, poytaxti Anqara.",
    "Turkmaniston": "Markaziy Osiyoda, gaz resurslari, poytaxti Ashxobod.",
    "Tuvalu": "Tinch okeanida, kichik davlat, poytaxti Funafuti.",
    "Uganda": "Sharqiy Afrikada, Viktoriya koʻli, poytaxti Kampala.",
    "Ukraina": "Yevropada, keng dashtlar, poytaxti Kiyev.",
    "Birlashgan Arab Amirliklari": "Yaqin Sharqda, Dubay, poytaxti Abu-Dabi.",
    "Buyuk Britaniya": "Yevropada, monarxiya, poytaxti London.",
    "Amerika Qoʻshma Shtatlari": "Shimoliy Amerikada, Gollivud, poytaxti Vashington, D.C.",
    "Urugvay": "Janubiy Amerikada, futbol, poytaxti Montevideo.",
    "Oʻzbekiston": "Markaziy Osiyoda, Ipak yoʻli, poytaxti Toshkent.",
    "Vanuatu": "Tinch okeanida, vulqonlar, poytaxti Port-Vila.",
    "Vatikan": "Yevropada, Katolik cherkovi, poytaxti Vatikan Siti.",
    "Venesuela": "Janubiy Amerikada, neft resurslari, poytaxti Karakas.",
    "Vyetnam": "Janubi-Sharqiy Osiyoda, Halong koʻrfazi, poytaxti Xanoy.",
    "Yaman": "Yaqin Sharqda, qadimiy shaharlar, poytaxti Sano.",
    "Zambiya": "Janubiy Afrikada, Viktoriya sharsharasi, poytaxti Lusaka.",
    "Zimbabve": "Janubiy Afrikada, Buyuk Zimbabve, poytaxti Harare."
}

# Store assigned countries for the country game
assigned_countries: Dict[str, str] = {}

# Store pending guesses for the capital game
pending_capital_guesses: Dict[str, Dict[str, str]] = {}

# Store pending guesses for the country game (map-based)
pending_country_guesses: Dict[str, str] = {}

# Store used countries for the capital guessing game
used_countries_for_capital: Set[str] = set()

# Keyboard layouts
default_keyboard = [
    ['/getcountry', '/getcapital'],
    ['/reset', '/help']
]
guess_keyboard = [
    ['/hint', '/getcapital'],
    ['/reset', '/help']
]
default_reply_markup = ReplyKeyboardMarkup(default_keyboard, resize_keyboard=True, one_time_keyboard=False)
guess_reply_markup = ReplyKeyboardMarkup(guess_keyboard, resize_keyboard=True, one_time_keyboard=False)


async def start(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    await update.message.reply_text(
        "Davlatlar oʻyin botiga xush kelibsiz! Oʻyinni boshlash uchun quyidagi buyruqlardan foydalaning.",
        reply_markup=default_reply_markup
    )


async def get_country(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /getcountry command."""
    user_id = str(update.message.from_user.id)

    # Check if there are unassigned countries left
    available_countries = [country for country in COUNTRIES if country not in assigned_countries.values()]

    if not available_countries:
        await update.message.reply_text(
            "Boshqa davlat qolmadi! Yangi oʻyinni boshlash uchun /reset buyrugʻini ishlating.",
            reply_markup=default_reply_markup
        )
        return

    # Assign a random country
    country = random.choice(available_countries)
    assigned_countries[user_id] = country
    pending_country_guesses[user_id] = country

    # Send Web App button
    web_app = WebAppInfo(url="https://your-domain.com/map.html")  # Replace with your hosted URL
    keyboard = [[telegram.KeyboardButton("Xaritada tanlash", web_app=web_app)]]
    web_app_reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        f"Sizning davlatingiz: **{country}**! Xaritada topish uchun quyidagi tugmani bosing.",
        reply_markup=web_app_reply_markup
    )


async def get_capital(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /getcapital command."""
    user_id = str(update.message.from_user.id)

    # Cancel any existing timer for this user
    if user_id in pending_capital_guesses and 'job' in pending_capital_guesses[user_id]:
        pending_capital_guesses[user_id]['job'].schedule_removal()

    # Check if there are unused countries left for guessing
    available_countries = [country for country in COUNTRIES if country not in used_countries_for_capital]

    if not available_countries:
        await update.message.reply_text(
            "Boshqa poytaxt qolmadi! Yangi oʻyinni boshlash uchun /reset buyrugʻini ishlating.",
            reply_markup=default_reply_markup
        )
        return

    # Pick a random country
    country = random.choice(available_countries)
    used_countries_for_capital.add(country)
    capital = countries_capitals[country]

    # Set pending guess
    pending_capital_guesses[user_id] = {'country': country, 'job': None}

    # Schedule timeout
    job = context.job_queue.run_once(
        callback=timeout_capital_guess,
        when=60,
        data={'user_id': user_id, 'chat_id': update.message.chat_id, 'country': country},
        name=f"timeout_{user_id}"
    )
    pending_capital_guesses[user_id]['job'] = job

    await update.message.reply_text(
        f"Poytaxt: **{capital}**. Davlat nomini yozib taxmin qiling! (1 daqiqa vaqtingiz bor)",
        reply_markup=guess_reply_markup
    )


async def timeout_capital_guess(context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for when the capital guess time expires."""
    job_data = context.job.data
    user_id = job_data['user_id']
    chat_id = job_data['chat_id']
    country = job_data['country']

    if user_id in pending_capital_guesses:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Vaqt tugadi! Toʻgʻri javob: **{country}**. Yana oʻynash uchun /getcapital buyrugʻini ishlating.",
            reply_markup=default_reply_markup
        )
        del pending_capital_guesses[user_id]


async def hint(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /hint command."""
    user_id = str(update.message.from_user.id)

    if user_id in pending_capital_guesses:
        country = pending_capital_guesses[user_id]['country']
        hint_text = country_hints.get(country, "Bu davlat haqida maʼlumot topilmadi.")
        await update.message.reply_text(
            f"Ishora: {hint_text}",
            reply_markup=guess_reply_markup
        )
    elif user_id in pending_country_guesses:
        country = pending_country_guesses[user_id]
        hint_text = country_hints.get(country, "Bu davlat haqida maʼlumot topilmadi.")
        await update.message.reply_text(
            f"Ishora: {hint_text}",
            reply_markup=guess_reply_markup
        )
    else:
        await update.message.reply_text(
            "Faol taxmin yoʻq. /getcountry yoki /getcapital buyrugʻini ishlatib boshlang.",
            reply_markup=default_reply_markup
        )


async def handle_guess(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for text messages to guess the country for capital game."""
    user_id = str(update.message.from_user.id)
    guess = update.message.text.strip().lower()

    if user_id in pending_capital_guesses:
        correct_country = pending_capital_guesses[user_id]['country'].lower()
        if guess == correct_country:
            pending_capital_guesses[user_id]['job'].schedule_removal()
            await update.message.reply_text(
                "Toʻgʻri! Ajoyib.",
                reply_markup=default_reply_markup
            )
            del pending_capital_guesses[user_id]
        else:
            await update.message.reply_text(
                "Notoʻgʻri! Yana urinib koʻring yoki /hint buyrugʻidan foydalaning.",
                reply_markup=guess_reply_markup
            )
    else:
        await update.message.reply_text(
            "Faol poytaxt taxmini yoʻq. /getcapital buyrugʻini ishlatib boshlang.",
            reply_markup=default_reply_markup
        )


async def handle_webapp_data(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for Web App data (country selection from map)."""
    user_id = str(update.effective_user.id)
    web_app_data = update.effective_message.web_app_data.data

    try:
        selected_country = json.loads(web_app_data)['country']
    except (json.JSONDecodeError, KeyError):
        await update.message.reply_text(
            "Xatolik! Iltimos, xaritada davlatni qayta tanlang.",
            reply_markup=default_reply_markup
        )
        return

    if user_id in pending_country_guesses:
        correct_country = pending_country_guesses[user_id]
        if selected_country.lower() == correct_country.lower():
            await update.message.reply_text(
                "Toʻgʻri! Ajoyib, siz xaritada **{}**ni topdingiz.".format(correct_country),
                reply_markup=default_reply_markup
            )
            del pending_country_guesses[user_id]
        else:
            await update.message.reply_text(
                "Notoʻgʻri! Siz **{}**ni tanladingiz, lekin toʻgʻri javob **{}**. /hint buyrugʻidan foydalaning yoki qayta urinib koʻring.".format(
                    selected_country, correct_country
                ),
                reply_markup=guess_reply_markup
            )
    else:
        await update.message.reply_text(
            "Faol davlat taxmini yoʻq. /getcountry buyrugʻini ishlatib boshlang.",
            reply_markup=default_reply_markup
        )


async def reset(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /reset command to clear assigned countries and guesses."""
    for user_id in list(pending_capital_guesses.keys()):
        if 'job' in pending_capital_guesses[user_id]:
            pending_capital_guesses[user_id]['job'].schedule_removal()
    assigned_countries.clear()
    pending_capital_guesses.clear()
    pending_country_guesses.clear()
    used_countries_for_capital.clear()
    await update.message.reply_text(
        "Oʻyin qayta tiklandi! Barcha davlatlar yana mavjud.",
        reply_markup=default_reply_markup
    )


async def help_command(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /help command."""
    help_text = (
        "/start - Botni ishga tushirish\n"
        "/getcountry - Tasodifiy davlat olish va xaritada topish\n"
        "/getcapital - Tasodifiy poytaxt olish va davlatni taxmin qilish (1 daqiqa)\n"
        "/hint - Davlat yoki poytaxt taxmin qilishda yordam olish\n"
        "/reset - Oʻyinni qayta boshlash\n"
        "/help - Ushbu yordam xabarini koʻrsatish"
    )
    await update.message.reply_text(help_text, reply_markup=default_reply_markup)


def main() -> None:
    """Main function to run the Telegram bot."""
    # Replace 'YOUR_BOT_TOKEN' with your actual Telegram Bot Token
    application = Application.builder().token('8290757136:AAHum1MEwq_YR9PF3floNoNnB7tnYjM84wc').build()

    # Add handlers for commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getcountry", get_country))
    application.add_handler(CommandHandler("getcapital", get_capital))
    application.add_handler(CommandHandler("hint", hint))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CommandHandler("help", help_command))

    # Add handlers for guesses and Web App data
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))
    application.add_handler(MessageHandler(filters.WEB_APP_DATA, handle_webapp_data))

    # Start the bot
    application.run_polling(allowed_updates=telegram.Update.ALL_TYPES)


if __name__ == '__main__':
    main()