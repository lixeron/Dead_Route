"""
Crew banter system: personality-driven interjections, ambient dialogue,
and reactive comments that make the bus feel alive.
"""

import random
from db import queries

BANTER = {
    "gruff": {
        "idle": [
            "Marcus is elbow-deep in the engine again. He hasn't said a word in an hour.",
            "Marcus flicks a bolt across the bus floor. \"Bored. That's a death sentence out here.\"",
            "You catch Marcus staring at a faded photo. He shoves it in his pocket when he notices you looking.",
            "\"This bus is held together by duct tape and spite,\" Marcus mutters. \"Mostly spite.\"",
            "Marcus cracks his knuckles one by one. It's the loudest sound on the bus.",
        ],
        "low_fuel": [
            "Marcus kicks the dashboard. \"She's drinking fumes. We need fuel or we're walking.\"",
            "\"I can squeeze maybe another mile out of this tank,\" Marcus says. He doesn't sound confident.",
        ],
        "low_food": [
            "Marcus's stomach growls. He glares at it like it betrayed him.",
            "\"I ate a shoe once,\" Marcus says flatly. \"I'd rather not do that again.\"",
        ],
        "after_combat": [
            "Marcus wipes something dark off his wrench. \"That never gets easier. Don't let anyone tell you it does.\"",
            "\"Everybody still got all their fingers?\" Marcus counts heads. Nods. Goes back to work.",
        ],
        "night": [
            "Marcus double-checks the door locks. Then checks them again.",
            "\"I'll take first watch,\" Marcus says. He always takes first watch.",
        ],
    },
    "cautious": {
        "idle": [
            "Elena is reorganizing the medical supplies again. Third time today.",
            "Elena counts the bandages. Counts them again. Her lips move silently.",
            "\"Has anyone been feeling feverish?\" Elena asks nobody in particular. \"Just checking.\"",
            "Elena is writing something in a small notebook. Patient notes. Old habits.",
            "You notice Elena positioned herself nearest the exit. She always does.",
        ],
        "low_fuel": [
            "Elena is already calculating walking distances on a crumpled map. Just in case.",
            "\"We should have a contingency plan,\" Elena says. \"In case the bus stops moving.\"",
        ],
        "low_food": [
            "Elena quietly portions out the remaining food into exact, tiny servings.",
            "\"I've seen what starvation does,\" Elena says quietly. \"We find food today, or we have a problem.\"",
        ],
        "after_combat": [
            "Elena immediately checks everyone for bites. No arguments. This is protocol.",
            "Elena patches up the wounds with steady hands. \"I'm fine,\" she says before anyone asks. She's lying.",
        ],
        "night": [
            "Elena triple-checks the first-aid kit. Needle, thread, tourniquet. Ready.",
            "\"Nobody leaves the bus after dark,\" Elena says. It's not a suggestion.",
        ],
    },
    "reckless": {
        "idle": [
            "Dex is carving another tally mark into his rifle stock. He seems way too happy about it.",
            "Dex flips a bullet between his fingers like a coin trick. \"You ever notice zombies don't blink?\"",
            "\"I'm just saying,\" Dex announces to nobody, \"I could probably take three at once.\"",
            "Dex is humming something. It might be a song. It might be the sound of someone losing it.",
            "Dex hangs his head out the window like a dog. \"Smell that? Freedom. And also death.\"",
        ],
        "low_fuel": [
            "\"So when we run out of gas, can I ride on the roof?\" Dex asks. He's serious.",
            "Dex suggests siphoning fuel from wrecked cars. \"I saw it in a movie once. How hard can it be?\"",
        ],
        "low_food": [
            "\"I could hunt something,\" Dex offers. \"Squirrels, deer, whatever. Same trigger pull.\"",
            "Dex eyes the canned goods. \"Dibs on the beans. I will fight you for the beans.\"",
        ],
        "after_combat": [
            "Dex is grinning. He's actually grinning. \"That was AWESOME. Did you see that headshot?\"",
            "\"New personal best,\" Dex says, patting his rifle. Everyone else is still shaking.",
        ],
        "night": [
            "Dex volunteers for a midnight supply run. Again. You tell him no. Again.",
            "\"The night is when the fun ones come out,\" Dex whispers, grinning in the dark.",
        ],
    },
    "intellectual": {
        "idle": [
            "Nadia is scribbling in her notebook. She fills three pages before looking up.",
            "\"The mutation rate is accelerating,\" Nadia says to herself. She doesn't elaborate.",
            "Nadia holds a dead insect up to the light, studying it. \"Even the bugs are different now.\"",
            "You catch Nadia mouthing chemical formulas. She notices and shrugs. \"Old habit.\"",
            "Nadia reorganizes her notes with color-coded tabs. The apocalypse hasn't killed her filing system.",
        ],
        "low_fuel": [
            "\"Ethanol can be distilled from corn,\" Nadia says. \"If we find a farm, I can make it work. Theoretically.\"",
            "Nadia starts calculating the bus's exact range. She doesn't share the number. That's not a good sign.",
        ],
        "low_food": [
            "Nadia identifies three edible plants on the roadside. \"Assuming the pathogen hasn't mutated into the soil.\"",
            "\"Caloric deficit compounds exponentially,\" Nadia says. \"In simple terms: we're in trouble.\"",
        ],
        "after_combat": [
            "Nadia collects a tissue sample from a dead zombie. \"For research.\" Everyone takes a step back.",
            "\"Their response time is faster than last week,\" Nadia observes. \"The pathogen is still evolving.\"",
        ],
        "night": [
            "Nadia stays up studying samples by flashlight. Sleep is a luxury she hasn't budgeted for.",
            "\"Statistically, nighttime attacks peak at 2 AM,\" Nadia says. Nobody wanted to know that.",
        ],
    },
    "optimist": {
        "idle": [
            "Tommy leads a stretching routine. Nobody joins, but he doesn't seem to mind.",
            "\"You know what today is?\" Tommy asks. \"Tuesday! Taco Tuesday!\" There are no tacos.",
            "Tommy whistles while organizing supplies. It's annoyingly cheerful. And somehow comforting.",
            "\"We should name the bus,\" Tommy suggests. \"Something inspiring. Like... Hope Machine.\"",
            "Tommy does push-ups in the aisle. \"Gotta stay ready,\" he says between reps.",
        ],
        "low_fuel": [
            "\"We'll find some,\" Tommy says firmly. \"We always find some.\" His jaw is clenched, though.",
            "Tommy suggests everyone push the bus to save fuel. He's only half joking.",
        ],
        "low_food": [
            "\"I used to do intermittent fasting,\" Tommy says. \"This is basically the same thing. Basically.\"",
            "Tommy splits his ration with whoever looks hungriest. He pretends he already ate.",
        ],
        "after_combat": [
            "\"Everyone okay? Everyone breathing?\" Tommy does a headcount. Twice. \"Okay. We're okay.\"",
            "Tommy claps someone on the shoulder. \"We're still here. That's a win. Every time is a win.\"",
        ],
        "night": [
            "Tommy tells a ghost story. It's terrible. But everyone listens anyway.",
            "\"Tomorrow's going to be better,\" Tommy says with absolute conviction. Nobody argues.",
        ],
    },
    "stoic": {
        "idle": [
            "Rhea is cleaning her rifle. She doesn't look up.",
            "Rhea sits by the window, scanning the horizon. She hasn't moved in twenty minutes.",
            "You notice Rhea's dog tags. She catches you looking. The moment passes without words.",
            "Rhea sharpens a knife. The sound is rhythmic. Almost meditative.",
            "Rhea checks every window. Every door. Every shadow. Then starts over.",
        ],
        "low_fuel": [
            "Rhea studies the map in silence. She circles two locations. Doesn't explain.",
            "\"We're going to need options,\" Rhea says. That's the most she's said all day.",
        ],
        "low_food": [
            "Rhea declines her ration. \"I've gone longer.\" Her voice leaves no room for argument.",
            "Rhea quietly sets a snare outside the bus. By morning, there's a rabbit.",
        ],
        "after_combat": [
            "Rhea reloads. Mag check. Safety off. Ready for the next one. No wasted motion.",
            "Rhea nods once. The military equivalent of a five-minute debrief.",
        ],
        "night": [
            "Rhea takes watch without being asked. She's a silhouette against the moonlight.",
            "\"Sleep,\" Rhea says. It's not a suggestion. She'll handle the night.",
        ],
    },
}

CROSS_BANTER = [
    ("gruff", "reckless", "Marcus tells Dex to stop wasting ammo on 'trick shots.' Dex tells Marcus to stop being old. It escalates from there."),
    ("gruff", "intellectual", "Marcus asks Nadia what she's writing. \"Notes on the pathogen.\" \"Write 'it sucks' and save yourself the trouble.\""),
    ("gruff", "optimist", "Tommy tries to get Marcus to sing. Marcus threatens to throw him off the bus. Tommy hums anyway."),
    ("gruff", "stoic", "Marcus and Rhea share a look. No words. They understand each other perfectly. Veterans of different wars, same exhaustion."),
    ("gruff", "cautious", "Marcus tells Elena the bus is fine. Elena asks when he last checked the brakes. Long pause. Marcus goes to check the brakes."),
    ("cautious", "reckless", "Elena tells Dex his last stunt almost got someone killed. Dex grins. \"Almost only counts in horseshoes.\" Elena is not amused."),
    ("cautious", "intellectual", "Elena and Nadia compare notes on the infected. It's the most animated either of them gets. Everyone else is uncomfortable."),
    ("cautious", "optimist", "\"What if we don't make it?\" Elena asks. \"We will,\" Tommy says. \"But what if--\" \"We will.\""),
    ("reckless", "stoic", "Dex challenges Rhea to a shooting contest. She puts three rounds through the same hole without changing expression. Contest over."),
    ("reckless", "optimist", "Dex and Tommy somehow get along. This concerns everyone else on the bus."),
    ("intellectual", "stoic", "Nadia asks Rhea about her unit. Long silence. \"They're gone.\" Nadia nods and goes back to her notebook."),
    ("intellectual", "optimist", "Tommy asks Nadia to explain the virus in simple terms. She tries. Tommy's smile falters for the first time."),
    ("optimist", "stoic", "Tommy offers Rhea a high five. She stares at his hand. He slowly lowers it. \"Rain check.\""),
]


def get_ambient_banter(context: str = "idle") -> str | None:
    npcs = queries.get_alive_npcs()
    if not npcs:
        return None

    if len(npcs) >= 2 and random.random() < 0.4:
        personalities = {c["personality"] for c in npcs}
        eligible = [
            (p1, p2, line) for p1, p2, line in CROSS_BANTER
            if p1 in personalities and p2 in personalities
        ]
        if eligible:
            return random.choice(eligible)[2]

    npc = random.choice(npcs)
    personality = npc["personality"]
    pool = BANTER.get(personality, {}).get(context, [])
    if not pool:
        pool = BANTER.get(personality, {}).get("idle", [])

    return random.choice(pool) if pool else None


def get_context(state: dict, resources: dict) -> str:
    if resources["fuel"] <= 8:
        return "low_fuel"
    if resources["food"] <= 3:
        return "low_food"
    if state["current_phase"] in ("evening", "midnight"):
        return "night"
    return "idle"
