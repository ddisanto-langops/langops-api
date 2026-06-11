from enum import Enum

class MediaGroupEnum(str, Enum):
    WEBSITE =           "Website"
    MAGAZINES =         "Magazines"
    LITERATURE =        "Literature"
    INTERPRETATION =    "Interpretation"
    AUDIO_VIDEO =       "Audio/Video"
    EMAILS =            "Emails"


class ProductCodeEnum(str, Enum):
    AD = 'AD'       # always audio_video
    ANN = 'ANN'     # always interpretation
    BCC = 'BCC'     # always literature
    BS = 'BS'       # always interpretation
    CWL = 'CWL'     # always literature
    KOD = 'KOD'     # if has article URL, classify as website as well as audio_video. If no article URL, classify as audio_video only.
    LIT = 'LIT'     # always literature
    LIT_S = 'LIT-S' # website only, never literature
    LSS = 'LSS'     # magazine if has edition code; else website
    LT = 'LT'       # always audio_video AND website
    MB = 'MB'       # website only
    OTHER = 'OTHER' # can be text or audio. If has duration, classify as audio_video. Else, classify as emails. 
    PCD = 'PCD'     # other only
    PN = 'PN'       # emails only
    POD = 'POD'     # always audio_video; also website if has URL
    PT = 'PT'       # magazine if has edition code; else website
    PTVID = 'PTVID' # always audio_video; also website if has URL
    RV = 'RV'       # magazine if has edition code; else website
    SER = 'SER'     # always interpretation
    SMT = 'SMT'     # always interpretation
    TB = 'TB'       # always website
    TE = 'TE'       # always website
    TW = 'TW'       # always audio_video; also website if has URL


class MediaCategoryEnum(str, Enum):
    media_groups: dict[str, list[str]] = {
        "literature": ["CWL", "LIT", "BCC"],
        "interpretation": ["ANN", "BS", "SER", "SMT"],
        "website": ["LIT-S", "PT", "TB", "MB", "KOD", "POD", "RV"],
        "audio_video": ["AD", "KOD", "TW", "POD", "PTVID", "OTHER"],
        "magazines": ["RV", "LSS", "PT"],
        "emails": ["PN", "PCD"],
    }


class SupportedLanguageEnum(str, Enum):
    AFRIKAANS =     "Afrikaans"
    DUTCH =         "Dutch"
    FINNISH =       "Finnish"
    FRENCH =        "French"
    GERMAN =        "German"
    HEBREW =        "Hebrew"
    ITALIAN =       "Italian"
    PORTUGUESE =    "Portuguese"
    SPANISH =       "Spanish"
    
    
