import sqlite3
import json
import os

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Surahs data
surahs = [
    {"id": 1, "name": "الفاتحة", "name_en": "Al-Fatiha", "verses": 7, "start_page": 1, "end_page": 1},
    {"id": 2, "name": "البقرة", "name_en": "Al-Baqarah", "verses": 286, "start_page": 2, "end_page": 49},
    {"id": 3, "name": "آل عمران", "name_en": "Aal-Imran", "verses": 200, "start_page": 50, "end_page": 76},
    {"id": 4, "name": "النساء", "name_en": "An-Nisa", "verses": 176, "start_page": 77, "end_page": 106},
    {"id": 5, "name": "المائدة", "name_en": "Al-Ma'idah", "verses": 120, "start_page": 106, "end_page": 127},
    {"id": 6, "name": "الأنعام", "name_en": "Al-An'am", "verses": 165, "start_page": 128, "end_page": 150},
    {"id": 7, "name": "الأعراف", "name_en": "Al-A'raf", "verses": 206, "start_page": 151, "end_page": 176},
    {"id": 8, "name": "الأنفال", "name_en": "Al-Anfal", "verses": 75, "start_page": 177, "end_page": 186},
    {"id": 9, "name": "التوبة", "name_en": "At-Tawbah", "verses": 129, "start_page": 187, "end_page": 207},
    {"id": 10, "name": "يونس", "name_en": "Yunus", "verses": 109, "start_page": 208, "end_page": 221},
    {"id": 11, "name": "هود", "name_en": "Hud", "verses": 123, "start_page": 221, "end_page": 235},
    {"id": 12, "name": "يوسف", "name_en": "Yusuf", "verses": 111, "start_page": 235, "end_page": 248},
    {"id": 13, "name": "الرعد", "name_en": "Ar-Ra'd", "verses": 43, "start_page": 249, "end_page": 255},
    {"id": 14, "name": "إبراهيم", "name_en": "Ibrahim", "verses": 52, "start_page": 255, "end_page": 261},
    {"id": 15, "name": "الحجر", "name_en": "Al-Hijr", "verses": 99, "start_page": 262, "end_page": 267},
    {"id": 16, "name": "النحل", "name_en": "An-Nahl", "verses": 128, "start_page": 267, "end_page": 281},
    {"id": 17, "name": "الإسراء", "name_en": "Al-Isra", "verses": 111, "start_page": 282, "end_page": 293},
    {"id": 18, "name": "الكهف", "name_en": "Al-Kahf", "verses": 110, "start_page": 293, "end_page": 304},
    {"id": 19, "name": "مريم", "name_en": "Maryam", "verses": 98, "start_page": 305, "end_page": 312},
    {"id": 20, "name": "طه", "name_en": "Ta-Ha", "verses": 135, "start_page": 312, "end_page": 321},
    {"id": 21, "name": "الأنبياء", "name_en": "Al-Anbiya", "verses": 112, "start_page": 322, "end_page": 331},
    {"id": 22, "name": "الحج", "name_en": "Al-Hajj", "verses": 78, "start_page": 332, "end_page": 341},
    {"id": 23, "name": "المؤمنون", "name_en": "Al-Mu'minun", "verses": 118, "start_page": 342, "end_page": 349},
    {"id": 24, "name": "النور", "name_en": "An-Nur", "verses": 64, "start_page": 350, "end_page": 359},
    {"id": 25, "name": "الفرقان", "name_en": "Al-Furqan", "verses": 77, "start_page": 359, "end_page": 366},
    {"id": 26, "name": "الشعراء", "name_en": "Ash-Shu'ara", "verses": 227, "start_page": 367, "end_page": 376},
    {"id": 27, "name": "النمل", "name_en": "An-Naml", "verses": 93, "start_page": 377, "end_page": 385},
    {"id": 28, "name": "القصص", "name_en": "Al-Qasas", "verses": 88, "start_page": 385, "end_page": 396},
    {"id": 29, "name": "العنكبوت", "name_en": "Al-Ankabut", "verses": 69, "start_page": 396, "end_page": 404},
    {"id": 30, "name": "الروم", "name_en": "Ar-Rum", "verses": 60, "start_page": 404, "end_page": 410},
    {"id": 31, "name": "لقمان", "name_en": "Luqman", "verses": 34, "start_page": 411, "end_page": 414},
    {"id": 32, "name": "السجدة", "name_en": "As-Sajdah", "verses": 30, "start_page": 415, "end_page": 417},
    {"id": 33, "name": "الأحزاب", "name_en": "Al-Ahzab", "verses": 73, "start_page": 418, "end_page": 427},
    {"id": 34, "name": "سبأ", "name_en": "Saba", "verses": 54, "start_page": 428, "end_page": 434},
    {"id": 35, "name": "فاطر", "name_en": "Fatir", "verses": 45, "start_page": 434, "end_page": 440},
    {"id": 36, "name": "يس", "name_en": "Ya-Sin", "verses": 83, "start_page": 440, "end_page": 445},
    {"id": 37, "name": "الصافات", "name_en": "As-Saffat", "verses": 182, "start_page": 446, "end_page": 452},
    {"id": 38, "name": "ص", "name_en": "Sad", "verses": 88, "start_page": 453, "end_page": 458},
    {"id": 39, "name": "الزمر", "name_en": "Az-Zumar", "verses": 75, "start_page": 458, "end_page": 467},
    {"id": 40, "name": "غافر", "name_en": "Ghafir", "verses": 85, "start_page": 467, "end_page": 476},
    {"id": 41, "name": "فصلت", "name_en": "Fussilat", "verses": 54, "start_page": 477, "end_page": 482},
    {"id": 42, "name": "الشورى", "name_en": "Ash-Shura", "verses": 53, "start_page": 483, "end_page": 489},
    {"id": 43, "name": "الزخرف", "name_en": "Az-Zukhruf", "verses": 89, "start_page": 489, "end_page": 495},
    {"id": 44, "name": "الدخان", "name_en": "Ad-Dukhan", "verses": 59, "start_page": 496, "end_page": 498},
    {"id": 45, "name": "الجاثية", "name_en": "Al-Jathiyah", "verses": 37, "start_page": 499, "end_page": 502},
    {"id": 46, "name": "الأحقاف", "name_en": "Al-Ahqaf", "verses": 35, "start_page": 502, "end_page": 506},
    {"id": 47, "name": "محمد", "name_en": "Muhammad", "verses": 38, "start_page": 507, "end_page": 510},
    {"id": 48, "name": "الفتح", "name_en": "Al-Fath", "verses": 29, "start_page": 511, "end_page": 515},
    {"id": 49, "name": "الحجرات", "name_en": "Al-Hujurat", "verses": 18, "start_page": 515, "end_page": 517},
    {"id": 50, "name": "ق", "name_en": "Qaf", "verses": 45, "start_page": 518, "end_page": 520},
    {"id": 51, "name": "الذاريات", "name_en": "Adh-Dhariyat", "verses": 60, "start_page": 520, "end_page": 523},
    {"id": 52, "name": "الطور", "name_en": "At-Tur", "verses": 49, "start_page": 523, "end_page": 525},
    {"id": 53, "name": "النجم", "name_en": "An-Najm", "verses": 62, "start_page": 526, "end_page": 528},
    {"id": 54, "name": "القمر", "name_en": "Al-Qamar", "verses": 55, "start_page": 528, "end_page": 531},
    {"id": 55, "name": "الرحمن", "name_en": "Ar-Rahman", "verses": 78, "start_page": 531, "end_page": 534},
    {"id": 56, "name": "الواقعة", "name_en": "Al-Waqi'ah", "verses": 96, "start_page": 534, "end_page": 537},
    {"id": 57, "name": "الحديد", "name_en": "Al-Hadid", "verses": 29, "start_page": 537, "end_page": 541},
    {"id": 58, "name": "المجادلة", "name_en": "Al-Mujadilah", "verses": 22, "start_page": 542, "end_page": 545},
    {"id": 59, "name": "الحشر", "name_en": "Al-Hashr", "verses": 24, "start_page": 545, "end_page": 548},
    {"id": 60, "name": "الممتحنة", "name_en": "Al-Mumtahanah", "verses": 13, "start_page": 549, "end_page": 551},
    {"id": 61, "name": "الصف", "name_en": "As-Saff", "verses": 14, "start_page": 551, "end_page": 552},
    {"id": 62, "name": "الجمعة", "name_en": "Al-Jumu'ah", "verses": 11, "start_page": 553, "end_page": 554},
    {"id": 63, "name": "المنافقون", "name_en": "Al-Munafiqun", "verses": 11, "start_page": 554, "end_page": 555},
    {"id": 64, "name": "التغابن", "name_en": "At-Taghabun", "verses": 18, "start_page": 556, "end_page": 557},
    {"id": 65, "name": "الطلاق", "name_en": "At-Talaq", "verses": 12, "start_page": 558, "end_page": 559},
    {"id": 66, "name": "التحريم", "name_en": "At-Tahrim", "verses": 12, "start_page": 560, "end_page": 561},
    {"id": 67, "name": "الملك", "name_en": "Al-Mulk", "verses": 30, "start_page": 562, "end_page": 564},
    {"id": 68, "name": "القلم", "name_en": "Al-Qalam", "verses": 52, "start_page": 564, "end_page": 566},
    {"id": 69, "name": "الحاقة", "name_en": "Al-Haqqah", "verses": 52, "start_page": 566, "end_page": 568},
    {"id": 70, "name": "المعارج", "name_en": "Al-Ma'arij", "verses": 44, "start_page": 568, "end_page": 570},
    {"id": 71, "name": "نوح", "name_en": "Nuh", "verses": 28, "start_page": 570, "end_page": 571},
    {"id": 72, "name": "الجن", "name_en": "Al-Jinn", "verses": 28, "start_page": 572, "end_page": 573},
    {"id": 73, "name": "المزمل", "name_en": "Al-Muzzammil", "verses": 20, "start_page": 574, "end_page": 575},
    {"id": 74, "name": "المدثر", "name_en": "Al-Muddathir", "verses": 56, "start_page": 575, "end_page": 577},
    {"id": 75, "name": "القيامة", "name_en": "Al-Qiyamah", "verses": 40, "start_page": 577, "end_page": 578},
    {"id": 76, "name": "الإنسان", "name_en": "Al-Insan", "verses": 31, "start_page": 578, "end_page": 580},
    {"id": 77, "name": "المرسلات", "name_en": "Al-Mursalat", "verses": 50, "start_page": 580, "end_page": 581},
    {"id": 78, "name": "النبأ", "name_en": "An-Naba", "verses": 40, "start_page": 582, "end_page": 583},
    {"id": 79, "name": "النازعات", "name_en": "An-Nazi'at", "verses": 46, "start_page": 583, "end_page": 584},
    {"id": 80, "name": "عبس", "name_en": "Abasa", "verses": 42, "start_page": 585, "end_page": 585},
    {"id": 81, "name": "التكوير", "name_en": "At-Takwir", "verses": 29, "start_page": 586, "end_page": 586},
    {"id": 82, "name": "الإنفطار", "name_en": "Al-Infitar", "verses": 19, "start_page": 587, "end_page": 587},
    {"id": 83, "name": "المطففين", "name_en": "Al-Mutaffifin", "verses": 36, "start_page": 587, "end_page": 589},
    {"id": 84, "name": "الإنشقاق", "name_en": "Al-Inshiqaq", "verses": 25, "start_page": 589, "end_page": 589},
    {"id": 85, "name": "البروج", "name_en": "Al-Buruj", "verses": 22, "start_page": 590, "end_page": 590},
    {"id": 86, "name": "الطارق", "name_en": "At-Tariq", "verses": 17, "start_page": 591, "end_page": 591},
    {"id": 87, "name": "الأعلى", "name_en": "Al-A'la", "verses": 19, "start_page": 591, "end_page": 592},
    {"id": 88, "name": "الغاشية", "name_en": "Al-Ghashiyah", "verses": 26, "start_page": 592, "end_page": 592},
    {"id": 89, "name": "الفجر", "name_en": "Al-Fajr", "verses": 30, "start_page": 593, "end_page": 594},
    {"id": 90, "name": "البلد", "name_en": "Al-Balad", "verses": 20, "start_page": 594, "end_page": 594},
    {"id": 91, "name": "الشمس", "name_en": "Ash-Shams", "verses": 15, "start_page": 595, "end_page": 595},
    {"id": 92, "name": "الليل", "name_en": "Al-Layl", "verses": 21, "start_page": 595, "end_page": 596},
    {"id": 93, "name": "الضحى", "name_en": "Ad-Duha", "verses": 11, "start_page": 596, "end_page": 596},
    {"id": 94, "name": "الشرح", "name_en": "Ash-Sharh", "verses": 8, "start_page": 596, "end_page": 596},
    {"id": 95, "name": "التين", "name_en": "At-Tin", "verses": 8, "start_page": 597, "end_page": 597},
    {"id": 96, "name": "العلق", "name_en": "Al-Alaq", "verses": 19, "start_page": 597, "end_page": 597},
    {"id": 97, "name": "القدر", "name_en": "Al-Qadr", "verses": 5, "start_page": 598, "end_page": 598},
    {"id": 98, "name": "البينة", "name_en": "Al-Bayyinah", "verses": 8, "start_page": 598, "end_page": 599},
    {"id": 99, "name": "الزلزلة", "name_en": "Az-Zalzalah", "verses": 8, "start_page": 599, "end_page": 599},
    {"id": 100, "name": "العاديات", "name_en": "Al-Adiyat", "verses": 11, "start_page": 599, "end_page": 600},
    {"id": 101, "name": "القارعة", "name_en": "Al-Qari'ah", "verses": 11, "start_page": 600, "end_page": 600},
    {"id": 102, "name": "التكاثر", "name_en": "At-Takathur", "verses": 8, "start_page": 600, "end_page": 600},
    {"id": 103, "name": "العصر", "name_en": "Al-Asr", "verses": 3, "start_page": 601, "end_page": 601},
    {"id": 104, "name": "الهمزة", "name_en": "Al-Humazah", "verses": 9, "start_page": 601, "end_page": 601},
    {"id": 105, "name": "الفيل", "name_en": "Al-Fil", "verses": 5, "start_page": 601, "end_page": 601},
    {"id": 106, "name": "قريش", "name_en": "Quraysh", "verses": 4, "start_page": 602, "end_page": 602},
    {"id": 107, "name": "الماعون", "name_en": "Al-Ma'un", "verses": 7, "start_page": 602, "end_page": 602},
    {"id": 108, "name": "الكوثر", "name_en": "Al-Kawthar", "verses": 3, "start_page": 602, "end_page": 602},
    {"id": 109, "name": "الكافرون", "name_en": "Al-Kafirun", "verses": 6, "start_page": 603, "end_page": 603},
    {"id": 110, "name": "النصر", "name_en": "An-Nasr", "verses": 3, "start_page": 603, "end_page": 603},
    {"id": 111, "name": "المسد", "name_en": "Al-Masad", "verses": 5, "start_page": 603, "end_page": 603},
    {"id": 112, "name": "الإخلاص", "name_en": "Al-Ikhlas", "verses": 4, "start_page": 604, "end_page": 604},
    {"id": 113, "name": "الفلق", "name_en": "Al-Falaq", "verses": 5, "start_page": 604, "end_page": 604},
    {"id": 114, "name": "الناس", "name_en": "An-Nas", "verses": 6, "start_page": 604, "end_page": 604}
]

# Juz data
juz = [
    {"id": 1, "name": "الجزء الأول", "start_surah": 1, "start_verse": 1, "end_surah": 2, "end_verse": 141, "start_page": 1, "end_page": 21},
    {"id": 2, "name": "الجزء الثاني", "start_surah": 2, "start_verse": 142, "end_surah": 2, "end_verse": 252, "start_page": 22, "end_page": 41},
    {"id": 3, "name": "الجزء الثالث", "start_surah": 2, "start_verse": 253, "end_surah": 3, "end_verse": 92, "start_page": 42, "end_page": 62},
    {"id": 4, "name": "الجزء الرابع", "start_surah": 3, "start_verse": 93, "end_surah": 4, "end_verse": 23, "start_page": 63, "end_page": 82},
    {"id": 5, "name": "الجزء الخامس", "start_surah": 4, "start_verse": 24, "end_surah": 4, "end_verse": 147, "start_page": 83, "end_page": 102},
    {"id": 6, "name": "الجزء السادس", "start_surah": 4, "start_verse": 148, "end_surah": 5, "end_verse": 81, "start_page": 103, "end_page": 122},
    {"id": 7, "name": "الجزء السابع", "start_surah": 5, "start_verse": 82, "end_surah": 6, "end_verse": 110, "start_page": 123, "end_page": 142},
    {"id": 8, "name": "الجزء الثامن", "start_surah": 6, "start_verse": 111, "end_surah": 7, "end_verse": 87, "start_page": 143, "end_page": 162},
    {"id": 9, "name": "الجزء التاسع", "start_surah": 7, "start_verse": 88, "end_surah": 8, "end_verse": 40, "start_page": 163, "end_page": 182},
    {"id": 10, "name": "الجزء العاشر", "start_surah": 8, "start_verse": 41, "end_surah": 9, "end_verse": 92, "start_page": 183, "end_page": 200},
    {"id": 11, "name": "الجزء الحادي عشر", "start_surah": 9, "start_verse": 93, "end_surah": 11, "end_verse": 5, "start_page": 201, "end_page": 221},
    {"id": 12, "name": "الجزء الثاني عشر", "start_surah": 11, "start_verse": 6, "end_surah": 12, "end_verse": 52, "start_page": 222, "end_page": 242},
    {"id": 13, "name": "الجزء الثالث عشر", "start_surah": 12, "start_verse": 53, "end_surah": 14, "end_verse": 52, "start_page": 243, "end_page": 261},
    {"id": 14, "name": "الجزء الرابع عشر", "start_surah": 15, "start_verse": 1, "end_surah": 16, "end_verse": 128, "start_page": 262, "end_page": 281},
    {"id": 15, "name": "الجزء الخامس عشر", "start_surah": 17, "start_verse": 1, "end_surah": 18, "end_verse": 74, "start_page": 282, "end_page": 301},
    {"id": 16, "name": "الجزء السادس عشر", "start_surah": 18, "start_verse": 75, "end_surah": 20, "end_verse": 135, "start_page": 302, "end_page": 321},
    {"id": 17, "name": "الجزء السابع عشر", "start_surah": 21, "start_verse": 1, "end_surah": 22, "end_verse": 78, "start_page": 322, "end_page": 341},
    {"id": 18, "name": "الجزء الثامن عشر", "start_surah": 23, "start_verse": 1, "end_surah": 25, "end_verse": 20, "start_page": 342, "end_page": 361},
    {"id": 19, "name": "الجزء التاسع عشر", "start_surah": 25, "start_verse": 21, "end_surah": 27, "end_verse": 55, "start_page": 362, "end_page": 381},
    {"id": 20, "name": "الجزء العشرون", "start_surah": 27, "start_verse": 56, "end_surah": 29, "end_verse": 45, "start_page": 382, "end_page": 401},
    {"id": 21, "name": "الجزء الحادي والعشرون", "start_surah": 29, "start_verse": 46, "end_surah": 33, "end_verse": 30, "start_page": 402, "end_page": 421},
    {"id": 22, "name": "الجزء الثاني والعشرون", "start_surah": 33, "start_verse": 31, "end_surah": 36, "end_verse": 27, "start_page": 422, "end_page": 441},
    {"id": 23, "name": "الجزء الثالث والعشرون", "start_surah": 36, "start_verse": 28, "end_surah": 39, "end_verse": 31, "start_page": 442, "end_page": 461},
    {"id": 24, "name": "الجزء الرابع والعشرون", "start_surah": 39, "start_verse": 32, "end_surah": 41, "end_verse": 46, "start_page": 462, "end_page": 481},
    {"id": 25, "name": "الجزء الخامس والعشرون", "start_surah": 41, "start_verse": 47, "end_surah": 45, "end_verse": 37, "start_page": 482, "end_page": 501},
    {"id": 26, "name": "الجزء السادس والعشرون", "start_surah": 46, "start_verse": 1, "end_surah": 51, "end_verse": 30, "start_page": 502, "end_page": 521},
    {"id": 27, "name": "الجزء السابع والعشرون", "start_surah": 51, "start_verse": 31, "end_surah": 57, "end_verse": 29, "start_page": 522, "end_page": 541},
    {"id": 28, "name": "الجزء الثامن والعشرون", "start_surah": 58, "start_verse": 1, "end_surah": 66, "end_verse": 12, "start_page": 542, "end_page": 561},
    {"id": 29, "name": "الجزء التاسع والعشرون", "start_surah": 67, "start_verse": 1, "end_surah": 77, "end_verse": 50, "start_page": 562, "end_page": 581},
    {"id": 30, "name": "الجزء الثلاثون", "start_surah": 78, "start_verse": 1, "end_surah": 114, "end_verse": 6, "start_page": 582, "end_page": 604}
]

# Save to JSON files
with open('data/surahs.json', 'w', encoding='utf-8') as f:
    json.dump(surahs, f, ensure_ascii=False, indent=2)

with open('data/juz.json', 'w', encoding='utf-8') as f:
    json.dump(juz, f, ensure_ascii=False, indent=2)

# Connect to SQLite database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
DROP TABLE IF EXISTS memorization
''')

cursor.execute('''
DROP TABLE IF EXISTS surahs
''')

cursor.execute('''
DROP TABLE IF EXISTS juz
''')

# Create surahs table
cursor.execute('''
CREATE TABLE surahs (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    name_en TEXT NOT NULL,
    verses INTEGER NOT NULL,
    start_page INTEGER NOT NULL,
    end_page INTEGER NOT NULL
)
''')

# Create juz table
cursor.execute('''
CREATE TABLE juz (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    start_surah INTEGER NOT NULL,
    start_verse INTEGER NOT NULL,
    end_surah INTEGER NOT NULL,
    end_verse INTEGER NOT NULL,
    start_page INTEGER NOT NULL,
    end_page INTEGER NOT NULL
)
''')

# Create memorization table
cursor.execute('''
CREATE TABLE memorization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    surah_id INTEGER NOT NULL,
    start_verse INTEGER NOT NULL,
    end_verse INTEGER NOT NULL,
    pages INTEGER,
    rating TEXT NOT NULL,
    reciter TEXT,
    notes TEXT,
    FOREIGN KEY (surah_id,
    favorite BOOLEAN DEFAULT 0,
    start_page INTEGER,
    end_page INTEGER
) REFERENCES surahs(id)
)
''')

# Create reciters table
cursor.execute('''
DROP TABLE IF EXISTS reciters
''')

cursor.execute('''
CREATE TABLE reciters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    info TEXT
)
''')

# Insert some popular reciters
reciters = [
    ("الشيخ عبد الباسط عبد الصمد", "قارئ مصري مشهور بصوته الجميل وتلاوته الخاشعة"),
    ("الشيخ محمود خليل الحصري", "أحد أشهر قراء القرآن في العالم الإسلامي"),
    ("الشيخ محمد صديق المنشاوي", "قارئ مصري مشهور بالتجويد والأداء المميز"),
    ("الشيخ مشاري راشد العفاسي", "قارئ كويتي معروف بتلاوته العذبة"),
    ("الشيخ ماهر المعيقلي", "إمام الحرم المكي وقارئ سعودي مشهور"),
    ("الشيخ عبد الرحمن السديس", "إمام الحرم المكي المعروف"),
    ("الشيخ سعد الغامدي", "قارئ سعودي مشهور بصوته الرخيم"),
    ("الشيخ عبدالله بصفر", "قارئ سعودي مشهور"),
    ("الشيخ محمود علي البنا", "قارئ مصري من كبار القراء المصريين")
]

for reciter in reciters:
    cursor.execute('INSERT INTO reciters (name, info) VALUES (?, ?)', reciter)

# Insert data into surahs table
for surah in surahs:
    cursor.execute('''
    INSERT INTO surahs (id, name, name_en, verses, start_page, end_page)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (surah['id'], surah['name'], surah['name_en'], surah['verses'], surah['start_page'], surah['end_page']))

# Insert data into juz table
for j in juz:
    cursor.execute('''
    INSERT INTO juz (id, name, start_surah, start_verse, end_surah, end_verse, start_page, end_page)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (j['id'], j['name'], j['start_surah'], j['start_verse'], j['end_surah'], j['end_verse'], j['start_page'], j['end_page']))

# Commit changes and close connection
conn.commit()
conn.close()

print("Database initialized successfully!")