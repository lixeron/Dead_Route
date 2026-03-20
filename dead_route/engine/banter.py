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
    "sardonic": {
        "idle": [
            "Javi is preparing something in a dented pot. It smells... actually good? How is that possible?",
            "\"I once made a reduction sauce from motor oil and despair,\" Javi says. \"It tasted better than this canned stuff.\"",
            "Javi has organized the food supplies by expiration date. They're all expired. He's organized them by 'how expired.'",
            "\"In my restaurant, this would be a health code violation. Out here, it's dinner.\" Javi plates the mystery meat on a hubcap.",
            "Javi is sharpening his cooking knife. It's the most dangerous weapon on the bus and nobody talks about it.",
        ],
        "low_fuel": [
            "\"I can cook without gas,\" Javi says. \"I cannot drive without gas. My skills have limits.\"",
            "Javi stares at the fuel gauge. \"I've seen soufflés with more substance.\"",
        ],
        "low_food": [
            "Javi is chewing his lip, staring at the empty shelves. This is personal for him. A cook without ingredients is a person without purpose.",
            "\"Give me a rat and thirty minutes,\" Javi says flatly. \"I'll make it taste like chicken. Don't ask how I know this.\"",
        ],
        "after_combat": [
            "Javi wipes something off his cooking knife. \"Zombies are like bad customers. They keep coming back and they never tip.\"",
            "\"Everyone still have all their limbs? Good. I can't cook for people who can't hold a spoon.\"",
        ],
        "night": [
            "Javi heats water on a camp stove. It's just hot water with a leaf in it. He calls it tea and nobody argues.",
            "\"I used to close the restaurant at 2 AM,\" Javi says, staring out the window. \"Walking to my car in the dark never used to be terrifying.\"",
        ],
    },
    "faithful": {
        "idle": [
            "Preacher Wells reads from his bullet-riddled Bible, lips moving silently. The book falls open to the same page every time.",
            "\"The Lord works in mysterious ways,\" Preacher says. He pauses. \"These ways are more mysterious than usual.\"",
            "Preacher is humming a hymn under his breath. It fills the bus with something that isn't quite peace, but isn't quite nothing either.",
            "Wells has carved tiny crosses into the dashboard with his thumbnail. Nobody asked him to stop. It felt wrong to.",
            "\"I've buried more people in six months than forty years of ministry,\" Preacher says quietly. \"Each one by name. Each one matters.\"",
        ],
        "low_fuel": [
            "\"Moses wandered forty years in the desert,\" Preacher says. \"We'll manage without fuel for a few more miles.\" He doesn't sound convinced.",
            "Preacher prays over the fuel tank. Marcus gives him a look. \"Can't hurt,\" Preacher says.",
        ],
        "low_food": [
            "\"Loaves and fishes,\" Preacher murmurs, dividing the last scraps. He gives away his share when he thinks nobody's watching.",
            "Preacher's hands shake when he distributes the rations. Not from hunger. From the weight of choosing who gets how much.",
        ],
        "after_combat": [
            "Preacher closes his eyes and whispers something over the fallen infected. Nobody mocks him for it.",
            "\"They were people once,\" Preacher says, looking at the bodies. \"I pray for what they were. Not what they became.\"",
        ],
        "night": [
            "Preacher reads scripture by moonlight. The words are old. The comfort is real.",
            "\"'Yea, though I walk through the valley of the shadow of death,'\" Preacher whispers. He looks out the window. \"This is the valley. We're in it.\"",
        ],
    },
    "anxious": {
        "idle": [
            "Sam is checking the locks on the bus door. Again. For the ninth time in an hour.",
            "Sam's leg bounces constantly. The vibration travels through the bus floor. Nobody mentions it.",
            "\"Do you think they can smell us?\" Sam asks, eyes wide. \"Like, through the metal? Can they smell through metal?\"",
            "Sam has memorized every exit on the bus. There are three. He recites them under his breath like a prayer.",
            "Sam is building something out of scrap wire and batteries. He won't say what. His hands are steadier when they're busy.",
        ],
        "low_fuel": [
            "Sam's breathing goes shallow. \"If we stop... if the bus stops moving...\" He can't finish the sentence. He doesn't need to.",
            "\"I calculated our range,\" Sam says, voice cracking. \"We have maybe twelve miles. Maybe.\"",
        ],
        "low_food": [
            "Sam hasn't asked for food in two days. Not because he's not hungry. Because asking means admitting how bad it is.",
            "\"I'm fine,\" Sam says. His stomach disagrees loudly. He wraps his arms around it like he can muffle the sound.",
        ],
        "after_combat": [
            "Sam is sitting in the corner, knees to chest, rocking slightly. He was brave during the fight. The fear always hits after.",
            "Sam's hands won't stop shaking. He keeps looking at the blood on them. \"I'm okay,\" he says to nobody. \"I'm okay I'm okay I'm okay.\"",
        ],
        "night": [
            "Sam doesn't sleep. He sits by the window with a flashlight, clicking it on and off. On and off. On and off.",
            "\"What was that sound?\" Sam whispers. There was no sound. But now everyone's listening.",
        ],
    },
    "weary": {
        "idle": [
            "Doc Harlan lowers himself into a seat with a groan that contains multitudes. \"My knees filed a formal complaint this morning.\"",
            "\"I've been alive for seventy-one years,\" Doc says. \"Sixty-nine of them were practice for this nonsense.\"",
            "Doc is napping sitting up, chin on chest. His hand still rests on the medical bag. Even asleep, he's on call.",
            "\"When I was your age,\" Doc starts. Everyone groans. He grins. \"Got you. I hate that phrase too.\"",
            "Doc polishes his reading glasses on his shirt. They're cracked. He squints through them anyway. \"Good enough for government work.\"",
        ],
        "low_fuel": [
            "\"I'm too old to walk,\" Doc says plainly. \"So I suggest we find fuel. My alternative contribution is dying dramatically and reducing the headcount.\"",
        ],
        "low_food": [
            "\"I've got maybe three weeks in me without food,\" Doc says with clinical detachment. \"Younger folks have longer. Prioritize accordingly.\"",
            "Doc hands his ration to Sam without a word. When Sam protests, Doc says, \"Hush. I'm investing in the future. Eat.\"",
        ],
        "after_combat": [
            "Doc works on the wounded with steady, ancient hands. His movements are slow but precise. He's done this a thousand times. Just usually on dogs.",
            "\"Adrenaline is a hell of a drug,\" Doc mutters, stitching a wound. \"Enjoy it while it lasts. The shaking starts in about ten minutes.\"",
        ],
        "night": [
            "Doc can't sleep anymore. Not because of fear — because his body has forgotten how. He sits watch because someone should.",
            "\"Old people don't need much sleep,\" Doc says. \"That's a myth, by the way. We need it. We just can't have it.\"",
        ],
    },
    "determined": {
        "idle": [
            "Zara is filming. Always filming. The camera lens catches everything — the blood, the beauty, the bus.",
            "\"Fourteen hours of footage,\" Zara says, checking the camera's dying battery. \"Fourteen hours of proof that we existed.\"",
            "Zara is writing in a notebook when the camera dies. The record continues. It always continues.",
            "\"Someone asked me why I bother,\" Zara says. \"Because someday, someone is going to need to know what happened. And I'll be the one who shows them.\"",
            "Zara interviews the crew when they let her. Most don't. But the ones who do talk for hours. Like they've been waiting for someone to ask.",
        ],
        "low_fuel": [
            "Zara films the fuel gauge. \"For the record,\" she says. Everything is for the record.",
            "\"If this is where the story ends,\" Zara says, raising the camera, \"at least it'll have documentation.\"",
        ],
        "low_food": [
            "Zara doesn't complain about hunger. She documented famine in three countries. This isn't new. It's just personal now.",
        ],
        "after_combat": [
            "Zara filmed the whole fight. Her hands didn't shake once. She's shaking now, though. After.",
            "\"I need to document the injuries,\" Zara says, camera raised. Elena blocks the lens. \"Not now.\" For once, Zara listens.",
        ],
        "night": [
            "Zara reviews footage by the blue light of the camera screen. Her face is illuminated in ghost-light. She looks haunted by what she's captured.",
        ],
    },
    "volatile": {
        "idle": [
            "Colt is flipping his knife. The blade catches light with each rotation. Nobody sits next to him.",
            "\"What are you looking at?\" Colt says to nobody in particular. The bus goes quiet.",
            "Colt carved something into the back of a bus seat. It's a name. Not his. He won't talk about it.",
            "You catch Colt staring at his hands. Old scars crisscross the knuckles. He clenches them into fists when he sees you looking.",
            "Colt laughs at something. The laugh is sharp and short and nobody else was part of the joke.",
        ],
        "low_fuel": [
            "\"If this bus stops, I'm not dying sitting in a metal box,\" Colt says. \"I'll take my chances on foot.\" He means it.",
        ],
        "low_food": [
            "Colt eyes the rations with a look that makes everyone uncomfortable. Prison taught him things about scarcity that civilization shouldn't know.",
            "\"In the joint, you fought for every meal,\" Colt says. \"At least out here, the competition can't file a shiv.\"",
        ],
        "after_combat": [
            "Colt is smiling. It's worse than Dex's combat grin because there's nothing behind it. Just reflex. Just violence rewarding itself.",
            "Blood on Colt's knuckles. Not his. He wipes it on his jeans without looking at it. Routine.",
        ],
        "night": [
            "Colt sleeps with one eye open. Literally. It's deeply unsettling.",
            "\"I've slept in worse places,\" Colt says, stretching out across a bus seat. \"At least this cage moves.\"",
        ],
    },
    "gentle": {
        "idle": [
            "Iris is folding blankets. There are three blankets on the bus. She has folded them seven times today.",
            "Iris sits next to whoever looks like they need it most. She doesn't speak. She just sits. Sometimes that's enough.",
            "\"How are you?\" Iris asks. She means it. Not the social pleasantry — the actual question. She waits for the real answer.",
            "Iris found wildflowers growing through a crack in the highway. She put them in an empty can on the dashboard. Nobody has moved them.",
            "Iris hums while she works. Not a song. Just a sound. Warm and low, like a mother's voice through a wall.",
        ],
        "low_fuel": [
            "Iris doesn't panic. She just quietly begins organizing what they'll need to carry if they have to walk. Practical compassion.",
        ],
        "low_food": [
            "Iris divides her ration into three portions and gives two away before anyone can stop her. \"I ate earlier,\" she lies. Nobody believes her.",
            "\"Hunger passes,\" Iris says softly. \"Kindness doesn't. Feed someone today and they remember it forever.\"",
        ],
        "after_combat": [
            "Iris is the first one tending wounds after every fight. Her hands are gentle even when the injuries aren't.",
            "Iris holds someone's hand while Elena stitches them up. She doesn't flinch at the blood. She spent years watching people suffer. She just learned to be present for it.",
        ],
        "night": [
            "Iris stays up with whoever can't sleep. She doesn't offer solutions. She just listens. Sometimes at 3 AM, that's the only medicine that works.",
            "\"You don't have to be strong right now,\" Iris whispers to someone crying in the dark. \"That's what the rest of us are for.\"",
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
    ("sardonic", "optimist", "Tommy says the sunrise is beautiful. Javi says it looks like the sky is bleeding. They stare at each other. \"We're VERY different people,\" Tommy says."),
    ("sardonic", "gruff", "Marcus and Javi argue about the best way to cook canned beans. It's the most passionate either of them has been in weeks. Nobody has the heart to tell them the beans are gone."),
    ("sardonic", "anxious", "Javi hands Sam a plate of something unidentifiable. \"Don't ask what it is.\" Sam asks. \"I told you not to ask.\" Sam puts the plate down. Picks it back up. Eats it anyway."),
    ("sardonic", "weary", "\"How are your knees, Doc?\" Javi asks. \"How's your cooking?\" Doc replies. \"Touché.\" They share a companionable silence."),
    ("faithful", "volatile", "Preacher offers to pray with Colt. Colt says something unprintable. Preacher nods. \"I'll pray for you anyway.\" Colt doesn't stop him."),
    ("faithful", "intellectual", "Nadia and Preacher have a quiet debate about creation and evolution. It's the most respectful argument anyone's heard in months. They agree to disagree. Then they keep talking."),
    ("faithful", "anxious", "Preacher puts a hand on Sam's shoulder. Sam flinches, then doesn't. \"You're going to be alright, son.\" Sam nods. He almost believes it."),
    ("faithful", "gentle", "Preacher and Iris sit together in silence. Two people whose job was comforting the dying, doing the same thing for the living."),
    ("anxious", "reckless", "Dex tries to teach Sam to shoot. Sam's hands shake so badly the barrel traces figure-eights. \"Okay,\" Dex says gently. \"Let's start with holding it.\""),
    ("anxious", "stoic", "Sam asks Rhea if she's ever scared. She looks at him for a long time. \"Every day.\" Sam's eyes go wide. It somehow makes him feel better."),
    ("anxious", "gentle", "Iris finds Sam hyperventilating in the back of the bus at 3 AM. She sits next to him and breathes slowly. In. Out. In. Out. After ten minutes, he matches her rhythm."),
    ("weary", "cautious", "Doc and Elena swap medical war stories. Doc's involve a lot more dogs. \"A hip replacement is a hip replacement,\" Doc insists. Elena looks horrified."),
    ("weary", "volatile", "Colt asks Doc if he's afraid of dying. \"Son, I'm seventy-one. I've been afraid of dying since before you were born. I just got bored of the fear.\""),
    ("determined", "intellectual", "Zara interviews Nadia about the pathogen. Three hours later, they're still talking. The footage will be the most important scientific record of LAZARUS in existence."),
    ("determined", "stoic", "Zara asks Rhea for an interview. \"No.\" \"Just five minutes.\" \"No.\" \"What about—\" \"No.\" Zara writes down 'refused interview x4' in her notebook."),
    ("determined", "sardonic", "Zara films Javi cooking. \"Apocalypse Kitchen, episode forty-seven,\" she narrates. Javi plays along with a full cooking show performance. It's the best content she's captured."),
    ("volatile", "reckless", "Colt and Dex compare kill counts. The energy between them is competitive and dangerous. Everyone else watches nervously. It's like two pit bulls circling."),
    ("volatile", "gruff", "Marcus catches Colt going through someone's bag. Their eyes meet. Colt puts the bag down. Slowly. Marcus doesn't blink. Some conversations don't need words."),
    ("gentle", "sardonic", "Iris asks Javi to teach her to cook. He's unexpectedly patient. \"You're burning it.\" \"Sorry!\" \"No, keep burning it. You'll learn what too far smells like. Everything in cooking is learning limits.\""),
    ("gentle", "weary", "Iris brings Doc water. He takes it without a word. She sits beside him. \"You don't have to carry everyone, Doc.\" \"Neither do you, Iris.\" They both know they won't stop."),
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
