"""
Deep character interaction scenes.

These replace the generic "ask how they're doing" interactions with
layered, progressive conversations that reveal character depth over time.
Each character has trust-gated dialogue tiers that unlock as the player
invests in the relationship. The goal: make the player care about these
people so deeply that every death, every infection, every scar feels personal.

Design philosophy:
  - Characters are people first, stat blocks second
  - Humor and warmth between the horror makes the horror worse
  - Nobody is one-dimensional — the tough guy has a soft spot,
    the optimist has a breaking point, the stoic has a story
  - Easter eggs and meta moments reward attentive players
"""

# ── Progressive Dialogue Trees ─────────────────────────────
# Each character has 5 tiers of dialogue unlocked by trust level.
# Early tiers: surface-level, guarded.
# Late tiers: raw, vulnerable, real.

DEEP_DIALOGUE = {
    "Marcus Cole": {
        "tier_1": {  # Trust 20-39: Guarded, transactional
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Marcus is under the bus, banging on something with a wrench. He doesn't look up."),
                        ("Marcus Cole", "Hand me the 9/16ths."),
                        ("narrator", "You hand him a wrench. He grunts. That's apparently conversation."),
                    ],
                    "trust_delta": 3,
                },
                {
                    "trigger": "backstory",
                    "text": [
                        ("Marcus Cole", "I fixed cars. Before. That's all you need to know."),
                        ("narrator", "The wall goes up so fast you can almost hear it slam."),
                    ],
                    "trust_delta": -2,
                },
            ],
        },
        "tier_2": {  # Trust 40-59: Starting to open up
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Marcus is sitting on the bus steps, staring at the sunset. He's holding something small — a photo, maybe."),
                        ("Marcus Cole", "You ever think about how quiet it is now? No traffic. No sirens. No music from the neighbor's yard at 2 AM."),
                        ("narrator", "He pauses."),
                        ("Marcus Cole", "I used to hate that music. Now I'd give anything to hear it one more time."),
                    ],
                    "trust_delta": 5,
                },
                {
                    "trigger": "share_meal",
                    "text": [
                        ("narrator", "You sit next to Marcus and split a can of beans. Neither of you speaks for a while."),
                        ("Marcus Cole", "My wife made the best chili. I'm talking competition-grade. Secret was smoked paprika."),
                        ("narrator", "He stares at the beans."),
                        ("Marcus Cole", "This tastes like sadness in a can."),
                        ("narrator", "You both laugh. It's the first real laugh you've heard in days."),
                    ],
                    "trust_delta": 8,
                    "cost": {"food": 1},
                },
            ],
        },
        "tier_3": {  # Trust 60-74: Real vulnerability
            "scenes": [
                {
                    "trigger": "backstory",
                    "text": [
                        ("narrator", "It's late. Everyone else is asleep. Marcus is awake, as usual, hands busy with something mechanical."),
                        ("Marcus Cole", "I had a daughter. Lily. Seven years old. Loved dinosaurs. Could name every single one, even the ones with thirty letters."),
                        ("narrator", "His hands stop moving."),
                        ("Marcus Cole", "When the outbreak hit Memphis, I was at the shop. Forty minutes away. I drove home in twelve. Ran three red lights and a barricade."),
                        ("narrator", "Long pause."),
                        ("Marcus Cole", "The front door was open. I've never told anyone what I found inside. I'm not going to tell you either."),
                        ("narrator", "He picks up the wrench again. His hands are shaking, but his voice is steady."),
                        ("Marcus Cole", "I keep this bus running because it's the only thing I know how to do that still matters. So let me do it. Okay?"),
                    ],
                    "trust_delta": 12,
                },
                {
                    "trigger": "small_talk",
                    "text": [
                        ("Marcus Cole", "Hey. I uh... I found this in one of the houses we searched."),
                        ("narrator", "He holds out a small, battered wind-up music box. He turns the key. A tinkling melody plays — Twinkle Twinkle Little Star, slightly off-key."),
                        ("Marcus Cole", "Lily had one just like it."),
                        ("narrator", "He sets it on the dashboard. Neither of you says anything. The music box plays until it winds down, and the bus is quiet again. But a different kind of quiet."),
                    ],
                    "trust_delta": 10,
                    "sets_flag": "marcus_music_box",
                },
            ],
        },
        "tier_4": {  # Trust 75-89: Deep bond
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Marcus hands you a cup of something hot. It smells terrible."),
                        ("Marcus Cole", "Found instant coffee in a glove compartment. It expired in 2019. I added creek water."),
                        ("narrator", "You both drink it. It's the worst coffee you've ever had."),
                        ("Marcus Cole", "You're alright, you know that? Most people out here... they take. They use. They leave. You're not like that."),
                        ("narrator", "He raises his cup."),
                        ("Marcus Cole", "To not being terrible people in a terrible world."),
                    ],
                    "trust_delta": 8,
                },
            ],
        },
        "tier_5": {  # Trust 90+: Devoted, would die for you
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Marcus pulls you aside while the others sleep."),
                        ("Marcus Cole", "Listen. I need to say something and I'm bad at this, so just... let me get through it."),
                        ("narrator", "He takes a breath."),
                        ("Marcus Cole", "I was done. After Memphis. After Lily. I was just going through the motions. Fixing things because that's what my hands do. Not because I cared if I woke up tomorrow."),
                        ("Marcus Cole", "Then your bus showed up. And you needed a mechanic. And for the first time in months, somebody needed me for something that mattered."),
                        ("narrator", "His voice cracks, just barely."),
                        ("Marcus Cole", "If it comes down to it — if it's me or the bus, me or you, me or any of these idiots — you let me go. You hear me? You keep driving. Promise me."),
                    ],
                    "trust_delta": 5,
                    "sets_flag": "marcus_promise",
                },
            ],
        },
    },

    "Elena Vasquez": {
        "tier_1": {
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("Elena Vasquez", "Are you hurt? Let me see. Roll up your sleeve."),
                        ("narrator", "You're fine. She checks anyway. Twice."),
                        ("Elena Vasquez", "Okay. Good. Just... tell me if anything changes."),
                    ],
                    "trust_delta": 3,
                },
            ],
        },
        "tier_2": {
            "scenes": [
                {
                    "trigger": "backstory",
                    "text": [
                        ("narrator", "Elena is inventorying the medical supplies for the fourth time today."),
                        ("Elena Vasquez", "I was a paramedic. Twelve years. You want to know the worst part of this?"),
                        ("narrator", "She holds up a half-empty bottle of ibuprofen."),
                        ("Elena Vasquez", "I used to have an ambulance full of equipment. Defibrillators. Oxygen. Real painkillers. Now I have this and some duct tape."),
                        ("Elena Vasquez", "People are going to die because I don't have the tools to save them. And I'm going to have to watch."),
                    ],
                    "trust_delta": 6,
                },
                {
                    "trigger": "share_meal",
                    "text": [
                        ("narrator", "Elena accepts the food but immediately tries to split it three ways."),
                        ("Elena Vasquez", "I don't need the whole thing. Someone else might—"),
                        ("narrator", "You push it back toward her."),
                        ("Elena Vasquez", "...fine. Thank you. I forget to eat sometimes. Occupational hazard. When you're the one keeping everyone alive, you forget you're included in 'everyone.'"),
                    ],
                    "trust_delta": 8,
                    "cost": {"food": 1},
                },
            ],
        },
        "tier_3": {
            "scenes": [
                {
                    "trigger": "backstory",
                    "text": [
                        ("narrator", "Elena is sitting alone, her notebook open to a page full of names. Some are crossed out."),
                        ("Elena Vasquez", "These are the people I couldn't save. Since the outbreak. I write down every name so someone remembers they existed."),
                        ("narrator", "The list is long. Very long."),
                        ("Elena Vasquez", "My partner, David, is on this list. Page three. He got bitten on a call. I watched the whole thing happen. Twelve years of saving people together, and I couldn't save him."),
                        ("narrator", "She closes the notebook carefully."),
                        ("Elena Vasquez", "I keep this list because if I stop counting, they become statistics. And the moment they're statistics, I've become something I don't want to be."),
                    ],
                    "trust_delta": 12,
                },
            ],
        },
        "tier_4": {
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Elena laughs. Actually laughs. You realize you've never heard it before."),
                        ("Elena Vasquez", "Sorry. I just... Dex tried to do a backflip off the bus roof to impress Rhea and landed in a thorn bush."),
                        ("narrator", "She's wiping tears from her eyes."),
                        ("Elena Vasquez", "I had to pull seventeen thorns out of his ass. SEVENTEEN. And Rhea just watched the whole thing without blinking."),
                        ("narrator", "For a moment, the apocalypse doesn't exist. It's just two people laughing until they can't breathe."),
                    ],
                    "trust_delta": 10,
                },
            ],
        },
        "tier_5": {
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Elena sits next to you, closer than usual. She's not checking for injuries this time."),
                        ("Elena Vasquez", "I've been thinking about what happens if we make it. To Haven, or wherever."),
                        ("Elena Vasquez", "I think I want to build a clinic. A real one. With actual walls and actual medicine and a sign on the door that says 'Everyone Welcome.'"),
                        ("narrator", "She looks at you."),
                        ("Elena Vasquez", "I'd want you there. Helping. You're not a doctor, but you're the reason any of us are still alive to need one."),
                        ("narrator", "She puts her hand on yours. Just for a moment. Then she's Elena again — checking supplies, counting bandages, planning for tomorrow. But the moment happened. And it mattered."),
                    ],
                    "trust_delta": 5,
                    "sets_flag": "elena_clinic_dream",
                },
            ],
        },
    },

    "Dex \"Deadeye\" Park": {
        "tier_1": {
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("Dex \"Deadeye\" Park", "Check it. Seventeen confirmed kills today. New record. I'm thinking of starting a leaderboard."),
                        ("narrator", "He's genuinely excited about this. It's a little unsettling."),
                    ],
                    "trust_delta": 3,
                },
            ],
        },
        "tier_2": {
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("Dex \"Deadeye\" Park", "You ever play video games? Before?"),
                        ("narrator", "You nod."),
                        ("Dex \"Deadeye\" Park", "This is literally a zombie survival game. We're IN the game. I used to play these for FUN. Is that messed up?"),
                        ("narrator", "He pauses, actually thinking about it."),
                        ("Dex \"Deadeye\" Park", "In the games, you respawn. That's the part they got wrong."),
                    ],
                    "trust_delta": 6,
                },
                {
                    "trigger": "small_talk",
                    "text": [
                        ("Dex \"Deadeye\" Park", "Hey, weird question. You ever wonder if, like... someone is watching us? Making our choices for us?"),
                        ("narrator", "You stare at him."),
                        ("Dex \"Deadeye\" Park", "Like a simulation, man. What if there's some dude sitting at a computer, clicking buttons, and WE'RE the ones running around doing whatever they pick?"),
                        ("narrator", "He gestures at the bus, the road, the wasteland."),
                        ("Dex \"Deadeye\" Park", "Because if someone IS controlling me, they've got TERRIBLE taste in apocalypses. At least give me a laser gun or something."),
                        ("narrator", "He's joking. Probably."),
                    ],
                    "trust_delta": 5,
                    "sets_flag": "dex_simulation_theory",
                },
            ],
        },
        "tier_3": {
            "scenes": [
                {
                    "trigger": "backstory",
                    "text": [
                        ("narrator", "Dex is cleaning his rifle. His usual grin is gone."),
                        ("Dex \"Deadeye\" Park", "I was competitive. Shooting, I mean. Three-gun, precision rifle, the whole circuit. Had sponsors. Was going to the nationals."),
                        ("narrator", "He chambers a round, unchambered it, chambers it again. Nervous habit."),
                        ("Dex \"Deadeye\" Park", "My mom used to come to every match. Front row. She'd bring this big stupid sign that said 'DEADEYE' with glitter on it. I pretended to be embarrassed but I loved it."),
                        ("narrator", "The rifle clicks softly in his hands."),
                        ("Dex \"Deadeye\" Park", "She was in a care home when it hit. Dementia. Couldn't... couldn't understand what was happening. The staff left. Just left. I got there and the doors were wide open and she was sitting in her wheelchair in the hallway, alone, asking for someone named Michael. That was my dad. He died in '09."),
                        ("narrator", "Long silence."),
                        ("Dex \"Deadeye\" Park", "I got her out. But she didn't last long after that. The confusion, the fear... she just kind of... stopped."),
                        ("narrator", "He sniffs hard, once, and forces the grin back on."),
                        ("Dex \"Deadeye\" Park", "Anyway. That's why I keep count. Every one of those things I put down, that's one less that gets to do what they did to her. Makes the numbers feel like they mean something."),
                    ],
                    "trust_delta": 15,
                },
            ],
        },
        "tier_4": {
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Dex drops the act. No grin, no bravado. Just a kid in a backwards cap sitting on a bus at the end of the world."),
                        ("Dex \"Deadeye\" Park", "I'm scared, man. Like, all the time. The jokes, the kill count, the 'look at me I'm so cool' thing — it's all just... noise. So I don't have to sit in the quiet and think about how we're probably all going to die."),
                        ("narrator", "He looks at his hands."),
                        ("Dex \"Deadeye\" Park", "But you don't treat me like I'm an idiot. Everyone else does. 'Oh there goes Dex, the reckless one, the funny one.' You actually listen. That means more than you know."),
                    ],
                    "trust_delta": 10,
                },
            ],
        },
        "tier_5": {
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Dex is sitting on the bus roof, legs dangling, watching the stars. He pats the space next to him."),
                        ("Dex \"Deadeye\" Park", "My mom used to say the stars were pinholes in the floor of heaven. So the angels could check on us."),
                        ("narrator", "He points up."),
                        ("Dex \"Deadeye\" Park", "If that's true, they're getting one HELL of a show right now."),
                        ("narrator", "You sit together in silence. The stars are impossibly bright without city lights to compete with. Somewhere far away, something howls. But up here, for this moment, it's almost peaceful."),
                        ("Dex \"Deadeye\" Park", "Hey. If I don't make it to Haven... make sure somebody remembers I was funny. Not brave. Not tough. Funny. That's what I want on the tombstone. 'He was funny.'"),
                        ("narrator", "He's smiling, but his eyes aren't."),
                    ],
                    "trust_delta": 5,
                    "sets_flag": "dex_tombstone",
                },
            ],
        },
    },

    "Nadia Okafor": {
        "tier_2": {
            "scenes": [
                {
                    "trigger": "backstory",
                    "text": [
                        ("Nadia Okafor", "I was three months from finishing my dissertation when the world ended. Three months. 'Mutation Dynamics in Synthetic Pathogens.' Ironic, right?"),
                        ("narrator", "She adjusts her glasses — a tic you've noticed she does when she's trying not to feel something."),
                        ("Nadia Okafor", "I know more about LAZARUS than almost anyone alive. I've been studying it from samples I've collected. The mutation rate, the transmission vectors, the neurological restructuring."),
                        ("narrator", "She opens her notebook. The pages are dense with formulas and diagrams."),
                        ("Nadia Okafor", "I think I understand how it works. But understanding and fixing are very different things."),
                    ],
                    "trust_delta": 7,
                },
            ],
        },
        "tier_3": {
            "scenes": [
                {
                    "trigger": "backstory",
                    "text": [
                        ("narrator", "Nadia is staring at a dead infected through the bus window. Not with fear — with something closer to fascination. And guilt about the fascination."),
                        ("Nadia Okafor", "The virus doesn't kill them. That's what people don't understand. It rewires them. The host is still alive — the heart beats, the lungs breathe, the muscles fire. But the consciousness... the person... is buried under layers of rewritten neural pathways."),
                        ("narrator", "She turns to you."),
                        ("Nadia Okafor", "I think they're still in there. Screaming. I think the worst part of LAZARUS isn't what it does to the body. It's that you're awake for all of it, trapped behind eyes you can't control, watching your hands do things you can't stop."),
                        ("narrator", "She closes her eyes."),
                        ("Nadia Okafor", "My advisor, Dr. Koroma. She got infected in the lab. I saw her three weeks later in the street. She looked right at me. And for one second — one second — I saw recognition. Then it was gone and she lunged."),
                        ("Nadia Okafor", "That second is why I need to get to wherever this started. Because if there's even a chance of reversing it... we owe it to every single one of them."),
                    ],
                    "trust_delta": 12,
                    "sets_flag": "nadia_cure_motivation",
                },
            ],
        },
        "tier_5": {
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Nadia is sitting with her notebook closed for once. She looks tired in a way that sleep won't fix."),
                        ("Nadia Okafor", "Can I tell you something I've never told anyone?"),
                        ("narrator", "You nod."),
                        ("Nadia Okafor", "I'm afraid that if we find a cure... it won't matter. That we've passed the point where science can fix this. That the world has changed so fundamentally that even if every infected person woke up tomorrow, we wouldn't know how to be a civilization again."),
                        ("narrator", "She looks at her hands."),
                        ("Nadia Okafor", "But I'm more afraid of the alternative. That there IS a cure, and I'm the only person left who could find it, and I die on this bus because we ran out of fuel or someone made a bad call or the universe just... didn't care."),
                        ("narrator", "She meets your eyes."),
                        ("Nadia Okafor", "So keep me alive. Please. Not for me. For everyone who's still screaming behind their own eyes."),
                    ],
                    "trust_delta": 5,
                    "sets_flag": "nadia_plea",
                },
            ],
        },
    },

    "Tommy Reeves": {
        "tier_2": {
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Tommy is doing push-ups in the aisle. He sees you watching and grins."),
                        ("Tommy Reeves", "Gotta stay ready! Zombie apocalypse fitness plan — patent pending."),
                        ("narrator", "He finishes his set and sits up, barely winded."),
                        ("Tommy Reeves", "You know what I miss? Coaching basketball. I had these kids — sixteen-year-olds, thought they knew everything. Couldn't make a free throw to save their lives. But man, when they finally got it..."),
                        ("narrator", "His smile changes. Softens."),
                        ("Tommy Reeves", "I wonder where they are now."),
                        ("narrator", "He starts another set of push-ups. Faster this time."),
                    ],
                    "trust_delta": 6,
                },
            ],
        },
        "tier_3": {
            "scenes": [
                {
                    "trigger": "backstory",
                    "text": [
                        ("narrator", "Tommy is sitting very still. Tommy is never still."),
                        ("Tommy Reeves", "I had twelve of them. My students. When the school was overrun, I got twelve kids on a bus — a real school bus, funny enough — and I drove."),
                        ("narrator", "He's gripping the seat so hard his knuckles are white."),
                        ("Tommy Reeves", "We made it four days. I found food. I found water. I kept them calm. I told them everything was going to be okay."),
                        ("narrator", "His voice drops."),
                        ("Tommy Reeves", "Then I went to scout a building and left them on the bus for ten minutes. Just ten minutes."),
                        ("narrator", "He doesn't finish the sentence. He doesn't need to."),
                        ("Tommy Reeves", "That's why I'm like this. The positivity, the 'everything will be fine' stuff. Because I said it to twelve kids and it was a lie, and if I stop saying it now, I have to admit it was always a lie."),
                        ("narrator", "He looks at you with eyes that are barely holding it together."),
                        ("Tommy Reeves", "But it CAN'T be a lie. Not this time. Not with you people. I won't let it be."),
                    ],
                    "trust_delta": 15,
                    "sets_flag": "tommy_twelve_kids",
                },
            ],
        },
        "tier_5": {
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Tommy sits next to you and says nothing for a long time. That alone tells you something is different."),
                        ("Tommy Reeves", "I don't say this to anyone. But I'm tired. I am so, so tired of being the one who smiles."),
                        ("narrator", "His voice is raw."),
                        ("Tommy Reeves", "Every morning I wake up and I choose to believe today will be better. And every day, it isn't. And I choose again the next morning. And the next. And the next."),
                        ("Tommy Reeves", "But you make it easier. Knowing someone else on this bus is fighting just as hard as I am... it makes the choosing easier."),
                        ("narrator", "He puts his hand on your shoulder. It's the steadiest thing in the whole shaking, rattling, falling-apart world."),
                        ("Tommy Reeves", "We're going to make it. And I don't mean that the way I usually do. I mean it."),
                    ],
                    "trust_delta": 5,
                },
            ],
        },
    },

    "Rhea Chen": {
        "tier_1": {
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Rhea is cleaning her rifle. She acknowledges you with a nod. That's it."),
                    ],
                    "trust_delta": 2,
                },
            ],
        },
        "tier_2": {
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Rhea speaks first. This has never happened before."),
                        ("Rhea Chen", "You handle yourself well."),
                        ("narrator", "Four words. From Rhea, that's a Shakespearean monologue."),
                    ],
                    "trust_delta": 8,
                },
            ],
        },
        "tier_3": {
            "scenes": [
                {
                    "trigger": "backstory",
                    "text": [
                        ("narrator", "Rhea is sitting watch. You bring her coffee — the terrible expired kind Marcus found. She takes it without a word, and you sit beside her."),
                        ("narrator", "Twenty minutes pass before she speaks."),
                        ("Rhea Chen", "Fort Whitmore. That was my unit. 274th Infantry. We held the line for nineteen days when DC fell."),
                        ("narrator", "Her voice is flat. Military flat. The kind of flat that's holding something enormous underneath."),
                        ("Rhea Chen", "On day twenty, command ordered us to fall back. By then, there was nothing to fall back to. We were fighting a retreating action through suburbs full of civilians who were turning faster than we could count."),
                        ("narrator", "She takes a sip of coffee."),
                        ("Rhea Chen", "I walked out of Fort Whitmore with three hundred soldiers. I walked out of the suburbs alone."),
                        ("narrator", "Another sip."),
                        ("Rhea Chen", "I don't talk about it because there's nothing to say. Good people died following orders given by people who were already dead. That's war. That's always been war. The zombies didn't change that."),
                    ],
                    "trust_delta": 15,
                },
            ],
        },
        "tier_5": {
            "scenes": [
                {
                    "trigger": "small_talk",
                    "text": [
                        ("narrator", "Rhea hands you something. A small brass compass, worn smooth from use."),
                        ("Rhea Chen", "My sergeant gave me this the day I enlisted. Said 'always know which way you're going.'"),
                        ("narrator", "She closes your hand around it."),
                        ("Rhea Chen", "I know which way I'm going now. With you. Wherever that leads. Whatever it costs."),
                        ("narrator", "She holds your gaze for exactly three seconds. Then she goes back to cleaning her rifle. But the compass in your hand is warm, and it means everything."),
                    ],
                    "trust_delta": 5,
                    "sets_flag": "rhea_compass",
                },
            ],
        },
    },
}


# ── Quiet Bus Moments ──────────────────────────────────────
# These fire randomly between phases when things are calm.
# They're not interactions — just atmosphere. Warmth before the storm.

QUIET_MOMENTS = [
    {
        "preconditions": {"min_crew": 3, "min_trust_avg": 50},
        "text": [
            ("narrator", "Someone found a deck of cards. Dog-eared, missing the seven of clubs. It doesn't matter. For one phase, the bus sounds like a living room — groaning, laughing, arguing about the rules of poker. Nobody mentions the dead. Nobody mentions tomorrow."),
        ],
    },
    {
        "preconditions": {"min_crew": 2, "flag": "marcus_music_box"},
        "text": [
            ("narrator", "Marcus winds the music box on the dashboard. Twinkle Twinkle Little Star fills the bus, tinkling and off-key. Nobody asks him to stop. Nobody says a word. When it winds down, the silence that follows is different from the usual silence. It's the silence of people who just shared something they didn't have words for."),
        ],
    },
    {
        "preconditions": {"min_crew": 4},
        "text": [
            ("narrator", "Elena falls asleep sitting up, her head resting against the window. Dex drapes his jacket over her shoulders without a word. When she wakes up an hour later, she looks at the jacket, looks at Dex, and says nothing. Dex pretends to be asleep. He isn't."),
        ],
    },
    {
        "preconditions": {"min_crew": 2, "phase": "morning"},
        "text": [
            ("narrator", "The sunrise is spectacular. Oranges and pinks and golds streaking across a sky that doesn't know the world has ended. Everyone on the bus stops what they're doing and watches. For thirty seconds, the apocalypse is beautiful."),
        ],
    },
    {
        "preconditions": {"min_crew": 3},
        "text": [
            ("narrator", "Tommy starts telling a joke. A terrible one — something about a zombie walking into a bar. It doesn't matter that the punchline makes no sense. What matters is that by the time he's done, three people are laughing and one is pretending not to. The bus sounds like it belongs to living people."),
        ],
    },
    {
        "preconditions": {"min_crew": 2},
        "text": [
            ("narrator", "Somebody wrote 'WASH ME' in the dust on the back window. Below it, in different handwriting: 'WITH WHAT?' Below that: 'TEARS.' Below THAT: 'WE'RE OUT OF THOSE TOO.' The bus has become a collaborative art project in apocalyptic one-liners."),
        ],
    },
    {
        "preconditions": {"min_crew": 3, "flag": "dex_simulation_theory"},
        "text": [
            ("narrator", "Dex is explaining his simulation theory to Tommy. Tommy looks deeply concerned — not about the theory, but about Dex's mental state. Nadia overhears and starts explaining actual multiverse theory. Within ten minutes, the three of them are in the most intellectually ambitious conversation the apocalypse has ever produced. Marcus watches from the back, bewildered. \"I just fix the engine,\" he mutters."),
        ],
    },
    {
        "preconditions": {"min_crew": 2, "phase": "midnight"},
        "text": [
            ("narrator", "It's quiet on the bus. The kind of quiet where you can hear everyone breathing. Someone is having a nightmare — small, choked sounds from the back seats. Someone else reaches over and holds their hand without waking them. The nightmare sounds stop. The hand doesn't let go."),
        ],
    },
]


# ── Utility Functions ──────────────────────────────────────

def get_deep_scene(char_name: str, trust: int, trigger: str = "small_talk") -> dict | None:
    """
    Get a trust-appropriate deep dialogue scene for a character.
    Returns scene dict or None if no scene available.
    """
    char_data = DEEP_DIALOGUE.get(char_name, {})
    if not char_data:
        return None

    # Determine tier from trust
    if trust >= 90:
        tier_key = "tier_5"
    elif trust >= 75:
        tier_key = "tier_4"
    elif trust >= 60:
        tier_key = "tier_3"
    elif trust >= 40:
        tier_key = "tier_2"
    else:
        tier_key = "tier_1"

    tier_data = char_data.get(tier_key)
    if not tier_data:
        # Fall back to highest available tier below current
        for fallback in ["tier_4", "tier_3", "tier_2", "tier_1"]:
            if fallback in char_data:
                tier_data = char_data[fallback]
                break

    if not tier_data:
        return None

    # Find scenes matching the trigger
    import random
    matching = [s for s in tier_data.get("scenes", []) if s["trigger"] == trigger]
    if not matching:
        # Fall back to any scene in the tier
        matching = tier_data.get("scenes", [])

    return random.choice(matching) if matching else None


def get_quiet_moment(crew: list, state: dict) -> dict | None:
    """
    Check if a quiet moment should fire.
    Returns moment dict or None.
    """
    import random
    from db import queries

    if random.random() > 0.15:  # 15% chance per phase
        return None

    flags = queries.get_all_flags()
    npcs = queries.get_alive_npcs()
    avg_trust = sum(c["trust"] for c in npcs) / max(1, len(npcs)) if npcs else 0

    eligible = []
    for moment in QUIET_MOMENTS:
        pre = moment.get("preconditions", {})
        if len(crew) < pre.get("min_crew", 0):
            continue
        if avg_trust < pre.get("min_trust_avg", 0):
            continue
        if "flag" in pre and not flags.get(pre["flag"]):
            continue
        if "phase" in pre and state["current_phase"] != pre["phase"]:
            continue
        eligible.append(moment)

    return random.choice(eligible) if eligible else None
