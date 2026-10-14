"""Build dictionary/lebanese_core_vocabulary.json - common Lebanese words in the forms people type.

Why: a coverage study of 2,571 real WhatsApp messages (2026-10) showed Tony had seen only 83% of
the words in a new message, and that the missing words were mostly *inflections of ordinary
verbs and nouns* ("menchuf", "batalt", "oulilo", "bayte", "sawtak"), not rare vocabulary. Those
are systematic, so they are generated here from curated stems:

  * verbs: present (b-imperfect), past, imperative, future (ra7 + bare imperfect), negative,
    with object suffixes (-ne -ak -ik -o -a -na -kon -on) and dative suffixes (-le -lak ... )
    on the most used persons
  * nouns: singular, plural, possessive suffixes (bayte, baytak, bayton ...)
  * adjectives: m / f / pl
  * function words, pronouns, question words, time words, numbers

Every entry has Arabic, English and tags. `franco[0]` is the house spelling (convention
compliant); the rest are *recognition variants* - the spellings customers really use
(ktir/kteer, 7abibi/habibi, chou/shou). They are for understanding input, not for writing.

Provenance: written by Claude (not a native speaker) from its own knowledge; marked
needs_native_review. Treat as silver until a Lebanese speaker skims it.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VOWELS = "aeiou"
PERSONS = ("ana", "enta", "ente", "huwe", "hiye", "ne7na", "ento", "henne")

# ---------------------------------------------------------------- verbs ---------------------
# (id, english, arabic, present_stem_1sg_without_b, past_3m, past_1sg, imperative_m, transitive)
# present_stem is the ana form minus the b-: "ektob" -> ana bektob. Plural/2f forms clip the last
# short vowel (ektob -> ektbo) unless the stem ends in a vowel (e7ke -> e7ko).
VERBS = [
    ("ktb", "write", "كتب", "ektob", "katab", "katabt", "ktob", True),
    ("7ke", "talk / tell", "حكى", "e7ke", "7eke", "7keet", "7ke", True),
    ("2ol", "say / tell", "قال", "2oul", "2al", "2elt", "2oul", True),
    ("shuf", "see", "شاف", "shouf", "shef", "sheft", "shouf", True),
    ("sma3", "hear / listen", "سمع", "esma3", "seme3", "sme3t", "sma3", True),
    ("3rf", "know", "عرف", "a3ref", "3eref", "3reft", "3rof", True),
    ("fhm", "understand", "فهم", "efham", "fehem", "fhemet", "fham", True),
    ("3ml", "do / make", "عمل", "a3mol", "3emel", "3melt", "3mol", True),
    ("rou7", "go", "راح", "rou7", "ra7", "re7et", "rou7", False),
    ("eje", "come", "إجا", "eje", "eja", "jeet", "ta3", False),
    ("b3at", "send", "بعت", "eb3at", "ba3at", "ba3at", "b3at", True),
    ("3ate", "give", "عطى", "a3te", "3ata", "3atet", "3ate", True),
    ("khod", "take", "أخد", "ekhod", "akhad", "akhadt", "khod", True),
    ("jib", "bring", "جاب", "jib", "jeb", "jebt", "jib", True),
    ("dfa3", "pay", "دفع", "edfa3", "dafa3", "dafa3t", "dfa3", True),
    ("shtre", "buy", "اشترى", "eshtre", "shtara", "shtaret", "shtre", True),
    ("bi3", "sell", "باع", "bi3", "be3", "be3t", "bi3", True),
    ("tlob", "order / request", "طلب", "otlob", "talab", "talabt", "tlob", True),
    ("stanna", "wait", "استنى", "stanna", "stanna", "stannet", "stanna", True),
    ("jarreb", "try", "جرب", "jarreb", "jarrab", "jarrabt", "jarreb", True),
    ("ghayyer", "change", "غير", "ghayyer", "ghayyar", "ghayyart", "ghayyer", True),
    ("salle7", "fix / repair", "صلح", "salle7", "salla7", "salla7t", "salle7", True),
    ("rakkeb", "install", "ركب", "rakkeb", "rakkab", "rakkabt", "rakkeb", True),
    ("fsol", "disconnect / unplug", "فصل", "efsol", "fasal", "fasalt", "fsol", True),
    ("wassel", "connect / deliver", "وصل", "wassel", "wassal", "wassalt", "wassel", True),
    ("wsal", "arrive", "وصل", "ousal", "wesel", "wselt", "ousal", False),
    ("fta7", "open", "فتح", "efta7", "fata7", "fata7t", "fta7", True),
    ("sakker", "close", "سكر", "sakker", "sakkar", "sakkart", "sakker", True),
    ("daww", "turn on", "ضوى", "dawwe", "dawwa", "dawwet", "dawwe", True),
    ("taffe", "turn off", "طفى", "taffe", "taffa", "taffet", "taffe", True),
    ("3abbe", "fill", "عبى", "3abbe", "3abba", "3abbet", "3abbe", True),
    ("jadded", "renew", "جدد", "jadded", "jaddad", "jaddadt", "jadded", True),
    ("sajjel", "register / record", "سجل", "sajjel", "sajjal", "sajjalt", "sajjel", True),
    ("7awwel", "transfer / switch", "حول", "7awwel", "7awwal", "7awwalt", "7awwel", True),
    ("7awel", "try / attempt", "حاول", "7awel", "7awal", "7awalt", "7awel", False),
    ("ttasal", "call (phone)", "اتصل", "ettesel", "ettasal", "ettasalt", "ettesel", False),
    ("rodd", "answer / reply", "رد", "rodd", "radd", "raddet", "rodd", False),
    ("s2al", "ask", "سأل", "es2al", "sa2al", "sa2alt", "s2al", True),
    ("jaweb", "answer", "جاوب", "jaweb", "jawab", "jawabt", "jaweb", True),
    ("sa3ed", "help", "ساعد", "sa3ed", "sa3ad", "sa3adt", "sa3ed", True),
    ("sta3mel", "use", "استعمل", "sta3mel", "sta3mal", "sta3malt", "sta3mel", True),
    ("sht8el", "work", "اشتغل", "eshteghel", "shtaghal", "shtaghalt", "shteghel", False),
    ("meshe", "work (function) / walk", "مشي", "emshe", "meshe", "msheet", "mshe", False),
    ("w2ef", "stop / stand", "وقف", "ou2af", "we2ef", "w2eft", "w2af", False),
    ("rje3", "return / come back", "رجع", "erja3", "reje3", "rje3t", "rja3", False),
    ("ndal", "stay / remain", "ضل", "dall", "dall", "dallet", "dall", False),
    ("nam", "sleep", "نام", "nem", "nem", "nemt", "nem", False),
    ("akal", "eat", "أكل", "ekol", "akal", "akalt", "kol", True),
    ("shreb", "drink", "شرب", "eshrab", "shereb", "shrebt", "shrab", True),
    ("7abb", "love / like", "حب", "7ebb", "7abb", "7abbet", "7ebb", True),
    ("bade", "want", "بدي", None, None, None, None, False),   # special: badde/baddak...
    ("fik", "can (be able)", "فيك", None, None, None, None, False),  # special: fine/fik...
    ("lezem", "must / need to", "لازم", None, None, None, None, False),
    ("3jab", "please (I like it)", "عجب", "3jab", "3ajab", "3ajabne", "3jab", False),
    ("khallas", "finish", "خلص", "khalles", "khallas", "khallast", "khalles", True),
    ("bada", "start", "بدا", "ebda", "bada", "badet", "bda", False),
    ("nse", "forget", "نسي", "ensa", "nese", "nseet", "nsa", True),
    ("tzakkar", "remember", "تذكر", "etzakkar", "tzakkar", "tzakkart", "tzakkar", True),
    ("d7ak", "laugh", "ضحك", "ed7ak", "de7ek", "d7ekt", "d7ak", False),
    ("bke", "cry", "بكى", "ebke", "beke", "bkeet", "bke", False),
    ("fakkar", "think", "فكر", "fakker", "fakkar", "fakkart", "fakker", False),
    ("7ass", "feel", "حس", "7ess", "7ass", "7asset", "7ess", False),
    ("khaf", "fear", "خاف", "khaf", "khaf", "kheft", "khaf", False),
    ("z3el", "get upset", "زعل", "ez3al", "ze3el", "z3elt", "z3al", False),
    ("fr7", "be happy", "فرح", "efra7", "fere7", "fre7t", "fra7", False),
    ("sheker", "thank", "شكر", "eshkor", "shakar", "shakart", "shkor", True),
    ("se2", "drive", "ساق", "sou2", "sa2", "se2t", "sou2", True),
    ("mshe", "walk", "مشي", "emshe", "meshe", "msheet", "mshe", False),
    ("rkod", "run", "ركض", "erkod", "rakad", "rakadt", "rkod", False),
    ("tla3", "go up / go out", "طلع", "etla3", "tele3", "tle3t", "tla3", False),
    ("nzel", "go down", "نزل", "enzal", "nezel", "nzelt", "nzal", False),
    ("fout", "enter", "فات", "fout", "fet", "fett", "fout", False),
    ("khalle", "leave / let", "خلى", "khalle", "khalla", "khallet", "khalle", True),
    ("ba3ad", "distance oneself / after", "بعد", None, None, None, None, False),
    ("7atta", "put", "حط", "7ott", "7att", "7attet", "7ott", True),
    ("shel", "remove / carry", "شال", "shil", "shel", "shelt", "shil", True),
    ("lbes", "wear", "لبس", "elbos", "lebes", "lbest", "lbos", True),
    ("8assal", "wash", "غسل", "eghsel", "ghassal", "ghassalt", "ghsel", True),
    ("nazzaf", "clean", "نظف", "nazzef", "nazzaf", "nazzaft", "nazzef", True),
    ("tbakh", "cook", "طبخ", "etbokh", "tabakh", "tabakht", "tbokh", True),
    ("2ara", "read", "قرا", "e2ra", "2ara", "2areet", "2ra", True),
    ("t3allam", "learn", "تعلم", "et3allam", "t3allam", "t3allamt", "t3allam", True),
    ("3allam", "teach", "علم", "3allem", "3allam", "3allamt", "3allem", True),
    ("sheghel", "turn on / operate", "شغل", "shaghel", "shaghal", "shaghalt", "shaghel", True),
    ("dawwar", "search / look for", "دور", "dawwer", "dawwar", "dawwart", "dawwer", False),
    ("la2a", "find", "لقى", "le2e", "la2a", "la2et", "le2e", True),
    ("dayya3", "lose", "ضيع", "dayye3", "dayya3", "dayya3t", "dayye3", True),
    ("kasar", "break", "كسر", "ekser", "kasar", "kasart", "kser", True),
    ("3alla2", "hang / get stuck", "علق", "3alle2", "3alla2", "3alla2t", "3alle2", False),
    ("n2ata3", "get cut", "انقطع", "en2ete3", "n2ata3", "n2ata3t", "n2ete3", False),
    ("rann", "ring", "رن", "renn", "rann", "rannet", "renn", False),
    ("nzal", "download", "نزل", "nazzel", "nazzal", "nazzalt", "nazzel", True),
    ("7ammal", "upload / load", "حمل", "7ammel", "7ammal", "7ammalt", "7ammel", True),
    ("2affal", "lock", "قفل", "2affel", "2affal", "2affalt", "2affel", True),
    ("akkad", "confirm", "أكد", "akked", "akkad", "akkadt", "akked", True),
    ("la8a", "cancel", "ألغى", "elghe", "lagha", "laghet", "lghe", True),
    ("2ayyam", "evaluate / rate", "قيم", "2ayyem", "2ayyam", "2ayyamt", "2ayyem", True),
    ("dakhkhal", "enter / input", "دخل", "dakhkhel", "dakhkhal", "dakhkhalt", "dakhkhel", True),
    ("tbe3", "follow / track", "تبع", "tebba3", "tabba3", "tabba3t", "tebba3", True),
    ("wa33ad", "promise", "وعد", "wa33ed", "wa33ad", "wa33adt", "wa33ed", True),
    ("2arrar", "decide", "قرر", "2arrer", "2arrar", "2arrart", "2arrer", False),
    ("ekhtar", "choose", "اختار", "ekhtar", "khtar", "khtart", "khtar", True),
    ("na22a", "pick / choose", "نقى", "na22e", "na22a", "na22et", "na22e", True),
    ("sta7a", "wake up", "صحي", "ous7a", "se7e", "s7eet", "ous7a", False),
    ("shtaka", "complain", "اشتكى", "eshtke", "shtaka", "shtakeet", "shtke", False),
    ("3addal", "adjust / edit", "عدل", "3addel", "3addal", "3addalt", "3addel", True),
    ("zabbat", "set right / work out", "زبط", "zabbet", "zabbat", "zabbatt", "zabbet", False),
    ("fasser", "explain", "فسر", "fasser", "fassar", "fassart", "fasser", True),
    ("shra7", "explain", "شرح", "eshra7", "shara7", "shara7t", "shra7", True),
    ("sa2al", "question", "سأل", "es2al", "sa2al", "sa2alt", "s2al", True),
    ("3add", "count", "عد", "3edd", "3add", "3addet", "3edd", True),
    ("7seb", "calculate / charge", "حسب", "e7seb", "7asab", "7asabt", "7seb", True),
    ("kallaf", "cost", "كلف", "kallef", "kallaf", "kallaft", "kallef", False),
    ("ghle", "be expensive", "غلي", "eghla", "ghele", "ghleet", "ghla", False),
    ("rkhes", "be cheap", "رخص", "erkhas", "rekhes", "rkhest", "rkhas", False),
    ("sefer", "travel", "سافر", "sefer", "sefar", "sefart", "sefer", False),
    ("sken", "live (reside)", "سكن", "eskon", "sakan", "sakant", "skon", False),
    ("3ash", "live", "عاش", "3ish", "3ash", "3esht", "3ish", False),
    ("met", "die", "مات", "mout", "met", "mett", "mout", False),
    ("w2a3", "fall", "وقع", "ou2a3", "we2e3", "w2e3t", "w2a3", False),
    ("t2akhar", "be late", "تأخر", "et2akhar", "t2akhar", "t2akhart", "t2akhar", False),
    ("sta3jal", "hurry", "استعجل", "esta3jel", "sta3jal", "sta3jalt", "sta3jel", False),
    ("7ader", "be ready / attend", "حضر", "e7dar", "7edir", "7dert", "7dar", False),
    ("ra22ad", "put to sleep / lay down", "رقد", "ra22ed", "ra22ad", "ra22adt", "ra22ed", True),
    ("sallem", "greet / hand over", "سلم", "sallem", "sallam", "sallamt", "sallem", True),
    ("zour", "visit", "زار", "zour", "zar", "zert", "zour", True),
    ("3azam", "invite", "عزم", "e3zom", "3azam", "3azamt", "3zom", True),
    ("dfosh", "push", "دفش", "edfosh", "dafash", "dafasht", "dfosh", True),
    ("mallaa", "fill in (form)", "ملا", "malle", "malla", "mallet", "malle", True),
    ("sawwar", "take a photo", "صور", "sawwer", "sawwar", "sawwart", "sawwer", True),
    ("f7as", "check / examine", "فحص", "ef7as", "fa7as", "fa7ast", "f7as", True),
]

OBJ_SUFFIX = {  # direct object
    "me": ("ne", "ني"), "you_m": ("ak", "ك"), "you_f": ("ik", "ك"), "him": ("o", "ه"),
    "her": ("a", "ها"), "us": ("na", "نا"), "you_pl": ("kon", "كن"), "them": ("on", "ن"),
}
DAT_SUFFIX = {  # indirect object (to me / to you ...)
    "to_me": ("le", "لي"), "to_you_m": ("lak", "لك"), "to_you_f": ("lik", "لك"), "to_him": ("lo", "لو"),
    "to_her": ("la", "لها"), "to_us": ("lna", "لنا"), "to_you_pl": ("lkon", "لكن"), "to_them": ("lon", "لن"),
}
DATIVE_VERBS = {"2ol", "7ke", "b3at", "3ate", "jib", "ktb", "shra7", "fasser", "sallem", "jaweb", "rodd"}

# ------------------------------------------------------------- nouns -----------------------
# (id, english, arabic, singular, plural)  - plural "" when not needed
NOUNS = [
    ("beit", "house", "بيت", "beit", "byout"), ("sawt", "voice / sound", "صوت", "sawt", "aswat"),
    ("ra2em", "number", "رقم", "ra2em", "ar2am"), ("telefon", "phone", "تلفون", "telefon", "telefonet"),
    ("khat", "line", "خط", "khat", "khtout"), ("wa2et", "time", "وقت", "wa2et", "aw2at"),
    ("yom", "day", "يوم", "yom", "iyyem"), ("sa3a", "hour / watch", "ساعة", "sa3a", "se3at"),
    ("shaher", "month", "شهر", "shaher", "eshhor"), ("sene", "year", "سنة", "sene", "snin"),
    ("esbou3", "week", "أسبوع", "esbou3", "asabi3"), ("sheghel", "work / job", "شغل", "sheghel", "ashghal"),
    ("meshkel", "problem", "مشكل", "meshkel", "mashekel"), ("so2al", "question", "سؤال", "so2al", "as2ile"),
    ("jaweb", "answer", "جواب", "jaweb", "ajwibe"), ("7al", "solution", "حل", "7al", "7loul"),
    ("talab", "order / request", "طلب", "talab", "talabat"), ("se3er", "price", "سعر", "se3er", "as3ar"),
    ("fatoura", "bill / invoice", "فاتورة", "fatoura", "fawatir"), ("masare", "money", "مصاري", "masare", ""),
    ("masrouf", "expense / spending", "مصروف", "masrouf", "masarif"), ("7seb", "account / bill", "حساب", "7seb", "7sebet"),
    ("dafe3", "payment", "دفعة", "daf3a", "daf3at"), ("khadme", "service", "خدمة", "khadme", "khadamet"),
    ("zboun", "customer", "زبون", "zboun", "zabayen"), ("mwazzaf", "employee", "موظف", "mwazzaf", "mwazzafin"),
    ("sherke", "company", "شركة", "sherke", "sherket"), ("far3", "branch", "فرع", "far3", "frou3"),
    ("ma7al", "shop", "محل", "ma7al", "ma7allet"), ("3enwein", "address", "عنوان", "3enwein", "3anawin"),
    ("mant2a", "area", "منطقة", "mant2a", "manate2"), ("tari2", "road / way", "طريق", "tari2", "toro2"),
    ("share3", "street", "شارع", "share3", "shawere3"), ("bineye", "building", "بناية", "bineye", "bineyet"),
    ("tabe2", "floor", "طابق", "tabe2", "tawabe2"), ("oda", "room", "أوضة", "oda", "owad"),
    ("bab", "door", "باب", "bab", "bweb"), ("shebbek", "window", "شباك", "shebbek", "shbebik"),
    ("sayyara", "car", "سيارة", "sayyara", "sayyarat"), ("rajel", "man", "رجال", "rejjel", "rjel"),
    ("mara", "woman", "مرا", "mara", "niswen"), ("walad", "boy / child", "ولد", "walad", "wled"),
    ("benet", "girl", "بنت", "benet", "banet"), ("ahl", "family / parents", "أهل", "ahl", ""),
    ("emm", "mother", "إم", "emm", ""), ("bayy", "father", "بي", "bayy", ""),
    ("khayy", "brother", "خي", "khayy", "ekhwe"), ("ekhet", "sister", "إخت", "ekhet", "khayyet"),
    ("sa7eb", "friend (m)", "صاحب", "sa7eb", "as7ab"), ("sa7be", "friend (f)", "صاحبة", "sa7be", "sa7bat"),
    ("jar", "neighbour", "جار", "jar", "jiran"), ("dektor", "doctor", "دكتور", "dektor", "dakatra"),
    ("mestashfa", "hospital", "مستشفى", "mestashfa", "mestashfayet"), ("dawa", "medicine", "دوا", "dawa", "adwiye"),
    ("akel", "food", "أكل", "akel", ""), ("mayy", "water", "مي", "mayy", ""),
    ("2ahwe", "coffee", "قهوة", "2ahwe", ""), ("shay", "tea", "شاي", "shay", ""),
    ("khebez", "bread", "خبز", "khebez", ""), ("la7me", "meat", "لحمة", "la7me", ""),
    ("fakha", "fruit", "فاكهة", "fakha", ""), ("khodra", "vegetables", "خضرا", "khodra", ""),
    ("sou2", "market", "سوق", "sou2", "aswe2"), ("matar", "airport", "مطار", "matar", ""),
    ("ba7er", "sea", "بحر", "ba7er", ""), ("jabal", "mountain", "جبل", "jabal", "jbel"),
    ("ta2es", "weather", "طقس", "ta2es", ""), ("shams", "sun", "شمس", "shams", ""),
    ("shete", "rain / winter", "شتي", "shete", ""), ("bared", "cold", "برد", "bared", ""),
    ("shob", "heat", "شوب", "shob", ""), ("kahraba", "electricity", "كهربا", "kahraba", ""),
    ("moteur", "generator", "موتور", "moteur", "moteurat"), ("internet", "internet", "إنترنت", "internet", ""),
    ("wifi", "wifi", "واي فاي", "wifi", ""), ("router", "router", "راوتر", "router", "routerat"),
    ("modem", "modem", "مودم", "modem", "modemat"), ("kebel", "cable", "كابل", "kebel", "kebelet"),
    ("dawa2", "light (indicator)", "ضو", "daw", "adwe2"), ("shashe", "screen", "شاشة", "shashe", "shashet"),
    ("jhez", "device", "جهاز", "jhez", "ajhize"), ("batariyye", "battery", "بطارية", "batariyye", "batariyyet"),
    ("chargeur", "charger", "شارجر", "charger", "chargerat"), ("bta2a", "card / SIM", "بطاقة", "bta2a", "bta2at"),
    ("ba2a", "package / plan", "باقة", "ba2a", "ba2at"), ("eshtirak", "subscription", "اشتراك", "eshtirak", "eshtirakat"),
    ("3ard", "offer", "عرض", "3ard", "3rood"), ("takhfid", "discount", "تخفيض", "takhfid", "takhfidat"),
    ("warqa", "paper / document", "ورقة", "war2a", "wra2"), ("sura", "picture", "صورة", "sura", "suwar"),
    ("file", "file", "ملف", "file", "files"), ("email", "email", "إيميل", "email", "emailet"),
    ("resale", "message", "رسالة", "resele", "rasayel"), ("mokalame", "call", "مكالمة", "mokaleme", "mokalemet"),
    ("maw3ed", "appointment", "موعد", "maw3ed", "mawa3id"), ("ejtime3", "meeting", "اجتماع", "ejtime3", "ejtime3at"),
    ("safra", "trip", "سفرة", "safra", "safrat"), ("ejeze", "holiday / leave", "إجازة", "ejeze", "ejezet"),
    ("3id", "feast / holiday", "عيد", "3id", "a3yed"), ("3ers", "wedding", "عرس", "3ers", "a3ras"),
    ("7afle", "party", "حفلة", "7afle", "7aflet"), ("ghanniyye", "song", "أغنية", "ghenniyye", "ghaneni"),
    ("mousi2a", "music", "موسيقى", "mousi2a", ""), ("film", "film", "فيلم", "film", "aflem"),
    ("le3be", "game", "لعبة", "le3be", "al3ab"), ("fari2", "team", "فريق", "fari2", "fera2"),
    ("match", "match", "مباراة", "match", "matchat"), ("kora", "ball / football", "كرة", "kora", ""),
    ("madrase", "school", "مدرسة", "madrase", "madares"), ("jem3a", "university", "جامعة", "jem3a", "jem3at"),
    ("derss", "lesson", "درس", "dars", "drous"), ("emti7an", "exam", "امتحان", "emti7an", "emti7anet"),
    ("kteb", "book", "كتاب", "kteb", "kotob"), ("2alam", "pen", "قلم", "2alam", "2lem"),
    ("tawle", "table", "طاولة", "tawle", "tawlet"), ("kerse", "chair", "كرسي", "kerse", "karese"),
    ("takhet", "bed", "تخت", "takhet", "tkhoute"), ("berrad", "fridge", "براد", "berrad", "berradat"),
    ("ghassele", "washing machine", "غسالة", "ghassele", "ghasselet"), ("mekwe", "iron", "مكوة", "mekwe", ""),
    ("teyyare", "plane", "طيارة", "teyyara", "teyyarat"), ("bosta", "bus", "بوسطة", "bosta", "bostat"),
    ("taxi", "taxi", "تاكسي", "taxi", "taxiyyet"), ("chauffeur", "driver", "شوفير", "chauffeur", "chauffeuriyye"),
    ("mashwar", "ride / errand", "مشوار", "mashwar", "mashawir"), ("tawsile", "ride / delivery", "توصيلة", "tawsile", "tawsilet"),
    ("ba3dayn", "later on", "بعدين", "ba3deen", ""), ("sabe7", "morning", "صبح", "sobo7", ""),
    ("masa", "evening", "مسا", "masa", ""), ("leil", "night", "ليل", "leil", "layele"),
    ("doher", "noon", "ضهر", "doher", ""), ("bukra", "tomorrow", "بكرا", "bukra", ""),
    ("embere7", "yesterday", "مبارح", "mbere7", ""), ("halla2", "now", "هلق", "halla2", ""),
    ("shi", "thing", "شي", "shi", "ashya"), ("kell", "every / all", "كل", "kell", ""),
    ("nes", "people", "ناس", "nes", ""), ("7ada", "someone", "حدا", "7ada", ""),
    ("kelme", "word", "كلمة", "kelme", "kelmet"), ("esem", "name", "إسم", "esem", "asema"),
    ("3omer", "age / life", "عمر", "3omer", ""), ("sa77a", "health", "صحة", "sa77a", ""),
    ("ra2y", "opinion", "رأي", "ra2y", "ara2"), ("fekra", "idea", "فكرة", "fekra", "afkar"),
    ("sabab", "reason", "سبب", "sabab", "asbab"), ("natije", "result", "نتيجة", "natije", "nateyej"),
    ("ghalat", "mistake", "غلط", "ghalat", "aghlat"), ("7a2", "right / truth", "حق", "7a2", "7ou2ou2"),
    ("dawr", "turn / role", "دور", "dawr", "adwar"), ("makan", "place", "مكان", "makan", "amekin"),
]

POSS_SUFFIX = {  # possessive on nouns
    "my": ("e", "ي"), "your_m": ("ak", "ك"), "your_f": ("ik", "ك"), "his": ("o", "ه"),
    "her": ("a", "ها"), "our": ("na", "نا"), "your_pl": ("kon", "كن"), "their": ("on", "ن"),
}

# ------------------------------------------------------------ adjectives ------------------
# (id, english, arabic, masculine)  f = +e (or +a after a), pl = +in
ADJECTIVES = [
    ("mnih", "good", "منيح", "mnih"), ("3atel", "bad / broken", "عاطل", "3atel"), ("kbir", "big", "كبير", "kbir"),
    ("zghir", "small", "زغير", "zghir"), ("jdid", "new", "جديد", "jdid"), ("2adim", "old", "قديم", "2adim"),
    ("ghale", "expensive", "غالي", "ghale"), ("rkhis", "cheap", "رخيص", "rkhis"), ("sari3", "fast", "سريع", "sari3"),
    ("bati2", "slow", "بطيء", "bati2"), ("sahel", "easy", "سهل", "sahel"), ("sa3eb", "hard / difficult", "صعب", "sa3eb"),
    ("ta3ben", "tired", "تعبان", "ta3ben"), ("mabsout", "happy", "مبسوط", "mabsout"), ("za3len", "upset", "زعلان", "za3len"),
    ("jou3an", "hungry", "جوعان", "jou3an"), ("3atshan", "thirsty", "عطشان", "3atshan"), ("marid", "sick", "مريض", "marid"),
    ("mashghoul", "busy", "مشغول", "mashghoul"), ("fade", "free (not busy) / empty", "فاضي", "fade"), ("jehez", "ready", "جاهز", "jehez"),
    ("mawjoud", "present / available", "موجود", "mawjoud"), ("msakkar", "closed", "مسكر", "msakkar"), ("maftou7", "open", "مفتوح", "maftou7"),
    ("ma2tou3", "cut off", "مقطوع", "ma2tou3"), ("mwassal", "connected", "موصل", "mwassal"), ("mkharbat", "messed up", "مخربط", "mkharbat"),
    ("mkassar", "broken", "مكسر", "mkassar"), ("ndif", "clean", "نظيف", "ndif"), ("wesekh", "dirty", "وسخ", "wesekh"),
    ("7elo", "nice / sweet", "حلو", "7elo"), ("besha3", "ugly / bad", "بشع", "besha3"), ("tawil", "long / tall", "طويل", "tawil"),
    ("2asir", "short", "قصير", "2asir"), ("3arid", "wide", "عريض", "3arid"), ("dayye2", "narrow / tight", "ضيق", "dayye2"),
    ("2arib", "near", "قريب", "2arib"), ("b3id", "far", "بعيد", "b3id"), ("sa7i7", "correct", "صحيح", "sa7i7"),
    ("ghalat_adj", "wrong", "غلط", "ghalat"), ("mohem", "important", "مهم", "mohem"), ("3ade", "normal / ordinary", "عادي", "3ade"),
    ("gharib", "strange", "غريب", "gharib"), ("mo3ayyan", "specific", "معين", "mo3ayyan"), ("akid", "sure", "أكيد", "akid"),
    ("mta2akked", "certain", "متأكد", "mta2akked"), ("mest3ed", "ready / willing", "مستعد", "mest3ed"), ("mesta3jel", "in a hurry", "مستعجل", "mesta3jel"),
    ("met2akhar", "late", "متأخر", "met2akhar"), ("bakkir", "early", "بكير", "bakkir"), ("raye2", "chill / calm", "رايق", "raye2"),
    ("3asabe", "nervous / angry", "عصبي", "3asabe"), ("lazi2", "sticky / annoying", "لزق", "lazi2"), ("latif", "kind / nice", "لطيف", "latif"),
    ("shater", "clever", "شاطر", "shater"), ("ghabe", "stupid", "غبي", "ghabe"), ("ghani", "rich", "غني", "ghani"),
    ("fa2ir", "poor", "فقير", "fa2ir"), ("kemel", "complete / full", "كامل", "kemel"), ("ne2es", "missing / incomplete", "ناقص", "ne2es"),
    ("mazboot", "right / exact", "مظبوط", "mazbout"), ("da3if", "weak", "ضعيف", "da3if"), ("2awe", "strong", "قوي", "2awe"),
    ("sekhen", "hot", "سخن", "sekhen"), ("bered", "cold", "بارد", "bered"), ("tari", "fresh", "طري", "tari"),
]

# --------------------------------------------------------- function words -----------------
# (franco house spelling, variants, arabic, english, tag)
FUNCTION = [
    ("ana", ["ane"], "أنا", "I", "pronoun"), ("enta", ["inta", "ent"], "إنت", "you (m)", "pronoun"),
    ("ente", ["inte", "ente"], "إنتي", "you (f)", "pronoun"), ("huwe", ["howe", "huwwe", "hwe"], "هو", "he", "pronoun"),
    ("hiye", ["hiyye", "hye"], "هي", "she", "pronoun"), ("ne7na", ["nehna", "na7na"], "نحنا", "we", "pronoun"),
    ("ento", ["into", "entu"], "إنتو", "you (pl)", "pronoun"), ("henne", ["hinne", "hinnen"], "هني", "they", "pronoun"),
    ("hayda", ["haida", "hayde"], "هيدا", "this (m)", "pronoun"), ("hayde", ["haidi", "haydi"], "هيدي", "this (f)", "pronoun"),
    ("hawde", ["hawdi", "haydol"], "هودي", "these", "pronoun"), ("hone", ["hon", "hawn"], "هون", "here", "place"),
    ("honik", ["hunik", "hunak"], "هونيك", "there", "place"), ("wen", ["wayn", "ween"], "وين", "where", "question"),
    ("shou", ["shu", "sho", "chou", "chu"], "شو", "what", "question"), ("lesh", ["leh", "laish", "lech"], "ليش", "why", "question"),
    ("kif", ["keef", "kif"], "كيف", "how", "question"), ("emta", ["eymta", "aymata", "imta"], "إيمتى", "when", "question"),
    ("min", ["meen", "mine"], "مين", "who", "question"), ("addesh", ["adesh", "adeh", "2addesh", "addeh"], "قديش", "how much / many", "question"),
    ("ayya", ["aya", "ayye"], "أي", "which", "question"), ("eh", ["ee", "ehh", "aywa", "aiwa"], "إي", "yes", "particle"),
    ("la2", ["la", "laa", "la2a"], "لأ", "no", "particle"), ("mesh", ["mish", "msh", "mech", "mch"], "مش", "not", "negation"),
    ("ma", ["maa"], "ما", "not (verbs)", "negation"), ("ma fi", ["mafi", "ma fee", "mafee"], "ما في", "there is not", "negation"),
    ("fi", ["fee", "fih"], "في", "there is / in", "particle"), ("3am", ["3m"], "عم", "(progressive)", "particle"),
    ("ra7", ["ra7a", "rah"], "رح", "will", "particle"), ("kent", ["kint", "kunt"], "كنت", "I was", "aux"),
    ("ken", ["kan"], "كان", "he was", "aux"), ("kenet", ["kanet", "kenit"], "كانت", "she was", "aux"),
    ("keno", ["kano"], "كانو", "they were", "aux"), ("bass", ["bas", "bs"], "بس", "but / only / enough", "particle"),
    ("w", ["we", "ou", "o"], "و", "and", "conjunction"), ("aw", ["au", "walla"], "أو", "or", "conjunction"),
    ("la2anno", ["la2eno", "la2anu", "li2anno", "lianno", "lian"], "لأنو", "because", "conjunction"),
    ("iza", ["eza", "izza"], "إذا", "if", "conjunction"), ("lamma", ["lama"], "لما", "when (time)", "conjunction"),
    ("ba3ed ma", ["ba3d ma"], "بعد ما", "after", "conjunction"), ("2abel ma", ["abel ma", "2abl ma"], "قبل ما", "before", "conjunction"),
    ("yalli", ["elli", "lli", "yali", "li"], "يلي", "which / that / who", "relative"),
    ("hek", ["heik", "hayk"], "هيك", "like this / so", "particle"), ("ktir", ["kteer", "kter", "ktyr"], "كتير", "very / a lot", "adverb"),
    ("shway", ["shwai", "shwaye", "shwayy", "chway"], "شوي", "a little", "adverb"), ("kamen", ["kaman", "kmen"], "كمان", "also", "adverb"),
    ("ba3ed", ["ba3d"], "بعد", "still / yet / after", "adverb"), ("lessa", ["lissa", "lesa"], "لسا", "still / not yet", "adverb"),
    ("deghre", ["deghri", "dighri", "dughre"], "دغري", "straight / right away", "adverb"), ("halla2", ["hala2", "halla", "hal2"], "هلق", "now", "time"),
    ("bukra", ["bokra", "boukra"], "بكرا", "tomorrow", "time"), ("mbere7", ["embere7", "mbare7", "embare7"], "مبارح", "yesterday", "time"),
    ("l yom", ["lyom", "el yom", "lyoum"], "اليوم", "today", "time"), ("ba3deen", ["ba3den", "ba3dein"], "بعدين", "later", "time"),
    ("dayman", ["dayman", "daymen"], "دايماً", "always", "adverb"), ("abadan", ["abadan"], "أبداً", "never", "adverb"),
    ("sar", ["saar"], "صار", "it happened / became", "verb"), ("sarle", ["sarli", "sar le"], "صرلي", "it has been (for me)", "verb"),
    ("badde", ["bade", "baddi", "badi", "bidde"], "بدي", "I want", "verb"), ("baddak", ["badak", "bidak"], "بدك", "you want (m)", "verb"),
    ("baddik", ["badik", "bidik"], "بدك", "you want (f)", "verb"), ("baddo", ["bado", "bido"], "بدو", "he wants", "verb"),
    ("badda", ["bada", "bida"], "بدها", "she wants", "verb"), ("badna", ["badna", "bidna"], "بدنا", "we want", "verb"),
    ("badkon", ["badkon", "bidkon", "badkoun"], "بدكن", "you (pl) want", "verb"), ("baddon", ["badon", "bidon"], "بدن", "they want", "verb"),
    ("fine", ["fini", "fiyye", "feene"], "فيني", "I can", "verb"), ("fik", ["feek"], "فيك", "you can (m)", "verb"),
    ("fike", ["fiki", "feeke"], "فيكي", "you can (f)", "verb"), ("fi", ["fih"], "فيه", "he can", "verb"),
    ("fiya", ["fiha"], "فيها", "she can", "verb"), ("fina", ["feena"], "فينا", "we can", "verb"),
    ("fikon", ["feekon"], "فيكن", "you (pl) can", "verb"), ("fiyon", ["fihon", "fion"], "فين", "they can", "verb"),
    ("lezem", ["lazem", "lazim", "lezim"], "لازم", "must / should", "modal"), ("mumken", ["momken", "mimken", "mumkin"], "ممكن", "maybe / can", "modal"),
    ("yemken", ["yimken", "yimkin"], "يمكن", "maybe", "modal"), ("3ande", ["3andi", "3ende"], "عندي", "I have", "verb"),
    ("3andak", ["3endak"], "عندك", "you have (m)", "verb"), ("3andik", ["3endik"], "عندك", "you have (f)", "verb"),
    ("3ando", ["3endo"], "عندو", "he has", "verb"), ("3anda", ["3enda"], "عندها", "she has", "verb"),
    ("3anna", ["3enna"], "عنا", "we have", "verb"), ("3andkon", ["3endkon"], "عندكن", "you (pl) have", "verb"),
    ("3andon", ["3endon"], "عندن", "they have", "verb"), ("ma3e", ["ma3i"], "معي", "with me / I have on me", "prep"),
    ("ma3ak", ["ma3ek"], "معك", "with you (m)", "prep"), ("ma3ik", ["ma3ek"], "معك", "with you (f)", "prep"),
    ("ma3o", [], "معو", "with him", "prep"), ("ma3a", [], "معها", "with her", "prep"), ("ma3na", [], "معنا", "with us", "prep"),
    ("ma3kon", [], "معكن", "with you (pl)", "prep"), ("ma3on", [], "معن", "with them", "prep"),
    ("ele", ["ili", "eli"], "إلي", "for me / mine", "prep"), ("elak", ["ilak"], "إلك", "for you (m)", "prep"),
    ("elik", ["ilik"], "إلك", "for you (f)", "prep"), ("elo", ["ilo"], "إلو", "for him", "prep"),
    ("ela", ["ila"], "إلها", "for her", "prep"), ("elna", ["ilna"], "إلنا", "for us", "prep"),
    ("elkon", ["ilkon"], "إلكن", "for you (pl)", "prep"), ("elon", ["ilon"], "إلن", "for them", "prep"),
    ("3a", ["3ala", "3al"], "على", "on / to", "prep"), ("mn", ["min", "men"], "من", "from", "prep"),
    ("la", ["li", "lal"], "لـ", "to / for", "prep"), ("b", ["bi", "bl", "bel"], "بـ", "in / with", "prep"),
    ("3an", [], "عن", "about", "prep"), ("ben", ["bayn", "been"], "بين", "between", "prep"),
    ("2eddem", ["eddem", "2ddem"], "قدام", "in front of", "prep"), ("wara", [], "ورا", "behind", "prep"),
    ("fo2", ["foo2", "fou2"], "فوق", "above", "prep"), ("ta7et", ["ta7t"], "تحت", "under", "prep"),
    ("jamb", ["7add", "7add"], "جنب", "next to", "prep"), ("jowwa", ["juwwa"], "جوا", "inside", "prep"),
    ("barra", ["bara"], "برا", "outside", "prep"), ("wa7ad", ["wa7ed", "wahad"], "واحد", "one", "number"),
    ("tnen", ["tneen", "tnein"], "تنين", "two", "number"), ("tlete", ["tleti", "tlate"], "تلاتة", "three", "number"),
    ("arb3a", ["arba3a"], "أربعة", "four", "number"), ("khamse", ["khamsi"], "خمسة", "five", "number"),
    ("sette", ["setti", "sitte"], "ستة", "six", "number"), ("sab3a", [], "سبعة", "seven", "number"),
    ("tmene", ["tmeni", "tmane"], "تمانة", "eight", "number"), ("tes3a", [], "تسعة", "nine", "number"),
    ("3ashra", ["3achra"], "عشرة", "ten", "number"), ("miyye", ["miye", "mit"], "مية", "hundred", "number"),
    ("alf", [], "ألف", "thousand", "number"), ("awwal", ["awal"], "أول", "first", "number"),
    ("tene", ["teni", "tani"], "تاني", "second / other", "number"), ("ekher", ["akher"], "آخر", "last", "number"),
    ("mar7aba", ["marhaba"], "مرحبا", "hello", "greeting"), ("ahla", ["ahlan", "ahleen", "ahlen"], "أهلا", "welcome / hi", "greeting"),
    ("kifak", ["keefak", "kifak"], "كيفك", "how are you (m)", "greeting"), ("kifik", ["keefik", "kifek"], "كيفك", "how are you (f)", "greeting"),
    ("kifkon", ["keefkon"], "كيفكن", "how are you (pl)", "greeting"), ("saba7 l kheir", ["sabah el kheir", "saba7o"], "صباح الخير", "good morning", "greeting"),
    ("masa l kheir", ["masa el kheir"], "مسا الخير", "good evening", "greeting"), ("tesba7 3a kheir", ["tesbah 3ala kheir"], "تصبح على خير", "good night", "greeting"),
    ("merci", ["merce", "mersi"], "مرسي", "thank you", "courtesy"), ("shukran", ["shoukran", "chukran"], "شكراً", "thank you", "courtesy"),
    ("3afwan", [], "عفواً", "you're welcome / sorry", "courtesy"), ("sorry", ["sory"], "سوري", "sorry", "courtesy"),
    ("ma3lesh", ["ma3lech", "ma3leish"], "معليش", "never mind / it's ok", "courtesy"), ("tfaddal", ["tfadal"], "تفضل", "please / go ahead (m)", "courtesy"),
    ("tfaddale", ["tfadali"], "تفضلي", "please / go ahead (f)", "courtesy"), ("3mol ma3rouf", ["3mol ma3rof", "a3mol ma3rouf"], "عمول معروف", "please (do me a favour)", "courtesy"),
    ("yalla", ["yala", "yallah"], "يلا", "come on / let's go", "particle"), ("khalas", ["5alas", "khlas"], "خلص", "done / enough", "particle"),
    ("tayeb", ["tayyeb", "tab", "tyb"], "طيب", "okay", "particle"), ("ok", ["okay", "oki", "okk"], "أوكي", "ok", "particle"),
    ("wallah", ["walla", "wlh"], "والله", "I swear / really", "particle"), ("inshallah", ["nshalla", "inchallah", "isa"], "إن شاء الله", "God willing", "particle"),
    ("l 7amdella", ["l7amdella", "el 7amdella", "7amdellah"], "الحمدلله", "thank God", "particle"), ("ya3ne", ["ya3ni", "y3ne", "y3ni"], "يعني", "I mean / that is", "particle"),
    ("3anjad", ["3an jad", "3njad"], "عنجد", "really / seriously", "adverb"), ("tab3an", ["tab3n"], "طبعاً", "of course", "adverb"),
    ("akid", ["akeed"], "أكيد", "sure", "adverb"), ("mazboot", ["mazbout", "mazbut"], "مظبوط", "right / correct", "adverb"),
    ("ghalat", [], "غلط", "wrong", "adverb"), ("bsor3a", ["bser3a", "b sor3a"], "بسرعة", "quickly", "adverb"),
    ("3a mahlak", ["3a mahlak"], "على مهلك", "slowly / take your time", "adverb"), ("sawa", ["sawa"], "سوا", "together", "adverb"),
    ("la 7ale", ["la7ale", "la 7ali"], "لحالي", "by myself", "adverb"), ("la 7alo", ["la7alo"], "لحالو", "by himself", "adverb"),
    ("ba3dayn", [], "بعدين", "afterwards", "time"), ("2abel", ["abel", "2abl"], "قبل", "before", "time"),
    ("ba3ed", [], "بعد", "after", "time"), ("khalas", [], "خلص", "finished", "particle"),
]

# ------------------------------------------------------------ engine -----------------------
PRES_PREFIX = {"ana": "b", "enta": "bt", "ente": "bt", "huwe": "by", "hiye": "bt", "ne7na": "mn", "ento": "bt", "henne": "by"}
FUT_PREFIX = {"ana": "", "enta": "t", "ente": "t", "huwe": "y", "hiye": "t", "ne7na": "n", "ento": "t", "henne": "y"}
PAST_SUFFIX = {"ana": "t", "enta": "t", "ente": "te", "huwe": "", "hiye": "et", "ne7na": "na", "ento": "to", "henne": "o"}


def clip(stem: str) -> str:
    """ektob -> ektb (before -e/-o endings); e7ke -> e7k; stanna -> stann."""
    if stem.endswith(("e", "a", "i")):
        return stem[:-1]
    m = re.match(r"^(.*[^aeiou])([aeiou])([^aeiou])$", stem)
    return m.group(1) + m.group(3) if m and len(stem) > 3 else stem


def present(stem: str, person: str, future: bool = False) -> str:
    pre = (FUT_PREFIX if future else PRES_PREFIX)[person]
    glue = "e" if pre and pre[-1] == stem[0] else ""
    if person in ("ente",):
        return pre + glue + clip(stem) + "e"
    if person in ("ento", "henne"):
        return pre + glue + clip(stem) + "o"
    base = stem
    # byektob / bte7ke: an initial vowel in the stem merges with the prefix (b+ektob -> bektob)
    if pre and base[0] in "ei" and pre[-1] in "ynt" and not future:
        return pre + base   # bt+ektob -> btektob, by+ektob -> byektob
    if pre == "b" and base[0] in "ei":
        return "b" + base   # b+ektob -> bektob
    out = pre + base
    # prefix colliding with the same consonant (b+bi3, t+taffe): people write an epenthetic e (bebi3, tetaffe)
    if pre and pre[-1] == base[0]:
        out = pre + "e" + base
    return out


def past(p3m: str, p1: str, person: str) -> str:
    if person in ("ana", "enta"):
        return p1
    if person == "ente":
        return p1 + "e"
    if person == "huwe":
        return p3m
    if person == "hiye":
        return (p3m[:-1] if p3m.endswith(("a", "e")) else p3m) + "et"
    core = p1[:-1] if p1.endswith("t") else p1
    if person == "ne7na":
        return core + "na"
    if person == "ento":
        return core + "to"
    return (p3m[:-1] if p3m.endswith(("a", "e")) else p3m) + "o"


def elide(form: str, min_len: int = 5) -> str:
    """Drop the short vowel before a vowel suffix: 3emel+o -> 3emlo, esem+e -> esme (not shef -> shf)."""
    if len(form) < min_len:
        return form
    return re.sub(r"^(.+[^aeiou])e([^aeiou])$", r"\1\2", form)


def with_suffix(form: str, suf: str) -> str:
    if form.endswith(("e", "a", "o", "i")) and suf[0] in "aeiou":
        return form[:-1] + suf  # 3ate + o -> 3ato ; 3ate + ak -> 3atak
    return form + suf


# recognition variants: the spellings customers actually type for the same word
VARIANT_RULES = [
    (r"ou", "u"), (r"ou", "oo"), (r"ee", "i"), (r"ei", "ay"), (r"ei", "ai"), (r"7", "h"), (r"sh", "ch"),
    (r"(?<=[a-z])e\b", "i"), (r"(?<=[a-z])e\b", "eh"), (r"2", ""), (r"2", "q"), (r"kh", "5"), (r"gh", "8"),
    (r"^mn", "men"), (r"^mn", "min"), (r"^by", "bi"), (r"^by", "bye"), (r"^bt", "bet"), (r"^bt", "bte"),
    (r"^b(?=[^aeiou])", "be"), (r"^mn(?=[^aeiou])", "mne"), (r"^y(?=[^aeiou])", "ye"), (r"^t(?=[^aeiou])", "te"),
    (r"a(?=[^aeiou]e\b)", "e"), (r"(?<=[^aeiou])e(?=[^aeiou])", "i"),
]
DOUBLE_RULES = [((r"sh", "ch"), (r"ou", "u")), ((r"7", "h"), (r"ou", "u")), ((r"sh", "ch"), (r"7", "h")),
                ((r"^mn", "men"), (r"sh", "ch")), ((r"^mn", "men"), (r"ou", "u")), ((r"(?<=[a-z])e\b", "i"), (r"7", "h")),
                ((r"(?<=[a-z])e\b", "i"), (r"sh", "ch")), ((r"^by", "bi"), (r"ou", "u")), ((r"^bt", "bet"), (r"ou", "u"))]


def _respell(word: str) -> list[str]:
    out: list[str] = []
    for pat, rep in VARIANT_RULES:
        v = re.sub(pat, rep, word)
        if v != word and v not in out:
            out.append(v)
    for (p1, r1), (p2, r2) in DOUBLE_RULES:
        v = re.sub(p2, r2, re.sub(p1, r1, word))
        if v != word and v not in out:
            out.append(v)
    return out


def variants(form: str, limit: int = 12) -> list[str]:
    """Recognition spellings of a (possibly multi-word) form, respelling each word independently."""
    words = form.split()
    out: list[str] = []
    for i, w in enumerate(words):
        for v in _respell(w):
            cand = " ".join(words[:i] + [v] + words[i + 1:])
            if cand not in out:
                out.append(cand)
            if len(out) >= limit:
                return out
    return out


def entry(eid: str, forms: list[str], arabic: str, english: str, tags: list[str]) -> dict:
    house = forms[0]
    seen, spellings = set(), []
    for f in forms + variants(house):
        if f and f not in seen:
            seen.add(f)
            spellings.append(f)
    return {"id": eid, "franco": spellings, "arabic": arabic, "english": english, "tags": tags}


def build() -> list[dict]:
    entries: list[dict] = []
    for vid, en, ar, pres, p3m, p1, imp, trans in VERBS:
        if pres is None:
            continue
        for person in PERSONS:
            entries.append(entry(f"v_{vid}_pres_{person}", [present(pres, person)], ar, f"{person}: {en} (present)", ["verb", "present"]))
            entries.append(entry(f"v_{vid}_past_{person}", [past(p3m, p1, person)], ar, f"{person}: {en} (past)", ["verb", "past"]))
            entries.append(entry(f"v_{vid}_fut_{person}", ["ra7 " + present(pres, person, future=True)], ar, f"{person}: will {en}", ["verb", "future"]))
        entries.append(entry(f"v_{vid}_neg_ana", ["ma " + present(pres, "ana")], ar, f"I do not {en}", ["verb", "negative"]))
        entries.append(entry(f"v_{vid}_sub_ana", ["badde " + present(pres, "ana", future=True)], "بدي " + ar, f"I want to {en}", ["verb", "subjunctive"]))
        entries.append(entry(f"v_{vid}_sub_huwe", ["lezem " + present(pres, "huwe", future=True)], "لازم " + ar, f"he must {en}", ["verb", "subjunctive"]))
        entries.append(entry(f"v_{vid}_sub_enta", ["fik " + present(pres, "enta", future=True)], "فيك " + ar, f"you can {en}", ["verb", "subjunctive"]))
        entries.append(entry(f"v_{vid}_prog_ana", ["3am " + present(pres, "ana")], ar, f"I am {en}-ing", ["verb", "progressive"]))
        entries.append(entry(f"v_{vid}_imp_m", [imp], ar, f"{en}! (to a man)", ["verb", "imperative"]))
        entries.append(entry(f"v_{vid}_imp_f", [clip(imp) + "e"], ar, f"{en}! (to a woman)", ["verb", "imperative"]))
        entries.append(entry(f"v_{vid}_imp_pl", [clip(imp) + "o"], ar, f"{en}! (to several)", ["verb", "imperative"]))
        if trans:
            for key, (suf, ar_suf) in OBJ_SUFFIX.items():
                for base_id, base in (("pres_ana", present(pres, "ana")), ("past_huwe", elide(p3m)), ("imp_m", imp), ("pres_huwe", present(pres, "huwe"))):
                    entries.append(entry(f"v_{vid}_{base_id}_obj_{key}", [with_suffix(base, suf)], ar + ar_suf,
                                         f"{en} + {key.replace('_', ' ')}", ["verb", "object-suffix"]))
        if vid in DATIVE_VERBS:
            for key, (suf, ar_suf) in DAT_SUFFIX.items():
                for base_id, base in (("pres_ana", present(pres, "ana")), ("past_huwe", elide(p3m)), ("imp_m", imp)):
                    entries.append(entry(f"v_{vid}_{base_id}_dat_{key}", [with_suffix(base, suf)], ar + ar_suf,
                                         f"{en} {key.replace('_', ' ')}", ["verb", "dative-suffix"]))
    for nid, en, ar, sg, pl in NOUNS:
        entries.append(entry(f"n_{nid}", [sg], ar, en, ["noun"]))
        if pl:
            entries.append(entry(f"n_{nid}_pl", [pl], ar, en + " (plural)", ["noun", "plural"]))
        stem = sg[:-1] + "t" if sg.endswith(("a", "e")) else elide(sg, 4)   # sa3a -> sa3te; esem -> esme
        for key, (suf, ar_suf) in POSS_SUFFIX.items():
            entries.append(entry(f"n_{nid}_{key}", [stem + suf], ar + ar_suf, f"{key.replace('_', ' ')} {en}", ["noun", "possessive"]))
        # people glue the article and prepositions to the noun: lfatoura, lal beit -> lalbeit, 3albeit, blbeit, mnlbeit
        art = ("el " + sg) if sg[0] in "aeiou" else ("l " + sg)
        fused = [("l", "ال", "the"), ("3al", "عال", "on the"), ("bl", "بال", "in the"), ("lal", "لل", "to the"), ("mnl", "منال", "from the")]
        for pre, ar_pre, en_pre in fused:
            glued = pre + sg if sg[0] not in "aeiou" else pre + sg   # la+l+esem -> lalesem (written as typed)
            entries.append(entry(f"n_{nid}_{pre}", [f"{pre} {sg}", glued], ar_pre + ar, f"{en_pre} {en}", ["noun", "with-article"]))
    for aid, en, ar, m in ADJECTIVES:
        if m.endswith("e"):
            f = m[:-1] + "ye"                     # ghale -> ghalye, fade -> fadye
        elif m.endswith("o"):
            f = m[:-1] + "we"                     # 7elo -> 7elwe
        else:
            f = m + ("a" if m.endswith(("3", "7", "2", "q", "t", "d", "s", "z", "kh", "gh")) else "e")
        pl = (m[:-1] if m.endswith("e") else m) + "in"
        entries.append(entry(f"a_{aid}", [m], ar, en + " (m)", ["adjective"]))
        entries.append(entry(f"a_{aid}_f", [f], ar + "ة", en + " (f)", ["adjective"]))
        entries.append(entry(f"a_{aid}_pl", [pl], ar + "ين", en + " (pl)", ["adjective", "plural"]))
        entries.append(entry(f"a_{aid}_neg", ["mesh " + m], "مش " + ar, "not " + en, ["adjective", "negative"]))
    seen_ids: set[str] = set()
    for i, (fr, var, ar, en, tag) in enumerate(FUNCTION):
        eid = "f_" + re.sub(r"[^a-z0-9]+", "_", fr).strip("_")
        if eid in seen_ids:
            eid = f"{eid}_{i}"
        seen_ids.add(eid)
        entries.append(entry(eid, [fr] + var, ar, en, ["function", tag]))
    return entries


def main() -> int:
    default = Path(__file__).resolve().parents[1] / "dictionary" / "lebanese_core_vocabulary.json"
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else default
    entries = build()
    pack = {
        "pack": "lebanese_core_vocabulary",
        "version": "1.0.0",
        "provenance": "claude-seed-v2 (generated by scripts/build_lebanese_core_pack.py)",
        "needs_native_review": True,
        "note": ("Common Lebanese verbs (all persons, tenses, object/dative suffixes), nouns (plural, "
                 "possessives), adjectives (m/f/pl) and function words, each with Arabic, English and "
                 "the spellings people actually type. franco[0] is the house spelling; the rest are "
                 "recognition variants for understanding input. Written by a non-native model: silver "
                 "until a Lebanese speaker skims it."),
        "entries": entries,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pack, ensure_ascii=False, indent=1), encoding="utf-8")
    forms = {s for e in entries for s in e["franco"]}
    words = {w for s in forms for w in s.split()}
    print(f"entries {len(entries):,} | spellings {len(forms):,} | distinct words {len(words):,} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
