from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class CustomEmoji:
    name: str
    id: int
    animated: bool = False

    @property
    def mention(self) -> str:
        prefix = "a" if self.animated else ""
        return f"<{prefix}:{self.name}:{self.id}>"

    @property
    def cdn_url(self) -> str:
        extension = "gif" if self.animated else "png"
        return f"https://cdn.discordapp.com/emojis/{self.id}.{extension}"

    def __str__(self) -> str:
        return self.mention


EMOJI_37496ALERT = CustomEmoji('37496alert', 1523491165096120341, True)
EMOJI_7CLUB_BAN = CustomEmoji('7club_ban', 1523491174155943936, False)
ROSE = CustomEmoji('_rose', 1291476899557671054, True)
AUTOREACT = CustomEmoji('Autoreact', 1523491199871094818, False)
AUTOROLE = CustomEmoji('autorole', 1523491208385662986, False)
AXON_OWNER = CustomEmoji('axon_owner', 1523491216900231349, False)
BLUEDOT = CustomEmoji('BlueDot', 1523491226412777522, True)
BOTS = CustomEmoji('Bots', 1523491235816411279, False)
BROWSER = CustomEmoji('browser', 1523491245383618741, False)
COMMANDS = CustomEmoji('Commands', 1523491254229405736, False)
CROSSICON = CustomEmoji('CrossIcon', 1523491262659956896, False)
CUSTOMROLE = CustomEmoji('customrole', 1523491272369639645, False)
DC_REDCROWNESPORTS = CustomEmoji('Dc_RedCrownEsports', 1523491281622536262, False)
DELETE = CustomEmoji('delete', 1523491290153615551, False)
DENIED = CustomEmoji('Denied', 1523491299188277358, False)
DISABLED1 = CustomEmoji('disabled1', 1523491309149487276, True)
DND = CustomEmoji('dnd', 1523491317949268122, False)
ENABLED = CustomEmoji('enabled', 1523491327168348240, False)
ENABLED_160063 = CustomEmoji('enabled_', 1329022799708160063, True)
EXTRA = CustomEmoji('Extra', 1523491335485788231, False)
FILDER = CustomEmoji('filder', 1523491343953825935, False)
FILE = CustomEmoji('file', 1523491352480841838, False)
FORWARD = CustomEmoji('forward', 1523491361611845702, False)
GAMES = CustomEmoji('games', 1523491370923200624, False)
GEAR = CustomEmoji('Gear', 1523491379496484946, True)
GIFD = CustomEmoji('GIFD', 1523491395132854344, True)
GIFN = CustomEmoji('GIFN', 1523491407774486559, True)
GIVEAWAY = CustomEmoji('Giveaway', 1523491417211535522, True)
GIVEAWAY_644980 = CustomEmoji('Giveaway', 1523491417211535522, True)
GIVEAWAYS = CustomEmoji('Giveaways', 1523491430385979533, True)
GREET = CustomEmoji('greet', 1523491439030435942, False)
HEADMOD = CustomEmoji('headmod', 1523491448710889565, False)
HEART_EM = CustomEmoji('heart_em', 1523491457875578980, False)
HEERIYE = CustomEmoji('Heeriye', 1523491466498805783, False)
HOME = CustomEmoji('home', 1523491475286134838, False)
ICON_BOOSTER = CustomEmoji('icon_booster', 1523491483737522347, False)
ICON_PING = CustomEmoji('icon_ping', 1523491491954032702, False)
ICONARROWRIGHT = CustomEmoji('iconArrowRight', 1523491500569395311, False)
ICONLOAD = CustomEmoji('iconLoad', 1523491509419380876, False)
ICONS_BOT = CustomEmoji('icons_bot', 1523491518009180270, False)
ICONS_CHANNEL = CustomEmoji('icons_channel', 1523491526624280756, False)
ICONS_DISCORDBOTDEV = CustomEmoji('icons_discordbotdev', 1523491535197306970, False)
ICONS_MUSIC = CustomEmoji('icons_music', 1523491543653285918, False)
ICONS_NEXT = CustomEmoji('icons_next', 1523491552385831002, False)
ICONS_PAUSE = CustomEmoji('icons_pause', 1523491560845475840, False)
ICONS_PLUS = CustomEmoji('icons_plus', 1523491569259515935, False)
ICONS_WARNING = CustomEmoji('icons_warning', 1523491577660444794, False)
ICONSETTING = CustomEmoji('iconSetting', 1523491587080847503, False)
IDLE = CustomEmoji('idle', 1523491595935285350, False)
IGNORE = CustomEmoji('ignore', 1523491605632520212, False)
INFO = CustomEmoji('info', 1523491614238965862, False)
INVITETRACKER = CustomEmoji('InviteTracker', 1523491622652743691, False)
JIOSAAVN = CustomEmoji('jiosaavn', 1523491631448330360, False)
KING = CustomEmoji('king', 1523491641435099176, True)
LAND_YILDIZ = CustomEmoji('land_yildiz', 1523491649995669546, False)
LAND_YILDIZ_722475 = CustomEmoji('land_yildiz', 1523491649995669546, False)
LOADING = CustomEmoji('loading', 1523491659139125288, True)
LOADING_461233 = CustomEmoji('loading', 1523491659139125288, True)
LOGGING = CustomEmoji('logging', 1523491670883045499, False)
MAX__A = CustomEmoji('max__A', 1523491721072083188, True)
MENTION = CustomEmoji('mention', 1523491735794090004, True)
ML_CROSS = CustomEmoji('ml_cross', 1523491761538859060, False)
MOBILE = CustomEmoji('mobile', 1523491773467332688, False)
MOD = CustomEmoji('mod', 1523491784708063354, False)
MODERATION = CustomEmoji('Moderation', 1523491796443856898, False)
MODULE = CustomEmoji('Module', 1523491805008629866, False)
MUSIC = CustomEmoji('music', 1523491817084158102, False)
MUSIC_116319 = CustomEmoji('music', 1523491817084158102, False)
MUSICSTOP_ICONS = CustomEmoji('musicstop_icons', 1523491829448966375, False)
NEXT = CustomEmoji('next', 1523491842707030148, False)
OFFLINE = CustomEmoji('offline', 1523491876978819082, False)
OLYMPUS_CROSS = CustomEmoji('olympus_cross', 1523491890719228064, False)
OLYMPUS_NOTIFY = CustomEmoji('olympus_notify', 1523491904824545290, False)
OLYMPUS_STAFF = CustomEmoji('olympus_staff', 1523491916451418254, False)
OLYMPUS_TICK = CustomEmoji('olympus_tick', 1523491930091159633, False)
OLYMPUSARROW = CustomEmoji('olympusArrow', 1523491944192413716, False)
ONLINE = CustomEmoji('online', 1523491958897639529, False)
OWNER = CustomEmoji('owner', 1523491976488419480, True)
OWNER_433185 = CustomEmoji('owner', 1523491976488419480, True)
PC = CustomEmoji('pc', 1523491987637014649, False)
PREMIUM = CustomEmoji('premium', 1523491999251042324, True)
QUESTIONS = CustomEmoji('questions', 1523492010110226493, False)
RED_DOT = CustomEmoji('red_dot', 1523492025008263220, False)
REDHEART = CustomEmoji('RedHeart', 1523492126187454527, True)
REWIND1 = CustomEmoji('rewind1', 1523492136056651866, False)
RIVERSE_FUN = CustomEmoji('riverse_fun', 1523492144554184795, False)
SECURITY = CustomEmoji('security', 1523492153194713088, False)
SG_RD = CustomEmoji('sg_rd', 1523492162627571722, True)
SHUFFLE = CustomEmoji('shuffle', 1523492171305717911, False)
SKIP = CustomEmoji('skip', 1523492180050837614, False)
SOUNDCLOUD = CustomEmoji('SoundCloud', 1523492188573401148, False)
SQ_HEADMOD = CustomEmoji('sq_HeadMod', 1523492197263999026, False)
STAR = CustomEmoji('star', 1523492206047133846, True)
STAR_147803 = CustomEmoji('star', 1523492206047133846, True)
TICK = CustomEmoji('tick', 1523492214045540556, False)
TICK_RED = CustomEmoji('tick_red', 1523492222874419373, False)
TICKET = CustomEmoji('ticket', 1523492231284129886, False)
TIMER = CustomEmoji('timer', 1523492244538261654, True)
U_ADMIN = CustomEmoji('U_admin', 1523492253199499415, False)
UPTIME = CustomEmoji('Uptime', 1523492265299939338, True)
USER = CustomEmoji('user', 1523492273625763962, False)
UTILITY = CustomEmoji('Utility', 1523492282047791255, False)
VANITYROLES = CustomEmoji('VanityRoles', 1523492290713227345, False)
VOICE = CustomEmoji('voice', 1523492298783199335, False)
VOICE_003466 = CustomEmoji('voice', 1523492298783199335, False)
WARNING = CustomEmoji('Warning', 1523492312116887566, True)
WARNINGICON = CustomEmoji('WarningIcon', 1523492320731992134, False)
YOUTUBE = CustomEmoji('youtube', 1523492329317466234, False)
YOUTUBE_570841 = CustomEmoji('youtube', 1523492329317466234, False)
ZTICK = CustomEmoji('Ztick', 1523492337999679612, False)


EMOJIS: dict[str, CustomEmoji] = {
    '37496alert': EMOJI_37496ALERT,
    '7club_ban': EMOJI_7CLUB_BAN,
    '_rose': ROSE,
    'Autoreact': AUTOREACT,
    'autorole': AUTOROLE,
    'axon_owner': AXON_OWNER,
    'BlueDot': BLUEDOT,
    'Bots': BOTS,
    'browser': BROWSER,
    'Commands': COMMANDS,
    'CrossIcon': CROSSICON,
    'customrole': CUSTOMROLE,
    'Dc_RedCrownEsports': DC_REDCROWNESPORTS,
    'delete': DELETE,
    'Denied': DENIED,
    'disabled1': DISABLED1,
    'dnd': DND,
    'enabled': ENABLED,
    'enabled_': ENABLED_160063,
    'Extra': EXTRA,
    'filder': FILDER,
    'file': FILE,
    'forward': FORWARD,
    'games': GAMES,
    'Gear': GEAR,
    'GIFD': GIFD,
    'GIFN': GIFN,
    'Giveaway': GIVEAWAY,
    'giveaway': GIVEAWAY_644980,
    'Giveaways': GIVEAWAYS,
    'greet': GREET,
    'headmod': HEADMOD,
    'heart_em': HEART_EM,
    'Heeriye': HEERIYE,
    'home': HOME,
    'icon_booster': ICON_BOOSTER,
    'icon_ping': ICON_PING,
    'iconArrowRight': ICONARROWRIGHT,
    'iconLoad': ICONLOAD,
    'icons_bot': ICONS_BOT,
    'icons_channel': ICONS_CHANNEL,
    'icons_discordbotdev': ICONS_DISCORDBOTDEV,
    'icons_music': ICONS_MUSIC,
    'icons_next': ICONS_NEXT,
    'icons_pause': ICONS_PAUSE,
    'icons_plus': ICONS_PLUS,
    'icons_warning': ICONS_WARNING,
    'iconSetting': ICONSETTING,
    'idle': IDLE,
    'ignore': IGNORE,
    'info': INFO,
    'InviteTracker': INVITETRACKER,
    'jiosaavn': JIOSAAVN,
    'king': KING,
    'land_yildiz': LAND_YILDIZ,
    'land_yildiz': LAND_YILDIZ_722475,
    'loading': LOADING,
    'Loading': LOADING_461233,
    'logging': LOGGING,
    'max__A': MAX__A,
    'mention': MENTION,
    'ml_cross': ML_CROSS,
    'mobile': MOBILE,
    'mod': MOD,
    'Moderation': MODERATION,
    'Module': MODULE,
    'music': MUSIC,
    'music': MUSIC_116319,
    'musicstop_icons': MUSICSTOP_ICONS,
    'next': NEXT,
    'offline': OFFLINE,
    'olympus_cross': OLYMPUS_CROSS,
    'olympus_notify': OLYMPUS_NOTIFY,
    'olympus_staff': OLYMPUS_STAFF,
    'olympus_tick': OLYMPUS_TICK,
    'olympusArrow': OLYMPUSARROW,
    'online': ONLINE,
    'owner': OWNER,
    'owner': OWNER_433185,
    'pc': PC,
    'premium': PREMIUM,
    'questions': QUESTIONS,
    'red_dot': RED_DOT,
    'RedHeart': REDHEART,
    'rewind1': REWIND1,
    'riverse_fun': RIVERSE_FUN,
    'security': SECURITY,
    'sg_rd': SG_RD,
    'shuffle': SHUFFLE,
    'skip': SKIP,
    'SoundCloud': SOUNDCLOUD,
    'sq_HeadMod': SQ_HEADMOD,
    'star': STAR,
    'Star': STAR_147803,
    'tick': TICK,
    'tick_red': TICK_RED,
    'ticket': TICKET,
    'timer': TIMER,
    'U_admin': U_ADMIN,
    'Uptime': UPTIME,
    'user': USER,
    'Utility': UTILITY,
    'VanityRoles': VANITYROLES,
    'voice': VOICE,
    'voice': VOICE_003466,
    'Warning': WARNING,
    'WarningIcon': WARNINGICON,
    'youtube': YOUTUBE,
    'YouTube': YOUTUBE_570841,
    'Ztick': ZTICK,
}

EMOJIS_BY_ID: dict[int, CustomEmoji] = {
    1273959128490049556: EMOJI_37496ALERT,
    1274766732786925750: EMOJI_7CLUB_BAN,
    1291476899557671054: ROSE,
    1330393356198477824: AUTOREACT,
    1330393358904066148: AUTOROLE,
    1228227536207740989: AXON_OWNER,
    1364125472539021352: BLUEDOT,
    1330393366373863526: BOTS,
    1329382931449516058: BROWSER,
    1329004882992300083: COMMANDS,
    1327829124894429235: CROSSICON,
    1330393383830683710: CUSTOMROLE,
    1287302832244129823: DC_REDCROWNESPORTS,
    1327842168693461022: DELETE,
    1294218790082711553: DENIED,
    1329022921427128321: DISABLED1,
    1329382206921248808: DND,
    1204107832232775730: ENABLED,
    1329022799708160063: ENABLED_160063,
    1330393380810657843: EXTRA,
    1330393371650297887: FILDER,
    1327842123906547713: FILE,
    1329361532999569439: FORWARD,
    1330393345796603924: GAMES,
    1329025929971896340: GEAR,
    1275850452323401789: GIFD,
    1275850451212042391: GIFN,
    1197061264271212605: GIVEAWAY,
    1330395924299644980: GIVEAWAY_644980,
    1351861871690645505: GIVEAWAYS,
    1330393349441585253: GREET,
    1274781954482376857: HEADMOD,
    1274781856406962250: HEART_EM,
    1274769360560328846: HEERIYE,
    1332569722801225749: HOME,
    1327842151962513515: ICON_BOOSTER,
    1327829337461882913: ICON_PING,
    1327829310962401331: ICONARROWRIGHT,
    1327829324518391824: ICONLOAD,
    1327829370881966092: ICONS_BOT,
    1327829380935843941: ICONS_CHANNEL,
    1327829391178338304: ICONS_DISCORDBOTDEV,
    1327829459729911900: ICONS_MUSIC,
    1327829470027055184: ICONS_NEXT,
    1327829480835780609: ICONS_PAUSE,
    1328966531140288524: ICONS_PLUS,
    1327829522573430864: ICONS_WARNING,
    1327842140570779658: ICONSETTING,
    1329382255046430740: IDLE,
    1330398849101205524: IGNORE,
    1374723970376405113: INFO,
    1392125185817051239: INVITETRACKER,
    1306976886047375430: JIOSAAVN,
    1234399917792034846: KING,
    1274766735702233089: LAND_YILDIZ,
    1274781969640722475: LAND_YILDIZ_722475,
    1246691973633671268: LOADING,
    1328740531907461233: LOADING_461233,
    1392124867872165969: LOGGING,
    1295014945641201685: MAX__A,
    1329408091011285113: MENTION,
    1204106928675102770: ML_CROSS,
    1329382816441569372: MOBILE,
    1327845044182585407: MOD,
    1330393377203556412: MODERATION,
    1330406766151860297: MODULE,
    1330393374271737896: MUSIC,
    1332620358255116319: MUSIC_116319,
    1327829536053923934: MUSICSTOP_ICONS,
    1327829548426854522: NEXT,
    1329382356804440107: OFFLINE,
    1227866668152393789: OLYMPUS_CROSS,
    1227866804630720565: OLYMPUS_NOTIFY,
    1228227884481515613: OLYMPUS_STAFF,
    1227866641027698792: OLYMPUS_TICK,
    1297341001341599797: OLYMPUSARROW,
    1329382084837507092: ONLINE,
    1272731689948287068: OWNER,
    1329041011984433185: OWNER_433185,
    1329382763161321524: PC,
    1204110058124873889: PREMIUM,
    1329005603669938236: QUESTIONS,
    1222796144996777995: RED_DOT,
    1272229548280512547: REDHEART,
    1329360839874056225: REWIND1,
    1327829569264160870: RIVERSE_FUN,
    1330393362305515560: SECURITY,
    1273974278433280122: SG_RD,
    1329360518367936564: SHUFFLE,
    1329359900563996754: SKIP,
    1307002774738829413: SOUNDCLOUD,
    1292538970500235366: SQ_HEADMOD,
    1251876754516349059: STAR,
    1273588820373147803: STAR_147803,
    1327829594954530896: TICK,
    1374052118020882563: TICK_RED,
    1355527347335467191: TICKET,
    1329404677820911697: TIMER,
    1327829252120510567: U_ADMIN,
    1368920252871737444: UPTIME,
    1329379728603353108: USER,
    1330393368894902272: UTILITY,
    1392125176644108359: VANITYROLES,
    1327841731651174450: VOICE,
    1330393386490003466: VOICE_003466,
    1299512982006665216: WARNING,
    1327829272697634937: WARNINGICON,
    1329365996959567893: YOUTUBE,
    1344680847315570841: YOUTUBE_570841,
    1222750301233090600: ZTICK,
}


def get(name: str) -> CustomEmoji:
    return EMOJIS[name]


def get_by_id(emoji_id: int) -> CustomEmoji:
    return EMOJIS_BY_ID[emoji_id]


def mention(name: str) -> str:
    return str(get(name))


def all_custom_emojis() -> tuple[CustomEmoji, ...]:
    return tuple(EMOJIS_BY_ID.values())


def _constant_emojis() -> dict[str, CustomEmoji]:
    return {
        name: value
        for name, value in globals().items()
        if name.isupper() and isinstance(value, CustomEmoji)
    }


def _rebuild_indexes() -> None:
    EMOJIS.clear()
    EMOJIS_BY_ID.clear()
    for emoji in _constant_emojis().values():
        EMOJIS[emoji.name] = emoji
        EMOJIS_BY_ID[emoji.id] = emoji


def apply_application_emojis(application_emojis: Iterable[object]) -> int:
    by_name = {
        str(getattr(emoji, "name")).lower(): emoji
        for emoji in application_emojis
        if getattr(emoji, "name", None) and getattr(emoji, "id", None)
    }
    updates = 0

    for constant_name, current in _constant_emojis().items():
        application_emoji = by_name.get(current.name.lower())
        if application_emoji is None:
            continue

        next_emoji = CustomEmoji(
            str(getattr(application_emoji, "name")),
            int(getattr(application_emoji, "id")),
            bool(getattr(application_emoji, "animated", False)),
        )
        if next_emoji != current:
            globals()[constant_name] = next_emoji
            updates += 1

    if updates:
        _rebuild_indexes()
    return updates


_rebuild_indexes()
