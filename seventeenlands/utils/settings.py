UPDATING_SETS: list[str] = ['MSH']
OLD_SETS: list[str] = ['SOS']
SETS: list[str] = UPDATING_SETS + OLD_SETS
DEFAULT_FORMAT: str = 'PremierDraft'

ALL_17L_SETS = ["MSH", "SOS", "Y26SOS", "TMT", "ECL", "Y26ECL", "TLA", "OM1", "EOE", "FIN", "Y25EOE", "TDM", "Y25TDM", "DFT", "Y25DFT", "PIO", "FDN", "DSK", "Y25DSK", "BLB", "Y25BLB", "MH3", "OTJ", "Y24OTJ", "MKM", "Y24MKM", "WOE", "Y24WOE", "LCI", "Y24LCI", "LTR", "MOM", "MAT", "SIR", "ONE", "Y23ONE", "BRO", "Y23BRO", "DMU", "Y23DMU", "HBG", "SNC", "Y22SNC", "NEO", "DBL", "VOW", "RAVM", "MID", "AFR", "STX", "CORE", "KHM", "KLR", "ZNR", "AKR", "M21", "IKO", "THB", "ELD", "Ravnica", "M20", "WAR", "M19", "DOM", "RIX", "GRN", "RNA", "KTK", "XLN", "Cube - Powered", "Cube", "Chaos", "Remix - Artifacts"]

FORMATS: dict[str, list[str]] = {
    'PremierDraft': ['bo1', 'premier', 'premierdraft'],
    'TradDraft': ['bo3', 'trad', 'traditional', 'traddraft', 'traditionaldraft'],
    'QuickDraft': ['qd', 'quick', 'quickdraft'],
    'Sealed': ['sealed', 'bo1sealed', 'sealedbo1'],
    'TradSealed': ['tradsealed', 'bo3sealed', 'sealedbo3'],
    'DraftChallenge': ['challenge', 'draftchallenge'],
}

FORMAT_MAPPINGS: dict[str, str] = {alias: name for name in FORMATS for alias in FORMATS[name]}

TIME_MAPPING = {"firstweek": ("FIRST_WEEK", "First Week"), "notfirstweek": ("ALL_EXCEPT_FIRST_WEEK", "All Except First Week"), "lasttwoweeks": ("LAST_TWO_WEEKS", "Last Two Weeks"), "lastweek": ("LAST_WEEK", "Last Week"), "lastday": ("LAST_DAY", "Last Day")}

DATA_COMMANDS: dict[str, list[tuple[str, str, bool]]] = {
    'alsa': [('seen_count', '# Seen', True), ('avg_seen', 'ALSA', False)],
    'ata': [('pick_count', '# Taken', True), ('avg_pick', 'ATA', False)],
    'gp': [('game_count', '# GP', True), ('win_rate', 'GP WR', False)],
    'oh': [('opening_hand_game_count', '# OH', True), ('opening_hand_win_rate', 'OH WR', False)],
    'gd': [('drawn_game_count', '# GD', True), ('drawn_win_rate', 'GD WR', False)],
    'gih': [('ever_drawn_game_count', '# GIH', True), ('ever_drawn_win_rate', 'GIH WR', False)],
    'gnd': [('never_drawn_game_count', '# GND', True), ('never_drawn_win_rate', 'GND WR', False)],
    'iwd': [('drawn_improvement_win_rate', 'IWD', False)]
}
DATA_COMMANDS['drafts'] = DATA_COMMANDS['alsa'] + DATA_COMMANDS['ata']
DATA_COMMANDS['games'] = DATA_COMMANDS['gp'] + DATA_COMMANDS['oh'] + DATA_COMMANDS['gd'] + DATA_COMMANDS['gih'] + \
                         DATA_COMMANDS['gnd'] + DATA_COMMANDS['iwd']
DATA_COMMANDS['data'] = DATA_COMMANDS['drafts'] + DATA_COMMANDS['games']
