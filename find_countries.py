import os
import json
import random
import logging
import sqlite3
import html as _html
from collections import defaultdict
from dotenv import load_dotenv
import telegram
from telegram import ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from typing import Dict, Set

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', '')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan. .env faylini tekshiring.")

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

COUNTRIES_SET = set(COUNTRIES)

# Maps English name (sent by map.html) → Uzbek name (used internally by the game)
MAP_EN_TO_UZ: dict = {
    "Afghanistan": "Afgʻoniston", "Albania": "Albaniya", "Algeria": "Jazoir",
    "Andorra": "Andorra", "Angola": "Angola", "Antigua and Barbuda": "Antigua va Barbuda",
    "Argentina": "Argentina", "Armenia": "Armaniston", "Australia": "Avstraliya",
    "Austria": "Avstriya", "Azerbaijan": "Ozarbayjon", "Bahamas": "Bagama orollari",
    "Bahrain": "Bahrayn", "Bangladesh": "Bangladesh", "Barbados": "Barbados",
    "Belarus": "Belarus", "Belgium": "Belgiya", "Belize": "Beliz", "Benin": "Benin",
    "Bhutan": "Butan", "Bolivia": "Boliviya", "Bosnia and Herzegovina": "Bosniya va Gertsegovina",
    "Botswana": "Botsvana", "Brazil": "Braziliya", "Brunei": "Bruney",
    "Bulgaria": "Bolgariya", "Burkina Faso": "Burkina Faso", "Burundi": "Burundi",
    "Cape Verde": "Kabo Verde", "Cambodia": "Kambodja", "Cameroon": "Kamerun",
    "Canada": "Kanada", "Central African Republic": "Markaziy Afrika Respublikasi",
    "Chad": "Chad", "Chile": "Chili", "China": "Xitoy", "Colombia": "Kolumbiya",
    "Comoros": "Komor orollari",
    "Democratic Republic of the Congo": "Kongo Demokratik Respublikasi",
    "Republic of the Congo": "Kongo Respublikasi",
    "Costa Rica": "Kosta Rika", "Croatia": "Xorvatiya", "Cuba": "Kuba",
    "Cyprus": "Qibris", "Czech Republic": "Chexiya", "Denmark": "Daniya",
    "Djibouti": "Jibuti", "Dominica": "Dominika", "Dominican Republic": "Dominikan Respublikasi",
    "Ecuador": "Ekvador", "Egypt": "Misr", "El Salvador": "Salvador",
    "Equatorial Guinea": "Ekvatorial Gvineya", "Eritrea": "Eritreya",
    "Estonia": "Estoniya", "Eswatini": "Esvatini", "Ethiopia": "Efiopiya",
    "Fiji": "Fiji", "Finland": "Finlandiya", "France": "Fransiya", "Gabon": "Gabon",
    "Gambia": "Gambiya", "Georgia": "Gruziya", "Germany": "Germaniya", "Ghana": "Gana",
    "Greece": "Gretsiya", "Grenada": "Grenada", "Guatemala": "Gvatemala",
    "Guinea": "Gvineya", "Guinea-Bissau": "Gvineya-Bisau", "Guyana": "Gayana",
    "Haiti": "Gaiti", "Honduras": "Gonduras", "Hungary": "Vengriya",
    "Iceland": "Islandiya", "India": "Hindiston", "Indonesia": "Indoneziya",
    "Iran": "Eron", "Iraq": "Iroq", "Ireland": "Irlandiya", "Israel": "Isroil",
    "Italy": "Italiya", "Jamaica": "Yamayka", "Japan": "Yaponiya",
    "Jordan": "Iordaniya", "Kazakhstan": "Qozogʻiston", "Kenya": "Keniya",
    "Kiribati": "Kiribati", "Kuwait": "Kuvayt", "Kyrgyzstan": "Qirgʻiziston",
    "Laos": "Laos", "Latvia": "Latviya", "Lebanon": "Livan", "Lesotho": "Lesoto",
    "Liberia": "Liberiya", "Libya": "Liviya", "Liechtenstein": "Lixtenshteyn",
    "Lithuania": "Litva", "Luxembourg": "Lyuksemburg", "Madagascar": "Madagaskar",
    "Malawi": "Malavi", "Malaysia": "Malayziya", "Maldives": "Maldiv orollari",
    "Mali": "Mali", "Malta": "Malta", "Marshall Islands": "Marshall orollari",
    "Mauritania": "Mavritaniya", "Mauritius": "Mavrikiy", "Mexico": "Meksika",
    "Micronesia": "Mikroneziya", "Moldova": "Moldova", "Monaco": "Monako",
    "Mongolia": "Moʻgʻuliston", "Montenegro": "Chernogoriya", "Morocco": "Marokash",
    "Mozambique": "Mozambik", "Myanmar": "Myanma", "Namibia": "Namibiya",
    "Nauru": "Nauru", "Nepal": "Nepal", "Netherlands": "Niderlandiya",
    "New Zealand": "Yangi Zelandiya", "Nicaragua": "Nikaragua", "Niger": "Niger",
    "Nigeria": "Nigeriya", "North Korea": "Shimoliy Koreya",
    "North Macedonia": "Shimoliy Makedoniya", "Norway": "Norvegiya", "Oman": "Ummon",
    "Pakistan": "Pokiston", "Palau": "Palau", "Palestine": "Falastin",
    "Panama": "Panama", "Papua New Guinea": "Papua Yangi Gvineya",
    "Paraguay": "Paragvay", "Peru": "Peru", "Philippines": "Filippin",
    "Poland": "Polsha", "Portugal": "Portugaliya", "Qatar": "Qatar",
    "Romania": "Ruminiya", "Russia": "Rossiya", "Rwanda": "Ruanda",
    "Saint Kitts and Nevis": "Sent Kitts va Nevis", "Saint Lucia": "Sent Lusiya",
    "Saint Vincent and the Grenadines": "Sent Vinsent va Grenadinlar",
    "Samoa": "Samoa", "San Marino": "San Marino",
    "Sao Tome and Principe": "San-Tome va Prinsipi", "Saudi Arabia": "Saudiya Arabistoni",
    "Senegal": "Senegal", "Serbia": "Serbiya", "Seychelles": "Seyshell orollari",
    "Sierra Leone": "Syerra Leone", "Singapore": "Singapur", "Slovakia": "Slovakiya",
    "Slovenia": "Sloveniya", "Solomon Islands": "Solomon orollari", "Somalia": "Somali",
    "South Africa": "Janubiy Afrika", "South Korea": "Janubiy Koreya",
    "South Sudan": "Janubiy Sudan", "Spain": "Ispaniya", "Sri Lanka": "Shri Lanka",
    "Sudan": "Sudan", "Suriname": "Surinam", "Sweden": "Shvetsiya",
    "Switzerland": "Shveytsariya", "Syria": "Suriya", "Taiwan": "Tayvan",
    "Tajikistan": "Tojikiston", "Tanzania": "Tanzaniya", "Thailand": "Tailand",
    "Timor-Leste": "Sharqiy Timor", "Togo": "Togo", "Tonga": "Tonga",
    "Trinidad and Tobago": "Trinidad va Tobago", "Tunisia": "Tunis",
    "Turkey": "Turkiya", "Turkmenistan": "Turkmaniston", "Tuvalu": "Tuvalu",
    "Uganda": "Uganda", "Ukraine": "Ukraina",
    "United Arab Emirates": "Birlashgan Arab Amirliklari",
    "United Kingdom": "Buyuk Britaniya", "United States": "Amerika Qoʻshma Shtatlari",
    "Uruguay": "Urugvay", "Uzbekistan": "Oʻzbekiston", "Vanuatu": "Vanuatu",
    "Vatican City": "Vatikan", "Venezuela": "Venesuela", "Vietnam": "Vyetnam",
    "Yemen": "Yaman", "Zambia": "Zambiya", "Zimbabwe": "Zimbabve",
}

countries_capitals = {
    "Afgʻoniston": "Kobul", "Albaniya": "Tirana", "Jazoir": "Jazoir",
    "Andorra": "Andorra la Vella", "Angola": "Luanda", "Antigua va Barbuda": "Sent-Jons",
    "Argentina": "Buenos-Ayres", "Armaniston": "Yerevan", "Avstraliya": "Kanberra",
    "Avstriya": "Vena", "Ozarbayjon": "Boku", "Bagama orollari": "Nassau",
    "Bahrayn": "Manama", "Bangladesh": "Dakka", "Barbados": "Bridjtaun",
    "Belarus": "Minsk", "Belgiya": "Bryussel", "Beliz": "Belmopan",
    "Benin": "Porto-Novo", "Butan": "Thimphu", "Boliviya": "Sukre",
    "Bosniya va Gertsegovina": "Sarayevo", "Botsvana": "Gaborone", "Braziliya": "Brazilia",
    "Bruney": "Bandar Seri Begavon", "Bolgariya": "Sofiya", "Burkina Faso": "Uagadugu",
    "Burundi": "Gitega", "Kabo Verde": "Praya", "Kambodja": "Pnompen",
    "Kamerun": "Yaunde", "Kanada": "Ottava", "Markaziy Afrika Respublikasi": "Bangui",
    "Chad": "Njamena", "Chili": "Santyago", "Xitoy": "Pekin",
    "Kolumbiya": "Bogota", "Komor orollari": "Moroni",
    "Kongo Demokratik Respublikasi": "Kinshasa", "Kongo Respublikasi": "Brazzavil",
    "Kosta Rika": "San-Xose", "Xorvatiya": "Zagreb", "Kuba": "Gavana",
    "Qibris": "Nikosiya", "Chexiya": "Praga", "Daniya": "Kopengagen",
    "Jibuti": "Jibuti", "Dominika": "Rozo", "Dominikan Respublikasi": "Santo-Domingo",
    "Ekvador": "Kito", "Misr": "Qohira", "Salvador": "San-Salvador",
    "Ekvatorial Gvineya": "Malabo", "Eritreya": "Asmara", "Estoniya": "Tallin",
    "Esvatini": "Mbabane", "Efiopiya": "Addis-Abeba", "Fiji": "Suva",
    "Finlandiya": "Xelsinki", "Fransiya": "Parij", "Gabon": "Librevil",
    "Gambiya": "Banjul", "Gruziya": "Tbilisi", "Germaniya": "Berlin",
    "Gana": "Akkra", "Gretsiya": "Afina", "Grenada": "Sent-Jorj",
    "Gvatemala": "Gvatemala Siti", "Gvineya": "Konakri", "Gvineya-Bisau": "Bisau",
    "Gayana": "Jorjtaun", "Gaiti": "Port-o-Prens", "Gonduras": "Tegusigalpa",
    "Vengriya": "Budapesht", "Islandiya": "Reykyavik", "Hindiston": "Yangi Dehli",
    "Indoneziya": "Jakarta", "Eron": "Tehron", "Iroq": "Bagʻdod",
    "Irlandiya": "Dublin", "Isroil": "Tel Aviv", "Italiya": "Rim",
    "Yamayka": "Kingston", "Yaponiya": "Tokio", "Iordaniya": "Ammon",
    "Qozogʻiston": "Astana", "Keniya": "Nayrobi", "Kiribati": "Tarava",
    "Kuvayt": "Kuvayt Siti", "Qirgʻiziston": "Bishkek", "Laos": "Vientian",
    "Latviya": "Riga", "Livan": "Bayrut", "Lesoto": "Maseru",
    "Liberiya": "Monroviya", "Liviya": "Tripoli", "Lixtenshteyn": "Vaduz",
    "Litva": "Vilnyus", "Lyuksemburg": "Lyuksemburg", "Madagaskar": "Antananarivo",
    "Malavi": "Lilongve", "Malayziya": "Kuala-Lumpur", "Maldiv orollari": "Male",
    "Mali": "Bamako", "Malta": "Valletta", "Marshall orollari": "Majuro",
    "Mavritaniya": "Nuakshot", "Mavrikiy": "Port-Lui", "Meksika": "Mexiko Siti",
    "Mikroneziya": "Palikir", "Moldova": "Kishinyov", "Monako": "Monako",
    "Moʻgʻuliston": "Ulan-Bator", "Chernogoriya": "Podgoritsa", "Marokash": "Rabat",
    "Mozambik": "Maputo", "Myanma": "Naypyido", "Namibiya": "Vindhuk",
    "Nauru": "Yaren", "Nepal": "Katmandu", "Niderlandiya": "Amsterdam",
    "Yangi Zelandiya": "Vellington", "Nikaragua": "Managua", "Niger": "Niamey",
    "Nigeriya": "Abuja", "Shimoliy Koreya": "Pxenyan", "Shimoliy Makedoniya": "Skopye",
    "Norvegiya": "Oslo", "Ummon": "Maskat", "Pokiston": "Islomobod",
    "Palau": "Ngerulmud", "Falastin": "Sharqiy Quddus", "Panama": "Panama Siti",
    "Papua Yangi Gvineya": "Port-Moresbi", "Paragvay": "Asunsion", "Peru": "Lima",
    "Filippin": "Manila", "Polsha": "Varshava", "Portugaliya": "Lissabon",
    "Qatar": "Doha", "Ruminiya": "Buxarest", "Rossiya": "Moskva",
    "Ruanda": "Kigali", "Sent Kitts va Nevis": "Baster", "Sent Lusiya": "Kastri",
    "Sent Vinsent va Grenadinlar": "Kingstaun", "Samoa": "Apia",
    "San Marino": "San Marino", "San-Tome va Prinsipi": "San-Tome",
    "Saudiya Arabistoni": "Riyod", "Senegal": "Dakar", "Serbiya": "Belgrad",
    "Seyshell orollari": "Viktoriya", "Syerra Leone": "Fritaun", "Singapur": "Singapur",
    "Slovakiya": "Bratislava", "Sloveniya": "Lyublyana", "Solomon orollari": "Honiara",
    "Somali": "Mogadishu", "Janubiy Afrika": "Pretoriya", "Janubiy Koreya": "Seul",
    "Janubiy Sudan": "Juba", "Ispaniya": "Madrid",
    "Shri Lanka": "Shri Jayavardenepura Kotte", "Sudan": "Xartum",
    "Surinam": "Paramaribo", "Shvetsiya": "Stokgolm", "Shveytsariya": "Bern",
    "Suriya": "Damashq", "Tayvan": "Taypey", "Tojikiston": "Dushanbe",
    "Tanzaniya": "Dodoma", "Tailand": "Bangkok", "Sharqiy Timor": "Dili",
    "Togo": "Lome", "Tonga": "Nukualofa", "Trinidad va Tobago": "Port-of-Speyn",
    "Tunis": "Tunis", "Turkiya": "Anqara", "Turkmaniston": "Ashxobod",
    "Tuvalu": "Funafuti", "Uganda": "Kampala", "Ukraina": "Kiyev",
    "Birlashgan Arab Amirliklari": "Abu-Dabi", "Buyuk Britaniya": "London",
    "Amerika Qoʻshma Shtatlari": "Vashington, D.C.", "Urugvay": "Montevideo",
    "Oʻzbekiston": "Toshkent", "Vanuatu": "Port-Vila", "Vatikan": "Vatikan Siti",
    "Venesuela": "Karakas", "Vyetnam": "Xanoy", "Yaman": "Sano",
    "Zambiya": "Lusaka", "Zimbabve": "Harare"
}

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
    "Chexiya": "Yevropada, pivo va qal'alar, poytaxti Praga.",
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
    "Gruziya": "Kavkazda, sharob an'analari, poytaxti Tbilisi.",
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
    "Malta": "Oʻrta yer dengizida, tarixiy qal'alar, poytaxti Valletta.",
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

# --- DATABASE ---
DB_PATH = 'geography_bot.db'

_SCORE_COLUMNS = {
    ('correct', 'country'): 'correct_country',
    ('wrong',   'country'): 'wrong_country',
    ('correct', 'capital'): 'correct_capital',
    ('wrong',   'capital'): 'wrong_capital',
    ('timeout', 'capital'): 'timeout_capital',
}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id      TEXT PRIMARY KEY,
                username     TEXT DEFAULT '',
                display_name TEXT DEFAULT '',
                correct_country  INTEGER DEFAULT 0,
                wrong_country    INTEGER DEFAULT 0,
                correct_capital  INTEGER DEFAULT 0,
                wrong_capital    INTEGER DEFAULT 0,
                timeout_capital  INTEGER DEFAULT 0
            )
        ''')
        # migrate: add display_name if upgrading from old schema
        try:
            conn.execute('ALTER TABLE users ADD COLUMN display_name TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass
    logger.info("Ma'lumotlar bazasi tayyor.")


def _ensure_user(conn: sqlite3.Connection, user_id: str, username: str):
    conn.execute(
        'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
        (user_id, username)
    )
    conn.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))


def record_result(user_id: str, username: str, game_type: str, result: str):
    col = _SCORE_COLUMNS.get((result, game_type))
    if col is None:
        return
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, user_id, username)
        conn.execute(f'UPDATE users SET {col} = {col} + 1 WHERE user_id = ?', (user_id,))


def set_display_name(user_id: str, username: str, display_name: str):
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, user_id, username)
        conn.execute('UPDATE users SET display_name = ? WHERE user_id = ?', (display_name, user_id))


def get_display_name(user_id: str, fallback: str) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            'SELECT display_name, username FROM users WHERE user_id = ?', (user_id,)
        ).fetchone()
    if row:
        return row[0] if row[0] else (row[1] if row[1] else fallback)
    return fallback


def get_stats(user_id: str, username: str) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, user_id, username)
        row = conn.execute(
            'SELECT correct_country, wrong_country, correct_capital, wrong_capital, timeout_capital '
            'FROM users WHERE user_id = ?', (user_id,)
        ).fetchone()
    return {
        'correct_country': row[0], 'wrong_country': row[1],
        'correct_capital': row[2], 'wrong_capital': row[3],
        'timeout_capital': row[4],
    }


def get_top_users(limit: int = 10) -> list:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            '''SELECT COALESCE(NULLIF(display_name,""), NULLIF(username,""), user_id),
                      correct_country, correct_capital,
                      correct_country + correct_capital AS total
               FROM users
               ORDER BY total DESC
               LIMIT ?''',
            (limit,)
        ).fetchall()
    return rows


# --- IN-MEMORY GAME STATE (keyed by chat_id) ---
# One active game per chat (group or private)
active_country_games: Dict[str, dict] = {}   # chat_id → {country}
active_capital_games: Dict[str, dict] = {}   # chat_id → {country, capital, job}
used_capital_countries: Dict[str, Set] = defaultdict(set)   # chat_id → set
used_country_countries: Dict[str, Set] = defaultdict(set)   # chat_id → set

# --- KEYBOARDS ---
default_keyboard = [
    ['🌍 Davlat topish', '🏙 Poytaxt topish'],
    ['🏆 Top', '📊 Statistika', '♻️ Reset', '❓ Yordam'],
]
guess_keyboard = [
    ['💡 Ishora', '🏙 Poytaxt topish'],
    ['♻️ Reset', '❓ Yordam'],
]
default_reply_markup = ReplyKeyboardMarkup(default_keyboard, resize_keyboard=True, one_time_keyboard=False)
guess_reply_markup   = ReplyKeyboardMarkup(guess_keyboard,   resize_keyboard=True, one_time_keyboard=False)


# --- HELPERS ---
def _chat_key(update: telegram.Update) -> str:
    return str(update.effective_chat.id)


def _is_group(update: telegram.Update) -> bool:
    return update.effective_chat.type in ('group', 'supergroup')


def _tg_username(update: telegram.Update) -> str:
    u = update.effective_user
    return u.username or u.first_name or str(u.id)


def _player_name(update: telegram.Update) -> str:
    """Display name from DB if registered, otherwise Telegram name."""
    return get_display_name(str(update.effective_user.id), _tg_username(update))


def _cancel_capital_job(chat_id: str):
    game = active_capital_games.get(chat_id)
    if game:
        job = game.get('job')
        if job is not None:
            try:
                job.schedule_removal()
            except Exception:
                pass


# --- COMMAND HANDLERS ---

async def start(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("/start: %s", _tg_username(update))
    await update.message.reply_text(
        "Davlatlar oʻyin botiga xush kelibsiz!\n\n"
        "Ismingizni saqlash uchun: /register Ism Familiya\n"
        "Oʻyinni boshlash uchun quyidagi buyruqlardan foydalaning.",
        reply_markup=default_reply_markup
    )


async def register(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    username = _tg_username(update)

    if not context.args:
        await update.message.reply_text(
            "Ismingizni kiriting. Masalan:\n/register Ali Valiyev",
            reply_markup=default_reply_markup
        )
        return

    display_name = ' '.join(context.args)[:50].strip()
    if not display_name:
        await update.message.reply_text("Ism boʻsh boʻlmasligi kerak.")
        return

    set_display_name(user_id, username, display_name)
    logger.info("Roʻyxat: %s → %s", user_id, display_name)
    await update.message.reply_text(
        f"✅ Siz <b>{_html.escape(display_name)}</b> sifatida roʻyxatdan oʻtdingiz!",
        parse_mode='HTML',
        reply_markup=default_reply_markup
    )


async def get_country(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_key(update)
    user_id = str(update.effective_user.id)
    username = _tg_username(update)

    _cancel_capital_job(chat_id)

    used = used_country_countries[chat_id]
    available = [c for c in COUNTRIES if c not in used]
    if not available:
        await update.message.reply_text(
            "Barcha davlatlar oʻynaldi! /reset bilan qayta boshlang.",
            reply_markup=default_reply_markup
        )
        return

    country = random.choice(available)
    used.add(country)
    hint_text = country_hints.get(country, "")
    active_country_games[chat_id] = {'country': country}

    with sqlite3.connect(DB_PATH) as _c:
        _ensure_user(_c, user_id, username)

    if _is_group(update):
        msg = (
            f"🌍 *Yangi savol!*\n\n"
            f"Ishora: _{hint_text}_\n\n"
            f"Bu qaysi davlat? Birinchi toʻgʻri javob bergan g'alaba qiladi!"
        )
    else:
        msg = (
            f"🌍 *Davlat topish oʻyini*\n\n"
            f"Ishora: _{hint_text}_\n\n"
            f"Davlat nomini yozing yoki xaritada toping!"
        )

    # Build keyboard: add map button if URL is configured
    if WEBAPP_URL and WEBAPP_URL != 'https://your-domain.com/map.html':
        map_keyboard = [
            [telegram.KeyboardButton("🗺 Xaritada topish", web_app=WebAppInfo(url=WEBAPP_URL))],
            ['💡 Ishora', '♻️ Reset'],
        ]
        reply_markup = ReplyKeyboardMarkup(map_keyboard, resize_keyboard=True, one_time_keyboard=False)
    else:
        reply_markup = guess_reply_markup

    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    logger.info("Davlat oʻyini: chat=%s → %s", chat_id, country)


async def get_capital(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_key(update)
    user_id = str(update.effective_user.id)
    username = _tg_username(update)

    _cancel_capital_job(chat_id)

    used = used_capital_countries[chat_id]
    available = [c for c in COUNTRIES if c not in used]
    if not available:
        await update.message.reply_text(
            "Barcha poytaxtlar oʻynaldi! /reset bilan qayta boshlang.",
            reply_markup=default_reply_markup
        )
        return

    country = random.choice(available)
    used.add(country)
    capital = countries_capitals[country]

    active_capital_games[chat_id] = {'country': country, 'capital': capital, 'job': None}
    with sqlite3.connect(DB_PATH) as _c:
        _ensure_user(_c, user_id, username)

    job = context.job_queue.run_once(
        callback=timeout_capital_guess,
        when=60,
        data={'chat_id': chat_id, 'country': country},
        name=f"timeout_{chat_id}"
    )
    active_capital_games[chat_id]['job'] = job

    if _is_group(update):
        msg = (
            f"🏙 *Yangi savol!*\n\n"
            f"Poytaxt: *{capital}*\n\n"
            f"Bu qaysi davlatning poytaxti? (60 soniya) Birinchi toʻgʻri javob bergan g'alaba qiladi!"
        )
    else:
        msg = (
            f"🏙 Poytaxt: *{capital}*\n\n"
            f"Davlat nomini yozing! (60 soniya)"
        )

    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=guess_reply_markup)
    logger.info("Poytaxt oʻyini: chat=%s → %s (%s)", chat_id, country, capital)


async def timeout_capital_guess(context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    chat_id = data['chat_id']
    country = data['country']

    if chat_id in active_capital_games and active_capital_games[chat_id]['country'] == country:
        del active_capital_games[chat_id]
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=f"⏰ Vaqt tugadi! Toʻgʻri javob: *{country}*.\nYana oʻynash uchun /getcapital.",
            parse_mode='Markdown',
            reply_markup=default_reply_markup
        )
        logger.info("Timeout: chat=%s — %s", chat_id, country)


async def hint(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_key(update)

    if chat_id in active_country_games:
        country = active_country_games[chat_id]['country']
        hint_text = country_hints.get(country, "Maʼlumot topilmadi.")
        await update.message.reply_text(f"💡 Ishora: _{hint_text}_", parse_mode='Markdown',
                                        reply_markup=guess_reply_markup)
    elif chat_id in active_capital_games:
        country = active_capital_games[chat_id]['country']
        hint_text = country_hints.get(country, "Maʼlumot topilmadi.")
        await update.message.reply_text(f"💡 Ishora: _{hint_text}_", parse_mode='Markdown',
                                        reply_markup=guess_reply_markup)
    else:
        await update.message.reply_text(
            "Faol oʻyin yoʻq. /getcountry yoki /getcapital bilan boshlang.",
            reply_markup=default_reply_markup
        )


async def handle_guess(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_key(update)
    user_id = str(update.effective_user.id)
    username = _tg_username(update)
    text = update.message.text.strip()

    if len(text) > 100:
        return

    # Route keyboard button presses to their command handlers
    _button_routes = {
        '🌍 davlat topish':  get_country,
        '🏙 poytaxt topish': get_capital,
        '💡 ishora':         hint,
        '🏆 top':            top,
        '📊 statistika':     stats,
        '♻️ reset':          reset,
        '❓ yordam':         help_command,
    }
    route = _button_routes.get(text.lower())
    if route:
        await route(update, context)
        return

    guess = text.lower()
    in_group = _is_group(update)

    # --- Country game ---
    if chat_id in active_country_games:
        correct = active_country_games[chat_id]['country']
        if guess == correct.lower():
            record_result(user_id, username, 'country', 'correct')
            del active_country_games[chat_id]
            name = _player_name(update)
            if in_group:
                msg = f"🎉 <b>{_html.escape(name)}</b> toʻgʻri topdi! Javob: <b>{_html.escape(correct)}</b>"
            else:
                msg = f"✅ Toʻgʻri! Ajoyib! Javob: <b>{_html.escape(correct)}</b>"
            await update.message.reply_text(msg, parse_mode='HTML', reply_markup=default_reply_markup)
            logger.info("Davlat toʻgʻri: chat=%s user=%s — %s", chat_id, user_id, correct)
        else:
            if not in_group:
                await update.message.reply_text(
                    "❌ Notoʻgʻri! Yana urinib koʻring yoki /hint.",
                    reply_markup=guess_reply_markup
                )
        return

    # --- Capital game ---
    if chat_id in active_capital_games:
        correct = active_capital_games[chat_id]['country']
        if guess == correct.lower():
            _cancel_capital_job(chat_id)
            record_result(user_id, username, 'capital', 'correct')
            del active_capital_games[chat_id]
            name = _player_name(update)
            if in_group:
                msg = f"🎉 <b>{_html.escape(name)}</b> toʻgʻri topdi! Javob: <b>{_html.escape(correct)}</b>"
            else:
                msg = f"✅ Toʻgʻri! Ajoyib!"
            await update.message.reply_text(msg, parse_mode='HTML', reply_markup=default_reply_markup)
            logger.info("Poytaxt toʻgʻri: chat=%s user=%s — %s", chat_id, user_id, correct)
        else:
            record_result(user_id, username, 'capital', 'wrong')
            if not in_group:
                await update.message.reply_text(
                    "❌ Notoʻgʻri! Yana urinib koʻring yoki /hint.",
                    reply_markup=guess_reply_markup
                )
        return

    # No active game — only respond in private chats to avoid noise in groups
    if not in_group:
        await update.message.reply_text(
            "Faol oʻyin yoʻq. /getcountry yoki /getcapital bilan boshlang.",
            reply_markup=default_reply_markup
        )


async def stats(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    username = _tg_username(update)
    name = _player_name(update)
    s = get_stats(user_id, username)

    total_country = s['correct_country'] + s['wrong_country']
    total_capital = s['correct_capital'] + s['wrong_capital'] + s['timeout_capital']
    country_pct = round(s['correct_country'] / total_country * 100) if total_country else 0
    capital_pct = round(s['correct_capital'] / total_capital * 100) if total_capital else 0

    text = (
        f"📊 <b>{_html.escape(name)} — statistika</b>\n\n"
        f"🌍 Davlat topish:\n"
        f"  ✅ {s['correct_country']}  ❌ {s['wrong_country']}  ({country_pct}%)\n\n"
        f"🏙 Poytaxt topish:\n"
        f"  ✅ {s['correct_capital']}  ❌ {s['wrong_capital']}  ⏰ {s['timeout_capital']}  ({capital_pct}%)"
    )
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=default_reply_markup)


async def top(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    rows = get_top_users(10)
    if not rows:
        await update.message.reply_text("Hali hech kim oʻynamagan.", reply_markup=default_reply_markup)
        return

    medals = ['🥇', '🥈', '🥉']
    lines = ["🏆 <b>Top oʻyinchilar</b>\n"]
    for i, (name, cc, cap, total) in enumerate(rows, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        lines.append(f"{medal} {_html.escape(str(name))} — {total} toʻgʻri (🌍{cc} 🏙{cap})")

    await update.message.reply_text('\n'.join(lines), parse_mode='HTML', reply_markup=default_reply_markup)


async def reset(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_key(update)
    _cancel_capital_job(chat_id)
    active_country_games.pop(chat_id, None)
    active_capital_games.pop(chat_id, None)
    used_capital_countries[chat_id].clear()
    used_country_countries[chat_id].clear()
    logger.info("Reset: chat=%s by %s", chat_id, _tg_username(update))
    await update.message.reply_text(
        "♻️ Oʻyin qayta tiklandi! Barcha davlatlar yana mavjud.",
        reply_markup=default_reply_markup
    )


async def help_command(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "/register Ism — ismingizni saqlash (guruh natijalari uchun)\n"
        "/getcountry — ishora asosida davlat toping\n"
        "/getcapital — poytaxt asosida davlat toping (60 soniya)\n"
        "/hint — qoʻshimcha ishora\n"
        "/stats — shaxsiy statistika\n"
        "/top — eng yaxshi oʻyinchilar\n"
        "/reset — oʻyinni qayta boshlash\n"
        "/help — yordam"
    )
    await update.message.reply_text(text, reply_markup=default_reply_markup)


def _map_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with the map WebApp button. Falls back to guess_reply_markup if WEBAPP_URL not set."""
    if not WEBAPP_URL or WEBAPP_URL == 'https://your-domain.com/map.html':
        return guess_reply_markup
    return ReplyKeyboardMarkup(
        [
            [telegram.KeyboardButton("🗺 Xaritada topish", web_app=WebAppInfo(url=WEBAPP_URL))],
            ['💡 Ishora', '♻️ Reset'],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


async def handle_webapp_data(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_key(update)
    user_id = str(update.effective_user.id)
    username = _tg_username(update)
    raw = update.effective_message.web_app_data.data

    try:
        selected_country = json.loads(raw)['country']
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("WebApp xatosi: %s — %s", user_id, e)
        # Use send_message (not reply_text) — replying to a web_app_data message
        # can prevent the keyboard from updating correctly in Telegram clients
        await context.bot.send_message(
            chat_id=int(chat_id),
            text="Xatolik! Xaritada davlatni qayta tanlang.",
            reply_markup=_map_keyboard()
        )
        return

    if chat_id not in active_country_games:
        await context.bot.send_message(
            chat_id=int(chat_id),
            text="Faol davlat oʻyini yoʻq. Davlat topish tugmasini bosing.",
            reply_markup=default_reply_markup
        )
        return

    correct = active_country_games[chat_id]['country']
    name = _player_name(update)
    in_group = _is_group(update)

    # Map sends English names; convert to Uzbek before comparing with the stored game answer
    selected_uz = MAP_EN_TO_UZ.get(selected_country, selected_country)

    if selected_uz.lower() == correct.lower():
        record_result(user_id, username, 'country', 'correct')
        del active_country_games[chat_id]
        if in_group:
            msg = f"🎉 <b>{_html.escape(name)}</b> xaritada toʻgʻri topdi! Javob: <b>{_html.escape(correct)}</b>"
        else:
            msg = f"✅ Toʻgʻri! Siz <b>{_html.escape(correct)}</b>ni xaritada topdingiz!"
        await context.bot.send_message(
            chat_id=int(chat_id), text=msg, parse_mode='HTML', reply_markup=default_reply_markup
        )
        logger.info("Xarita toʻgʻri: chat=%s user=%s — %s", chat_id, user_id, correct)
    else:
        record_result(user_id, username, 'country', 'wrong')
        msg = (f"❌ Notoʻgʻri! Siz <b>{_html.escape(selected_country)}</b>ni tanladingiz.\n"
               f"Xaritada qayta urinib koʻring yoki 💡 Ishora tugmasini bosing.")
        await context.bot.send_message(
            chat_id=int(chat_id), text=msg, parse_mode='HTML', reply_markup=_map_keyboard()
        )


def main() -> None:
    init_db()
    logger.info("Bot ishga tushmoqda...")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start",      start))
    application.add_handler(CommandHandler("register",   register))
    application.add_handler(CommandHandler("getcountry", get_country))
    application.add_handler(CommandHandler("getcapital", get_capital))
    application.add_handler(CommandHandler("hint",       hint))
    application.add_handler(CommandHandler("stats",      stats))
    application.add_handler(CommandHandler("top",        top))
    application.add_handler(CommandHandler("reset",      reset))
    application.add_handler(CommandHandler("help",       help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    application.run_polling(allowed_updates=telegram.Update.ALL_TYPES)


if __name__ == '__main__':
    main()
