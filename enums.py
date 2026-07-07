from enum import Enum

class MediaGroups(str, Enum):
    WEBSITE =           "website"
    MAGAZINES =         "magazines"
    LITERATURE =        "literature"
    INTERPRETATION =    "interpretation"
    AUDIO_VIDEO =       "audio_video"
    EMAILS =            "emails"
    OTHER =             "other"


class ProductCodes(str, Enum):
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
    PCD = 'PCD'     # Email only
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


class MediaCategories(str, Enum):
    media_groups: dict[str, list[str]] = {
        "literature": ["CWL", "LIT", "BCC"],
        "interpretation": ["ANN", "BS", "SER", "SMT"],
        "website": ["LIT_S", "PT", "TB", "MB", "KOD", "POD", "RV"],
        "audio_video": ["AD", "KOD", "TW", "POD", "PTVID", "OTHER"],
        "magazines": ["RV", "LSS", "PT"],
        "emails": ["PN", "PCD"],
    }


class ProductStatus(str, Enum):
    PUBLISHED = "published"
    PENDING = "pending"
    UNKNOWN = "unknown"

class Languages(str, Enum):
    # Lists the ISO-639-1 code of allowed languages
    AFRIKAANS =     "af"
    DUTCH =         "nl"
    FINNISH =       "fi"
    FRENCH =        "fr"
    GERMAN =        "de"
    HEBREW =        "he"
    ITALIAN =       "it"
    PORTUGUESE =    "pt"
    SPANISH =       "es"
    
    
class CustomFields(str, Enum):
    published = "688a48647c40d0183e053280"
    crowdin_project = "694efa16d67cda3bf9fabdab"
    crowdin_file = "694ef9fdf5bf21eada294ef4"
    exclude = "69ef857e7b87bddeafa48757"


CROWDIN_PROJECT_IDS: dict[str, str] = {
    'test project (general)': '678338',
    'newses': '680076',
    'religiones': '680078',
    'archaeologyes': '680080',
    'newsfr': '680084',
    'religionfr': '680086',
    'archaeologyfr': '680088',
    'newsde': '680090',
    'religionde': '680092',
    'archaeologyde': '680094',
    'youthes': '680096',
    'test project (patrick)': '688783',
    'archaeologyaf': '693487',
    'archaeologyit': '693489',
    'archaeologynl': '693491',
    'archaeologyno': '693495',
    'archaeologyfi': '693497',
    'archaeologypt': '693499',
    'archaeologyhe': '693501',
    'youthaf': '693505',
    'youthfr': '693509',
    'youthit': '693511',
    'youthnl': '693513',
    'youthno': '693515',
    'youthfi': '693519',
    'youthpt': '693521',
    'youthhe': '693523',
    'newsaf': '693525',
    'newsit': '693527',
    'newsnl': '693529',
    'newsno': '693531',
    'newsfi': '693533',
    'newspt': '693535',
    'newshe': '693537',
    'religionaf': '693539',
    'religionit': '693541',
    'religionnl': '693545',
    'religionno': '693547',
    'religionfi': '693549',
    'religionpt': '693551',
    'religionhe': '693553',
    'youthde': '693565',
    'archaeologyhe-en': '725173',
    'fot 2025': '823618',
}
