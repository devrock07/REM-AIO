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


EMOJI_37496ALERT = CustomEmoji('rem_alert', 1525739908826660984, False)
EMOJI_7CLUB_BAN = CustomEmoji('rem_ban', 1525739944205746286, False)
ROSE = CustomEmoji('rem_rose', 1525740415326621746, False)
AUTOREACT = CustomEmoji('rem_autoreact', 1525739929978798202, False)
AUTOROLE = CustomEmoji('rem_autorole', 1525739936966381638, False)
AXON_OWNER = CustomEmoji('rem_owner', 1525740365976440902, False)
BLUEDOT = CustomEmoji('rem_dot', 1525740064988991689, False)
BOTS = CustomEmoji('rem_bots', 1525739964845785089, False)
BROWSER = CustomEmoji('rem_browser', 1525739972294873268, False)
COMMANDS = CustomEmoji('rem_commands', 1525739993362993163, False)
CROSSICON = CustomEmoji('rem_cross', 1525740000728191106, False)
CUSTOMROLE = CustomEmoji('rem_customrole', 1525740021758296104, False)
DC_REDCROWNESPORTS = CustomEmoji('rem_crown', 1525740014703476877, False)
DELETE = CustomEmoji('rem_delete', 1525740028779692143, False)
DENIED = CustomEmoji('rem_denied', 1525740035838578873, False)
DISABLED1 = CustomEmoji('rem_disabled', 1525740050313248828, False)
DND = CustomEmoji('rem_dnd', 1525740057758269521, False)
ENABLED = CustomEmoji('rem_enabled', 1525740079040041141, False)
ENABLED_160063 = CustomEmoji('rem_on', 1525740351527059529, False)
EXTRA = CustomEmoji('rem_extra', 1525740085977415710, False)
FILDER = CustomEmoji('rem_folder', 1525740099978133604, False)
FILE = CustomEmoji('rem_file', 1525740092990423071, False)
FORWARD = CustomEmoji('rem_forward', 1525740107070574622, False)
GAMES = CustomEmoji('rem_games', 1525740121448644648, False)
GEAR = CustomEmoji('rem_settings', 1525740429096648948, False)
GIFD = CustomEmoji('rem_gif_off', 1525740128365183239, False)
GIFN = CustomEmoji('rem_gif_on', 1525740135386316952, False)
GIVEAWAY = CustomEmoji('rem_giveaway', 1525740142730412173, False)
GIVEAWAY_644980 = CustomEmoji('rem_giveaway', 1525740142730412173, False)
GIVEAWAYS = CustomEmoji('rem_giveaways', 1525740149785231431, False)
GREET = CustomEmoji('rem_welcome', 1525740608025788416, False)
HEADMOD = CustomEmoji('rem_headmod', 1525740156777271507, False)
HEART_EM = CustomEmoji('rem_heart', 1525740163861577858, False)
HEERIYE = CustomEmoji('rem_note', 1525740327925846177, False)
HOME = CustomEmoji('rem_home', 1525740185210327060, False)
ICON_BOOSTER = CustomEmoji('rem_booster', 1525739951252045884, False)
ICON_PING = CustomEmoji('rem_ping', 1525740387027652658, False)
ICONARROWRIGHT = CustomEmoji('rem_arrow_right', 1525739922860802130, False)
ICONLOAD = CustomEmoji('rem_load', 1525740235336450118, False)
ICONS_BOT = CustomEmoji('rem_bot', 1525739958155874324, False)
ICONS_CHANNEL = CustomEmoji('rem_channel', 1525739978934452287, False)
ICONS_DISCORDBOTDEV = CustomEmoji('rem_dev', 1525740043300376746, False)
ICONS_MUSIC = CustomEmoji('rem_music_note', 1525740306484428884, False)
ICONS_NEXT = CustomEmoji('rem_next', 1525740313841238197, False)
ICONS_PAUSE = CustomEmoji('rem_pause', 1525740372569882686, False)
ICONS_PLUS = CustomEmoji('rem_plus', 1525740394166616094, False)
ICONS_WARNING = CustomEmoji('rem_warning_sm', 1525740600924704919, False)
ICONSETTING = CustomEmoji('rem_cog', 1525739986505306162, False)
IDLE = CustomEmoji('rem_idle', 1525740192273662123, False)
IGNORE = CustomEmoji('rem_ignore', 1525740199517225070, False)
INFO = CustomEmoji('rem_info', 1525740206685163610, False)
INVITETRACKER = CustomEmoji('rem_invites', 1525740213404438602, False)
JIOSAAVN = CustomEmoji('rem_jiosaavn', 1525740220983541791, False)
KING = CustomEmoji('rem_king', 1525740228235628605, False)
LAND_YILDIZ = CustomEmoji('rem_star', 1525740472700637346, False)
LAND_YILDIZ_722475 = CustomEmoji('rem_star', 1525740472700637346, False)
LOADING = CustomEmoji('rem_loading', 1525740242538332263, False)
LOADING_461233 = CustomEmoji('rem_loading', 1525740242538332263, False)
LOGGING = CustomEmoji('rem_logging', 1525740249534300210, False)
MAX__A = CustomEmoji('rem_volume', 1525740579827224727, False)
MENTION = CustomEmoji('rem_mention', 1525740256157110274, False)
ML_CROSS = CustomEmoji('rem_cross_ml', 1525740007640404048, False)
MOBILE = CustomEmoji('rem_mobile', 1525740263455064114, False)
MOD = CustomEmoji('rem_mod', 1525740270216282194, False)
MODERATION = CustomEmoji('rem_moderation', 1525740284879700018, False)
MODULE = CustomEmoji('rem_module', 1525740291993370684, False)
MUSIC = CustomEmoji('rem_music', 1525740299379540019, False)
MUSIC_116319 = CustomEmoji('rem_music', 1525740299379540019, False)
MUSICSTOP_ICONS = CustomEmoji('rem_stop', 1525740493617631233, False)
NEXT = CustomEmoji('rem_skip_fwd', 1525740451120812052, False)
OFFLINE = CustomEmoji('rem_offline', 1525740341972570214, False)
OLYMPUS_CROSS = CustomEmoji('rem_no', 1525740320925679636, False)
OLYMPUS_NOTIFY = CustomEmoji('rem_notify', 1525740334976467066, False)
OLYMPUS_STAFF = CustomEmoji('rem_staff', 1525740465574514930, False)
OLYMPUS_TICK = CustomEmoji('rem_success', 1525740500999602227, False)
OLYMPUSARROW = CustomEmoji('rem_arrow', 1525739915503993033, False)
ONLINE = CustomEmoji('rem_online', 1525740358946783364, False)
OWNER = CustomEmoji('rem_owner', 1525740365976440902, False)
OWNER_433185 = CustomEmoji('rem_owner', 1525740365976440902, False)
PC = CustomEmoji('rem_pc', 1525740380014907422, False)
PREMIUM = CustomEmoji('rem_premium', 1525740400877371425, False)
QUESTIONS = CustomEmoji('rem_help', 1525740177820090428, False)
RED_DOT = CustomEmoji('rem_dot_red', 1525740072043941908, False)
REDHEART = CustomEmoji('rem_heart_red', 1525740170572464240, False)
REWIND1 = CustomEmoji('rem_rewind', 1525740407835721760, False)
RIVERSE_FUN = CustomEmoji('rem_fun', 1525740114096034013, False)
SECURITY = CustomEmoji('rem_security', 1525740422121521407, False)
SG_RD = CustomEmoji('rem_status_dot', 1525740486801752296, False)
SHUFFLE = CustomEmoji('rem_shuffle', 1525740436646268939, False)
SKIP = CustomEmoji('rem_skip', 1525740443592167578, False)
SOUNDCLOUD = CustomEmoji('rem_soundcloud', 1525740458355986545, False)
SQ_HEADMOD = CustomEmoji('rem_mod_shield', 1525740277854240798, False)
STAR = CustomEmoji('rem_star_badge', 1525740479986008077, False)
STAR_147803 = CustomEmoji('rem_star_badge', 1525740479986008077, False)
TICK = CustomEmoji('rem_tick', 1525740508222066829, False)
TICK_RED = CustomEmoji('rem_tick_red', 1525740515281080441, False)
TICKET = CustomEmoji('rem_ticket', 1525740529524936775, False)
TIMER = CustomEmoji('rem_timer', 1525740537381126185, False)
U_ADMIN = CustomEmoji('rem_admin', 1525739901587292172, False)
UPTIME = CustomEmoji('rem_uptime', 1525740544645533846, False)
USER = CustomEmoji('rem_user', 1525740551716999170, False)
UTILITY = CustomEmoji('rem_utility', 1525740558503379035, False)
VANITYROLES = CustomEmoji('rem_vanity', 1525740565776306306, False)
VOICE = CustomEmoji('rem_voice', 1525740572734914714, False)
VOICE_003466 = CustomEmoji('rem_voice', 1525740572734914714, False)
WARNING = CustomEmoji('rem_warning', 1525740586819125420, False)
WARNINGICON = CustomEmoji('rem_warning_badge', 1525740593953771703, False)
YOUTUBE = CustomEmoji('rem_youtube', 1525740615013236834, False)
YOUTUBE_570841 = CustomEmoji('rem_youtube', 1525740615013236834, False)
ZTICK = CustomEmoji('rem_tick_round', 1525740522369712350, False)


EMOJIS: dict[str, CustomEmoji] = {
    'rem_alert': EMOJI_37496ALERT,
    'rem_ban': EMOJI_7CLUB_BAN,
    'rem_rose': ROSE,
    'rem_autoreact': AUTOREACT,
    'rem_autorole': AUTOROLE,
    'rem_owner': AXON_OWNER,
    'rem_dot': BLUEDOT,
    'rem_bots': BOTS,
    'rem_browser': BROWSER,
    'rem_commands': COMMANDS,
    'rem_cross': CROSSICON,
    'rem_customrole': CUSTOMROLE,
    'rem_crown': DC_REDCROWNESPORTS,
    'rem_delete': DELETE,
    'rem_denied': DENIED,
    'rem_disabled': DISABLED1,
    'rem_dnd': DND,
    'rem_enabled': ENABLED,
    'rem_on': ENABLED_160063,
    'rem_extra': EXTRA,
    'rem_folder': FILDER,
    'rem_file': FILE,
    'rem_forward': FORWARD,
    'rem_games': GAMES,
    'rem_settings': GEAR,
    'rem_gif_off': GIFD,
    'rem_gif_on': GIFN,
    'rem_giveaway': GIVEAWAY,
    'giveaway': GIVEAWAY_644980,
    'rem_giveaways': GIVEAWAYS,
    'rem_welcome': GREET,
    'rem_headmod': HEADMOD,
    'rem_heart': HEART_EM,
    'rem_note': HEERIYE,
    'rem_home': HOME,
    'rem_booster': ICON_BOOSTER,
    'rem_ping': ICON_PING,
    'rem_arrow_right': ICONARROWRIGHT,
    'rem_load': ICONLOAD,
    'rem_bot': ICONS_BOT,
    'rem_channel': ICONS_CHANNEL,
    'rem_dev': ICONS_DISCORDBOTDEV,
    'rem_music_note': ICONS_MUSIC,
    'rem_next': ICONS_NEXT,
    'rem_pause': ICONS_PAUSE,
    'rem_plus': ICONS_PLUS,
    'rem_warning_sm': ICONS_WARNING,
    'rem_cog': ICONSETTING,
    'rem_idle': IDLE,
    'rem_ignore': IGNORE,
    'rem_info': INFO,
    'rem_invites': INVITETRACKER,
    'rem_jiosaavn': JIOSAAVN,
    'rem_king': KING,
    'rem_star': LAND_YILDIZ,
    'rem_star': LAND_YILDIZ_722475,
    'rem_loading': LOADING,
    'Loading': LOADING_461233,
    'rem_logging': LOGGING,
    'rem_volume': MAX__A,
    'rem_mention': MENTION,
    'rem_cross_ml': ML_CROSS,
    'rem_mobile': MOBILE,
    'rem_mod': MOD,
    'rem_moderation': MODERATION,
    'rem_module': MODULE,
    'rem_music': MUSIC,
    'rem_music': MUSIC_116319,
    'rem_stop': MUSICSTOP_ICONS,
    'rem_skip_fwd': NEXT,
    'rem_offline': OFFLINE,
    'rem_no': OLYMPUS_CROSS,
    'rem_notify': OLYMPUS_NOTIFY,
    'rem_staff': OLYMPUS_STAFF,
    'rem_success': OLYMPUS_TICK,
    'rem_arrow': OLYMPUSARROW,
    'rem_online': ONLINE,
    'rem_owner': OWNER,
    'rem_owner': OWNER_433185,
    'rem_pc': PC,
    'rem_premium': PREMIUM,
    'rem_help': QUESTIONS,
    'rem_dot_red': RED_DOT,
    'rem_heart_red': REDHEART,
    'rem_rewind': REWIND1,
    'rem_fun': RIVERSE_FUN,
    'rem_security': SECURITY,
    'rem_status_dot': SG_RD,
    'rem_shuffle': SHUFFLE,
    'rem_skip': SKIP,
    'rem_soundcloud': SOUNDCLOUD,
    'rem_mod_shield': SQ_HEADMOD,
    'rem_star_badge': STAR,
    'Star': STAR_147803,
    'rem_tick': TICK,
    'rem_tick_red': TICK_RED,
    'rem_ticket': TICKET,
    'rem_timer': TIMER,
    'rem_admin': U_ADMIN,
    'rem_uptime': UPTIME,
    'rem_user': USER,
    'rem_utility': UTILITY,
    'rem_vanity': VANITYROLES,
    'rem_voice': VOICE,
    'rem_voice': VOICE_003466,
    'rem_warning': WARNING,
    'rem_warning_badge': WARNINGICON,
    'rem_youtube': YOUTUBE,
    'YouTube': YOUTUBE_570841,
    'rem_tick_round': ZTICK,
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
