from datetime import datetime
import re

import discord
from discord import app_commands

from util import client, tree, send_error, send_long_msg, log_command, ALL
from database import _get_all_db, _get_one_db, _set_db



CARD_LIST = ["The Dawning Archaic", "Rancorous Archaic", "Sundering Archaic", "Together as One", "Transcendent Archaic", "Ajani's Response", "Antiquities on the Loose", "Ascendant Dustspeaker", "Daydream", "Dig Site Inventory", "Eager Glyphmage", "Elite Interceptor", "Emeritus of Truce", "Ennis, Debate Moderator", "Erode", "Graduation Day", "Group Project", "Harsh Annotation", "Honorbound Page", "Informed Inkwright", "Inkshape Demonstrator", "Interjection", "Joined Researchers", "Owlin Historian", "Practiced Offense", "Primary Research", "Quill-Blade Laureate", "Rapier Wit", "Rehearsed Debater", "Restoration Seminar", "Shattered Acolyte", "Soaring Stoneglider", "Spiritcall Enthusiast", "Stand Up for Yourself", "Stirring Hopesinger", "Stone Docent", "Summoned Dromedary", "Banishing Betrayal", "Brush Off", "Campus Composer", "Chase Inspiration", "Deluge Virtuoso", "Divergent Equation", "Echocasting Symposium", "Emeritus of Ideation", "Encouraging Aviator", "Essence Scatter", "Exhibition Tidecaller", "Flow State", "Fractal Anomaly", "Fractalize", "Harmonized Trio", "Homesickness", "Hydro-Channeler", "Jadzi, Steward of Fate", "Landscape Painter", "Mana Sculpt", "Mathemagics", "Matterbending Mage", "Muse Seeker", "Muse's Encouragement", "Orysa, Tide Choreographer", "Pensive Professor", "Procrastinate", "Quick Study", "Run Behind", "Skycoach Conductor", "Spellbook Seeker", "Tester of the Tangential", "Textbook Tabulator", "Wisdom of Ages", "Adventurous Eater", "Arcane Omens", "Arnyn, Deathbloom Botanist", "Burrog Banemaker", "Cheerful Osteomancer", "Cost of Brilliance", "Decorum Dissertation", "Dissection Practice", "Emeritus of Woe", "End of the Hunt", "Eternal Student", "Foolish Fate", "Forum Necroscribe", "Grave Researcher", "Last Gasp", "Lecturing Scornmage", "Leech Collector", "Masterful Flourish", "Melancholic Poet", "Moseo, Vein's New Dean", "Poisoner's Apprentice", "Postmortem Professor", "Pox Plague", "Pull from the Grave", "Rabid Attack", "Ral Zarek, Guest Lecturer", "Scathing Shadelock", "Scheming Silvertongue", "Send in the Pest", "Sneering Shadewriter", "Tragedy Feaster", "Ulna Alley Shopkeep", "Wander Off", "Withering Curse", "Ancestral Anger", "Archaic's Agony", "Artistic Process", "Blazing Firesinger", "Charging Strifeknight", "Choreographed Sparks", "Duel Tactics", "Emeritus of Conflict", "Expressive Firedancer", "Flashback", "Garrison Excavator", "Goblin Glasswright", "Heated Argument", "Impractical Joke", "Improvisation Capstone", "Living History", "Maelstrom Artisan", "Magmablood Archaic", "Mica, Reader of Ruins", "Molten-Core Maestro", "Pigment Wrangler", "Rearing Embermare", "Rubble Rouser", "Seize the Spoils", "Steal the Show", "Strife Scholar", "Tablet of Discovery", "Tackle Artist", "Thunderdrum Soloist", "Tome Blast", "Unsubtle Mockery", "Zealous Lorecaster", "Aberrant Manawurm", "Additive Evolution", "Ambitious Augmenter", "Burrog Barrage", "Chelonian Tackle", "Comforting Counsel", "Efflorescence", "Emeritus of Abundance", "Emil, Vastlands Roamer", "Environmental Scientist", "Follow the Lumarets", "Germination Practicum", "Glorious Decay", "Hungry Graffalon", "Infirmary Healer", "Lumaret's Favor", "Mindful Biomancer", "Noxious Newt", "Oracle's Restoration", "Pestbrood Sloth", "Planar Engineering", "Shopkeeper's Bane", "Slumbering Trudge", "Snarl Song", "Studious First-Year", "Tenured Concocter", "Thornfist Striker", "Topiary Lecturer", "Vastlands Scavenger", "Wild Hypothesis", "Wildgrowth Archaic", "Zimone's Experiment", "Abigale, Poet Laureate", "Abstract Paintmage", "Applied Geometry", "Ark of Hunger", "Aziza, Mage Tower Captain", "Berta, Wise Extrapolator", "Blech, Loafing Pest", "Bogwater Lumaret", "Borrowed Knowledge", "Cauldron of Essence", "Colorstorm Stallion", "Colossus of the Blood Age", "Conciliator's Duelist", "Cuboid Colony", "Dina's Guidance", "Elemental Mascot", "Embrace the Paradox", "Essenceknit Scholar", "Fix What's Broken", "Fractal Mascot", "Fractal Tender", "Geometer's Arthropod", "Grapple with Death", "Growth Curve", "Hardened Academic", "Imperious Inkmage", "Inkling Mascot", "Killian's Confidence", "Kirol, History Buff", "Lluwen, Exchange Student", "Lorehold Charm", "Lorehold, the Historian", "Mind into Matter", "Mind Roots", "Molten Note", "Moment of Reckoning", "Nita, Forum Conciliator", "Old-Growth Educator", "Paradox Surveyor", "Pest Mascot", "Practiced Scrollsmith", "Prismari Charm", "Prismari, the Inspiration", "Proctor's Gaze", "Professor Dellian Fel", "Pterafractyl", "Pursue the Past", "Quandrix Charm", "Quandrix, the Proof", "Rapturous Moment", "Render Speechless", "Resonating Lute", "Root Manipulation", "Sanar, Unfinished Genius", "Scolding Administrator", "Silverquill Charm", "Silverquill, the Disputant", "Snooping Page", "Social Snub", "Spectacular Skywhale", "Spirit Mascot", "Splatter Technique", "Stadium Tidalmage", "Startled Relic Sloth", "Stirring Honormancer", "Stress Dream", "Suspend Aggression", "Tam, Observant Sequencer", "Teacher's Pest", "Traumatic Critique", "Vibrant Outburst", "Vicious Rivalry", "Visionary's Dance", "Wilt in the Heat", "Witherbloom Charm", "Witherbloom, the Balancer", "Zaffai and the Tempests", "Biblioplex Tomekeeper", "Diary of Dreams", "Mage Tower Referee", "Page, Loose Leaf", "Potioner's Trove", "Strixhaven Skycoach", "Deathcap Glade", "Dreamroot Cascade", "Fields of Strife", "Forum of Amity", "Great Hall of the Biblioplex", "Paradox Gardens", "Petrified Hamlet", "Shattered Sanctum", "Skycoach Waypoint", "Spectacle Summit", "Stormcarved Coast", "Sundown Pass", "Terramorphic Expanse", "Titan's Grave", "Akroma's Will", "Angel's Grace", "Armageddon", "Duty Beyond Death", "Helping Hand", "Hop to It", "Prismatic Ending", "Repel Calamity", "Reprieve", "Requisition Raid", "Return to the Ranks", "Winds of Abandon", "Brain Freeze", "Cyclonic Rift", "Daze", "Deduce", "Disdainful Stroke", "Flusterstorm", "Force of Will", "Pongify", "Preordain", "Sleight of Hand", "Spell Pierce", "Stock Up", "Ad Nauseam", "Bitter Triumph", "Culling the Weak", "Dismember", "Feed the Swarm", "Living End", "Locust Spray", "Sheoldred's Edict", "Smallpox", "Stargaze", "Vampiric Tutor", "Zombify", "Abrade", "Big Score", "Brotherhood's End", "Bulk Up", "Burst Lightning", "Crackle with Power", "Empty the Warrens", "Jeska's Will", "Monstrous Rage", "Pyretic Ritual", "Return the Favor", "Subterranean Tremors", "Awaken the Woods", "Berserk", "Crop Rotation", "Giant Growth", "Glimpse of Nature", "Knockout Maneuver", "Pick Your Poison", "Royal Treatment", "Shamanic Revelation", "Shared Roots", "Triumph of the Hordes", "Veil of Summer", "Bring to Light", "Culling Ritual", "Deflecting Palm", "Expressive Iteration", "Fracture"]
LOWER_CARD_LIST = [c.lower() for c in CARD_LIST]


async def card_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    subseq = re.compile('.*'.join(re.escape(x) for x in current.lower()))
    return [
        app_commands.Choice(name=n, value=n)
        for n in CARD_LIST
        if subseq.search(n.lower())
    ][:10]

@tree.command(  # type: ignore[arg-type]
    name="add_card_note",
    description="Record notes on a limited card",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.autocomplete(card=card_autocomplete)
async def add_card_note(interaction: discord.Interaction, your_name: str, card: str, note: str):
    if card.lower() not in LOWER_CARD_LIST:
        await send_error(interaction, "Invalid card")
        return

    _set_db(
        f"""INSERT INTO card_notes (server, card, note, recorded_by, recorded_at) VALUES
        (%s, %s, %s, %s, %s)""",
        (interaction.guild_id, card.lower(), note, your_name, int(datetime.now().timestamp()))
    )

    await interaction.response.send_message("Recorded!", ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="card_notes",
    description="Get all notes on a limited card",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.autocomplete(card=card_autocomplete)
async def card_notes(interaction: discord.Interaction, card: str):
    if card.lower() not in LOWER_CARD_LIST:
        await send_error(interaction, "Invalid card")
        return

    notes = _get_all_db(f"SELECT note,recorded_by,recorded_at FROM card_notes WHERE server={interaction.guild_id} AND card='{card.lower()}'")
    if len(notes) == 0:
        await interaction.response.send_message(f"No notes found for {card}")
        return

    msg = f"{len(notes)} sets of notes found for {card}:\n"
    for note in notes:
        msg += f"- {note[0]} - {note[1]} @ <t:{note[2]}:s>\n"
    await send_long_msg(interaction, msg)