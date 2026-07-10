from typing import Optional
import re
from datetime import date, timedelta, datetime

from seventeenlands.WUBRG import FAILSAFE, COLOR_COMBINATIONS, get_color_identity, get_color_supersets
from seventeenlands.utils.consts import STAT_ALIASES, DEFAULT_STATS
from seventeenlands.utils.settings import FORMAT_MAPPINGS, DEFAULT_FORMAT, SETS
from seventeenlands.utils.utils import query_scryfall


class CardParseOptions:
    # If this is in the opt_str, then use verbose.
    verbose_re = re.compile(r'([Vv]erbose ?|-[Vv])', re.IGNORECASE)

    # This could happen more than once, and could be a comma separated list of colour aliases
    color_re = re.compile(r'([Cc]olou?rs?|-[Cc])=([WUBRGwubrg, ]*(?: |$))', re.IGNORECASE)

    # This could happen more than once, and could be a comma separated list of format aliases
    format_re = re.compile(r'([Ff]ormats?|-[Ff])=([a-zA-Z0-9, ]*(?: |$))', re.IGNORECASE)

    # This could happen more than once, and could be a comma separated list of format aliases
    stats_re = re.compile(r'([Ss]tats?|[Cc]olumns?)=([a-zA-Z0-9, ]*(?: |$))', re.IGNORECASE)

    # This should happen once, and be a 3 character string of letters and numbers.
    set_re = re.compile(r'([Ss]et)=([a-zA-Z0-9]{3})', re.IGNORECASE)

    def __init__(self, options: str = ''):
        self.OPTIONS_STR: str = options
        self.PARSED: bool = self.OPTIONS_STR == ''
        self.VERBOSE: bool = False
        self.COLORS: Optional[list[str]] = None
        self.FORMATS: Optional[list[str]] = None
        self.STATS: Optional[list[str]] = None
        self.SET: Optional[str] = None

        self._handle_verbose()
        self._handle_color_filter()
        self._handle_format_filter()
        self._handle_set_override()
        self._handle_single_arg()

        if not self.PARSED:
            print(f"Could not parse options '{self.OPTIONS_STR}'!")

    @staticmethod
    def _parse_list_match(match_str: str):
        # Try to split on commas,
        if ',' in match_str:
            match_list = match_str.split(',')
        # But split on spaces if no commas are found.
        else:
            match_list = match_str.split(' ')

        # Initialize the return list,
        ret_list = []
        for ele in match_list:
            # And add whitespace-trimmed non-empty values to it.
            val = ele.strip()
            if val:
                ret_list.append(val)

        return ret_list

    def _handle_verbose(self):
        """ Handles self.VERBOSE """
        # Find the flag for verbose.
        verbose_match = self.verbose_re.search(self.OPTIONS_STR)
        self.VERBOSE = verbose_match is not None
        if self.VERBOSE:
            self.PARSED = True
            print("Verbose Mode enabled.")

    def _handle_color_filter(self):
        # Get the list of colours to display stats for, if it exists.
        color_match = self.color_re.search(self.OPTIONS_STR)

        if self.VERBOSE:
            print(f"color_match: {color_match is not None}")

        # If the flag is found,
        if color_match:
            self.PARSED = True
            # Initialize a list for COLORS, and split the found values.
            self.COLORS = list()
            colors = self._parse_list_match(color_match.group(2))
            if self.VERBOSE:
                print(f"colors: {colors is not None}")

            # For each value,
            for c in colors:
                # Clean the value,
                c_id = get_color_identity(c)
                # And if it is new and valid, append it to the list.
                if c_id != FAILSAFE and c_id not in self.COLORS:
                    self.COLORS.append(c_id)

            if self.VERBOSE:
                print(self.COLORS)

    def _handle_format_filter(self):
        # Get the list of formats to display stats for, if it exists.
        format_match = self.format_re.search(self.OPTIONS_STR)

        if self.VERBOSE:
            print(f"format_match: {format_match is not None}")

        if format_match:
            self.PARSED = True
            # Initialize a list for FORMATS, and split the found values.
            self.FORMATS = list()
            formats = self._parse_list_match(format_match.group(2))
            if self.VERBOSE:
                print(f"formats: {formats is not None}")

            # For each value,
            for f in formats:
                format_alias = f.lower()
                # If the alias is found in FORMAT_MAPPING get the name,
                if format_alias in FORMAT_MAPPINGS:
                    format_name = FORMAT_MAPPINGS[format_alias]
                    # And if it is a new item, add it to the list.
                    if format_name not in self.FORMATS:
                        self.FORMATS.append(format_name)

            if self.VERBOSE:
                print(self.FORMATS)

    def _handle_stats_filter(self):
        # Get the list of formats to display stats for, if it exists.
        stats_match = self.stats_re.search(self.OPTIONS_STR)

        if self.VERBOSE:
            print(f"stats_match: {stats_match is not None}")

        if stats_match:
            self.PARSED = True
            # Initialize a list for FORMATS, and split the found values.
            self.STATS = list()
            stats = self._parse_list_match(stats_match.group(2))
            if self.VERBOSE:
                print(f"formats: {stats is not None}")

            # For each value,
            for s in stats:
                stat_alias = s.lower()
                # If the alias is found in STAT_ALIASES get the name,
                if stat_alias in STAT_ALIASES:
                    stat_name = STAT_ALIASES[stat_alias]
                    # And if it is a new item, add it to the list.
                    if stat_name not in self.STATS:
                        self.STATS.append(stat_name)

            if self.VERBOSE:
                print(self.STATS)

    def _handle_set_override(self):
        # Get the set to pull data from, if it exists.
        set_match = self.set_re.search(self.OPTIONS_STR)

        if self.VERBOSE:
            print(f"set_match: {set_match is not None}")

        if set_match:
            self.PARSED = True
            self.SET = set_match.group(2).upper()

        if self.VERBOSE:
            print(self.SET)

    def _handle_single_arg(self):
        if '=' not in self.OPTIONS_STR:
            val = self.OPTIONS_STR.strip()

            if val.upper() in SETS:
                self.PARSED = True
                self.SET = val.upper()
                if self.VERBOSE:
                    print(f"Setting SET to {self.SET}, from single_arg")

            if val.lower() in FORMAT_MAPPINGS:
                self.PARSED = True
                self.FORMATS = [FORMAT_MAPPINGS[val.lower()]]
                if self.VERBOSE:
                    print(f"Setting FORMATS to {self.FORMATS}, from single_arg")

            color_val = get_color_identity(val)
            if color_val != '' and color_val in COLOR_COMBINATIONS:
                self.PARSED = True
                self.COLORS = [color_val]
                if self.VERBOSE:
                    print(f"Setting COLORS to {self.COLORS}, from single_arg")


class CardParseData:
    def __init__(self, card: dict, options: CardParseOptions):
        self.OPTIONS: CardParseOptions = options
        self.CARD_DATA: dict = card
        self._fill_missing_options()

    def _fill_missing_options(self):
        if not self.OPTIONS.COLORS:
            self.OPTIONS.COLORS = [''] + get_color_supersets(''.join(self.CARD_DATA['color_identity']), 2)

        if not self.OPTIONS.FORMATS:
            # info['formats'] = settings.get_user_formats(username)
            self.OPTIONS.FORMATS = [DEFAULT_FORMAT]

        if not self.OPTIONS.STATS:
            self.OPTIONS.STATS = DEFAULT_STATS

        if not self.OPTIONS.SET:
            # TODO: Search through the sets and find the most recent set in which the card was printed.
            self.OPTIONS.SET = self.CARD_DATA['set'].upper()


class MessageParseData:
    multi_card_re = re.compile(r'(?:"(.*?)")+')
    single_card_re = re.compile(r'{{(.*?) ?(?:\||}})')
    options_re = re.compile(r'\| ?(.*?)?}}')

    def __init__(self, cmd_str: str):
        """ :param cmd_str: The {{card_name | options}} style string. """
        self.CMD_STR: str = cmd_str
        # Attempt to find the options in the string.
        options_match = self.options_re.search(self.CMD_STR)

        # If found, use the options, otherwise use the empty string.
        if options_match:
            self._options_text = options_match[1]
        else:
            self._options_text = ''
        self.OPTIONS: CardParseOptions = CardParseOptions(self._options_text)

        self._card_name_list: list[str] = []
        self.CARDS: list[dict] = []
        self.CARD_SEARCH_ERRORS: list[str] = []
        self.CARD_CALLS: list[CardParseData] = []

        self._parse_cards()
        self._gen_card_calls()

    def _parse_cards(self):
        # Attempt to find multiple card names in the query, separated by quotes.
        self._card_name_list = self.multi_card_re.findall(self.CMD_STR)

        # If no names were found, attempt to parse query as a single card name.
        if not self._card_name_list:
            self._card_name_list = self.single_card_re.findall(self.CMD_STR)

        # For each card name found, get the card from scryfall.
        for name in self._card_name_list:
            card = query_scryfall(name)
            if 'error' not in card:
                self.CARDS.append(card)
            else:
                self.CARD_SEARCH_ERRORS.append(card['error'])

    def _gen_card_calls(self):
        # For each found card,
        for card in self.CARDS:
            self.CARD_CALLS.append(CardParseData(card, CardParseOptions(self._options_text)))


if __name__ == "__main__":
    test_strings = list()
    test_strings.append('{{"Virus Beetle" "Inkrise Infiltrator" | -w=1 -c=ub}}')
    for string in test_strings:
        card_parse = MessageParseData(string)
        for card_call in card_parse.CARD_CALLS:
            print(card_call.__dict__)
            print(card_call.OPTIONS.__dict__)
