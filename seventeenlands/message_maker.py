import re
from discord import TextChannel, Embed
import requests
from datetime import date

from seventeenlands.CardParseData import MessageParseData, CardParseData
from seventeenlands.utils.settings import SETS
from seventeenlands.utils.consts import COMMAND_STR
from seventeenlands.embed_maker import gen_card_embed, supported_color_strings, how_to_query_17lands
from seventeenlands.DataCache import DataCache


card_call_re = re.compile(r'({{.*?}})')


async def send_embed_message(channel, embed: Embed) -> None:
    """
    Sends an embed to the specified channel.
    :param channel: The channel to send the message to.
    :param embed: The embed to send.
    """
    print(f"Sending embedded message to channel '#{channel}'")
    await channel.send(embed=embed)


async def send_message(channel, message: str) -> None:
    """
    Sends a message to the specified channel.
    :param channel: The channel to send the message to.
    :param message: The message to send.
    """
    print(f'Sending message to channel {channel}: {message}')
    await channel.send(message)


async def handle_command(message: str, channel):
    print(f'Parsing message: {message}')
    rest = message[len(COMMAND_STR):].strip()

    # Get command
    command = rest.split(' ')[0]

    if command == 'colors':
        await send_embed_message(channel, supported_color_strings())
    elif command == 'help':
        await send_embed_message(channel, how_to_query_17lands())
    elif command == 'code':
        await send_message(channel, 'Based on <https://github.com/JasonYe4273/17lands-helper>')
    else:
        await send_message(channel, 'Current available commands are `colors`, `help`, and `code`')


def get_data_to_use(set_code: str, formats: list[str], query_str: str, use_cache: bool) -> dict:
    data_to_use = dict()
    for f in formats:
        # Use data from the cache if possible
        if use_cache:
            data_to_use[f] = DataCache[set_code][f]  # type: ignore[misc]
        elif f'{f}{query_str}' in DataCache[set_code]:  # type: ignore[misc]
            data_to_use[f] = DataCache[set_code][f'{f}{query_str}']  # type: ignore[misc]
        else:
            try:
                # Otherwise, query from 17lands and add the result to the cache
                data_to_use[f] = dict()
                DataCache[set_code][f'{f}{query_str}'] = dict()  # type: ignore[misc]
                print(f'Fetching data for {set_code} {f} with query {query_str}...')
                response = requests.get(
                    'https://www.17lands.com/api/card_data?' +
                    f'expansion={s}&event_type={f}{query_str}'
                )
                for c in response.json():
                    data_to_use[f][c['name']] = c
                    DataCache[set_code][f'{f}{query_str}'][c['name']] = c  # type: ignore[misc]
                print('Success!')
            except Exception:
                pass
                # await send_message(channel, f'Failed to fetch data for {s} {f} from 17lands')
    return data_to_use


async def send_card_call_response(card_call: CardParseData, channel) -> None:
    colors = None
    use_cache = True
    query_str = ''

    if len(card_call.OPTIONS.COLORS) == 1:  # type: ignore[arg-type]
        use_cache = False
        colors = card_call.OPTIONS.COLORS[0]  # type: ignore[index]

    if not use_cache:
        # Calculate 17lands query string
        query_str = f'&time_period=ALL_TIME'
        if colors:
            query_str += f'&colors={colors}'

    if card_call.OPTIONS.SET not in SETS:
        msg_str = f"Data for `{card_call.OPTIONS.SET}` is not currently available.\n" \
                  f"Please specify another set, or request that the data be added."
        await send_message(channel, msg_str)
    else:
        data_to_use = get_data_to_use(card_call.OPTIONS.SET,
                                      card_call.OPTIONS.FORMATS,  # type: ignore[arg-type]
                                      query_str,
                                      use_cache)
        try:
            await send_embed_message(channel, gen_card_embed(
                card=card_call.CARD_DATA,
                set_code=card_call.OPTIONS.SET,
                data=data_to_use,
                formats=card_call.OPTIONS.FORMATS,  # type: ignore[arg-type]
                fields=card_call.OPTIONS.STATS,  # type: ignore[arg-type]
                time_period="All Time",
                color_filter=(colors if colors else "None")
            ))
        except Exception:
            msg_str = f"An error occurred trying to display data for `{card_call.CARD_DATA['name']}` in " \
                      f"`{card_call.OPTIONS.SET}`."
            await send_message(channel, msg_str)


async def handle_card_request_v2(message: str, channel) -> None:
    match = card_call_re.findall(message)

    for call in match:
        card_parse = MessageParseData(call)

        for e in card_parse.CARD_SEARCH_ERRORS:
            await send_message(channel, e)

        if len(card_parse.CARD_CALLS) > 0:
            if not card_parse.OPTIONS.PARSED:
                msg_str = f"WARNING! Could not parse options `{card_parse.OPTIONS.OPTIONS_STR}`.\n" \
                          f"Some options have been reset to their defaults."
                await send_message(channel, msg_str)

            for card_call in card_parse.CARD_CALLS:
                await send_card_call_response(card_call, channel)
