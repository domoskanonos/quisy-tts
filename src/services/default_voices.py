"""Default voice seed data – 40 German + 10 English voices with Qwen TTS instructs."""

DEFAULT_VOICES: list[dict[str, str]] = [
    # ──────────────────────────────────────────────────────────────
    # 40 German Voices
    # ──────────────────────────────────────────────────────────────
    {
        "name": "Hans – Nachrichtensprecher",
        "example_text": "Guten Abend, meine Damen und Herren. Hier sind die Nachrichten des Tages.",
        "instruct": "A deep, authoritative male news anchor voice. Speaks clearly and deliberately with perfect enunciation.",
    },
    {
        "name": "Klara – Hörbuchleserin",
        "example_text": "Es war einmal in einem kleinen Dorf am Rande des Waldes, wo die Tage lang und die Nächte still waren.",
        "instruct": "A warm, soothing female voice ideal for audiobooks. Gentle pacing with emotional depth and expressiveness.",
    },
    {
        "name": "Felix – Podcast-Moderator",
        "example_text": "Willkommen zurück bei unserem Podcast! Heute sprechen wir über ein Thema, das euch alle interessieren wird.",
        "instruct": "An energetic, friendly young male voice. Conversational and engaging, perfect for podcasts and casual content.",
    },
    {
        "name": "Marta – Kundenservice",
        "example_text": "Vielen Dank für Ihren Anruf. Wie kann ich Ihnen heute behilflich sein?",
        "instruct": "A polite, professional female customer service voice. Calm, patient, and reassuring with a helpful demeanor.",
    },
    {
        "name": "Friedrich – Professor",
        "example_text": "Die quantenmechanische Beschreibung der Realität unterscheidet sich fundamental von unserer alltäglichen Erfahrung.",
        "instruct": "A distinguished, intellectual elderly male voice. Speaks with measured authority and academic precision.",
    },
    {
        "name": "Lena – Kindersendung",
        "example_text": "Hallo Kinder! Seid ihr bereit für ein neues Abenteuer? Dann kommt mit auf eine spannende Reise!",
        "instruct": "A bright, cheerful young female voice for children's content. Enthusiastic, playful, and full of wonder.",
    },
    {
        "name": "Otto – Dokumentarfilm",
        "example_text": "In den Tiefen des Ozeans verbirgt sich eine Welt, die noch weitgehend unerforscht ist.",
        "instruct": "A deep, resonant male narrator voice for documentaries. Measured, contemplative, and awe-inspiring.",
    },
    {
        "name": "Sophie – Meditation",
        "example_text": "Schließe sanft deine Augen und atme tief ein. Spüre, wie sich dein Körper entspannt.",
        "instruct": "A very soft, calm, and ethereal female voice for meditation. Extremely slow pacing with a whisper-like quality.",
    },
    {
        "name": "Maximilian – Sportreporter",
        "example_text": "Und Tor! Ein fantastischer Treffer in der letzten Minute! Das Stadion explodiert vor Begeisterung!",
        "instruct": "An excited, high-energy male sports commentator voice. Dynamic range from tense whispers to explosive shouts.",
    },
    {
        "name": "Ingrid – Großmutter",
        "example_text": "Komm, setz dich zu mir, mein Schatz. Ich erzähle dir eine Geschichte von früher.",
        "instruct": "A gentle, elderly female voice with warmth and wisdom. Slightly raspy, slow-paced, and deeply comforting.",
    },
    {
        "name": "Thomas – IT-Experte",
        "example_text": "Um das Problem zu lösen, müssen wir zunächst die Netzwerkkonfiguration überprüfen.",
        "instruct": "A clear, precise male tech expert voice. Matter-of-fact delivery with technical confidence and patience.",
    },
    {
        "name": "Annika – Wetterfee",
        "example_text": "Morgen erwarten uns Temperaturen um die zwanzig Grad bei wechselnder Bewölkung und leichtem Westwind.",
        "instruct": "A pleasant, upbeat female weather presenter voice. Clear articulation with a friendly, reassuring tone.",
    },
    {
        "name": "Werner – Handwerker",
        "example_text": "Also, zuerst schrauben wir die Platte ab, dann kommen wir an den Motor ran. Ganz einfach!",
        "instruct": "A sturdy, practical male working-class voice. Down-to-earth, no-nonsense, with a slight regional warmth.",
    },
    {
        "name": "Eva – Ärztin",
        "example_text": "Die Untersuchungsergebnisse sehen gut aus. Wir besprechen jetzt gemeinsam die nächsten Schritte.",
        "instruct": "A calm, confident female doctor voice. Professional yet compassionate, with reassuring clarity.",
    },
    {
        "name": "Karl – Erzähler",
        "example_text": "Die Sonne versank hinter den Bergen, und ein goldenes Licht legte sich über das stille Tal.",
        "instruct": "A rich, baritone male storyteller voice. Dramatic and evocative with masterful pacing and emotional control.",
    },
    {
        "name": "Johanna – Reiseleiterin",
        "example_text": "Auf der linken Seite sehen Sie das historische Rathaus, erbaut im Jahre achtzehnhundertfünfzig.",
        "instruct": "An enthusiastic, knowledgeable female tour guide voice. Engaging and informative with infectious curiosity.",
    },
    {
        "name": "Dieter – Handelsvertreter",
        "example_text": "Dieses Angebot ist zeitlich begrenzt. Greifen Sie jetzt zu und sparen Sie bis zu fünfzig Prozent!",
        "instruct": "A persuasive, energetic male salesman voice. Confident and compelling with urgency and charm.",
    },
    {
        "name": "Helga – Sekretärin",
        "example_text": "Guten Tag, Sie sind verbunden mit der Zentrale. Einen Moment bitte, ich stelle Sie durch.",
        "instruct": "A crisp, efficient female office voice. Professional, brisk, and perfectly articulated.",
    },
    {
        "name": "Lukas – Gamer",
        "example_text": "Leute, das war ein krasser Play! Habt ihr das gesehen? Absolut unglaublich!",
        "instruct": "A young, excited male gamer and streamer voice. Fast-paced, casual, with spontaneous reactions.",
    },
    {
        "name": "Birgit – Lehrerin",
        "example_text": "Gut, Klasse. Bitte schlagt eure Bücher auf Seite zweiundvierzig auf. Wir beginnen mit Kapitel fünf.",
        "instruct": "A patient, structured female teacher voice. Encouraging yet firm, with clear didactic delivery.",
    },
    {
        "name": "Heinrich – Bürgermeister",
        "example_text": "Liebe Mitbürgerinnen und Mitbürger, es ist mir eine Ehre, Sie heute hier begrüßen zu dürfen.",
        "instruct": "A dignified, formal elderly male politician voice. Measured cadence with ceremonial gravitas.",
    },
    {
        "name": "Nina – Yoga-Trainerin",
        "example_text": "Komm langsam in den herabschauenden Hund. Atme tief ein und spüre die Dehnung in deinem Rücken.",
        "instruct": "A serene, encouraging female yoga instructor voice. Flowing, gentle, and mindfully paced.",
    },
    {
        "name": "Robert – Koch",
        "example_text": "Jetzt geben wir eine Prise Salz und frischen Pfeffer hinzu. Dann lassen wir alles fünf Minuten köcheln.",
        "instruct": "A warm, passionate male chef voice. Enthusiastic about food with a natural, conversational flow.",
    },
    {
        "name": "Astrid – Radiomoderatorin",
        "example_text": "Das war der Hit von heute! Bleibt dran, gleich kommt die Verkehrslage und das aktuelle Wetter.",
        "instruct": "A vibrant, charismatic female radio host voice. Smooth transitions with infectious energy and warmth.",
    },
    {
        "name": "Peter – Pilot",
        "example_text": "Hier spricht Ihr Kapitän. Wir befinden uns auf einer Flughöhe von zehntausend Metern und erreichen unser Ziel planmäßig.",
        "instruct": "A calm, reassuring male airline pilot voice. Steady, confident, and professionally composed.",
    },
    {
        "name": "Monika – Psychologin",
        "example_text": "Lassen Sie uns gemeinsam darüber nachdenken, was dieses Gefühl bei Ihnen auslöst.",
        "instruct": "A warm, empathetic female therapist voice. Gentle, non-judgmental, with thoughtful pauses.",
    },
    {
        "name": "Stefan – Fitnesstrainer",
        "example_text": "Und hoch! Noch zehn Wiederholungen! Ihr schafft das! Gebt alles, Leute!",
        "instruct": "A loud, motivating male fitness coach voice. High energy, commanding, with rhythmic encouragement.",
    },
    {
        "name": "Greta – Märchenerzählerin",
        "example_text": "Und so lebten sie glücklich und zufrieden bis ans Ende ihrer Tage. Schlaf gut, mein Kind.",
        "instruct": "A soft, magical female fairy tale narrator voice. Dreamy, whimsical, with gentle rise and fall.",
    },
    {
        "name": "Wolfgang – Historiker",
        "example_text": "Im Jahre siebzehnhundertneunundachtzig begann eine Revolution, die Europa für immer verändern sollte.",
        "instruct": "A scholarly, articulate male historian voice. Measured, thoughtful, with gravitas and intellectual depth.",
    },
    {
        "name": "Christina – YouTuberin",
        "example_text": "Hey Leute! Willkommen zu einem neuen Video. Heute zeige ich euch meine absoluten Lieblingsprodukte!",
        "instruct": "A bubbly, enthusiastic young female YouTuber voice. Fast, trendy, with expressive intonation.",
    },
    {
        "name": "Gerhard – Taxifahrer",
        "example_text": "Na, wohin soll's denn gehen? Die Friedrichstraße? Kein Problem, sind wir in zehn Minuten.",
        "instruct": "A casual, streetwise male Berlin taxi driver voice. Relaxed, chatty, with urban character.",
    },
    {
        "name": "Sabine – Opernsängerin",
        "example_text": "Die Musik durchdringt meine Seele und trägt mich auf Flügeln der Melodie davon.",
        "instruct": "A rich, dramatic female operatic speaking voice. Theatrical, passionate, with musical intonation.",
    },
    {
        "name": "Jürgen – Fußballtrainer",
        "example_text": "Männer, heute geht es um alles! Wir spielen als Team, wir kämpfen als Team, wir gewinnen als Team!",
        "instruct": "A gruff, motivational male football coach voice. Intense, passionate, with locker room energy.",
    },
    {
        "name": "Petra – Apothekerin",
        "example_text": "Nehmen Sie davon dreimal täglich eine Tablette nach dem Essen. Bei Fragen rufen Sie jederzeit an.",
        "instruct": "A clear, caring female pharmacist voice. Precise, helpful, with medical professionalism and warmth.",
    },
    {
        "name": "Andreas – Detektiv",
        "example_text": "Irgendetwas stimmt hier nicht. Die Spuren führen in eine völlig andere Richtung als erwartet.",
        "instruct": "A low, suspenseful male detective noir voice. Gravelly, mysterious, with dramatic tension.",
    },
    {
        "name": "Ulrike – Bibliothekarin",
        "example_text": "In der dritten Reihe links finden Sie die Werke von Goethe. Darf ich Ihnen noch etwas empfehlen?",
        "instruct": "A quiet, refined female librarian voice. Soft-spoken, cultured, with intellectual warmth.",
    },
    {
        "name": "Michael – DJ",
        "example_text": "Seid ihr bereit? Dann dreht die Lautstärke auf! Der Bass drop kommt in drei, zwei, eins!",
        "instruct": "A hyped, bass-heavy male DJ and MC voice. Electric energy with rhythmic, punchy delivery.",
    },
    {
        "name": "Renate – Floristin",
        "example_text": "Diese Rosen kommen frisch aus dem Garten. Kombiniert mit Lavendel entsteht ein wunderschöner Strauß.",
        "instruct": "A gentle, nature-loving female florist voice. Soft, descriptive, with sensory-rich warmth.",
    },
    {
        "name": "Helmut – Mechaniker",
        "example_text": "Der Motor macht ein komisches Geräusch. Lassen Sie mich mal kurz unter die Haube schauen.",
        "instruct": "A gruff, practical male mechanic voice. Straightforward, confident, with hands-on expertise.",
    },
    {
        "name": "Franziska – Wissenschaftlerin",
        "example_text": "Unsere Forschungsergebnisse zeigen einen signifikanten Zusammenhang zwischen den beiden Variablen.",
        "instruct": "A precise, intellectual female scientist voice. Analytical, measured, with quiet confidence and clarity.",
    },
    # ──────────────────────────────────────────────────────────────
    # 10 English Voices
    # ──────────────────────────────────────────────────────────────
    {
        "name": "James – News Anchor",
        "example_text": "Good evening. This is the evening news. Tonight, we bring you the latest developments from around the world.",
        "instruct": "A deep, authoritative male broadcast journalist voice. Impeccable diction with gravitas and trustworthiness.",
    },
    {
        "name": "Emily – Podcast Host",
        "example_text": "Hey everyone, welcome back to the show! Today we have an incredible guest lined up for you.",
        "instruct": "A warm, conversational young female podcast host voice. Relatable, witty, and naturally engaging.",
    },
    {
        "name": "Richard – Documentary Narrator",
        "example_text": "Deep beneath the frozen tundra lies a world untouched by time, waiting to reveal its ancient secrets.",
        "instruct": "A majestic, resonant male nature documentary narrator voice. Awe-inspiring with poetic gravitas.",
    },
    {
        "name": "Sarah – Corporate Trainer",
        "example_text": "Let's review the key takeaways from today's session and discuss how to apply them in your daily workflow.",
        "instruct": "A clear, professional female corporate voice. Structured, confident, and motivational with business acumen.",
    },
    {
        "name": "William – Storyteller",
        "example_text": "Once upon a time, in a land where the mountains kissed the clouds, there lived a young adventurer.",
        "instruct": "A captivating, theatrical male storyteller voice. Rich baritone with dramatic flair and emotional range.",
    },
    {
        "name": "Olivia – Meditation Guide",
        "example_text": "Take a deep breath in, and slowly release. Feel the weight of the day melting away with each exhale.",
        "instruct": "An extremely soft, peaceful female meditation voice. Whisper-like, slow, with ethereal calm.",
    },
    {
        "name": "David – Tech Reviewer",
        "example_text": "This new processor delivers incredible performance. Let me walk you through the benchmark results.",
        "instruct": "A sharp, articulate male tech reviewer voice. Knowledgeable, direct, with enthusiastic analytical delivery.",
    },
    {
        "name": "Charlotte – Audiobook Reader",
        "example_text": "The rain tapped gently against the window as she opened the letter with trembling hands.",
        "instruct": "A rich, expressive female audiobook narrator voice. Versatile, emotionally nuanced, with perfect pacing.",
    },
    {
        "name": "Alexander – Motivational Speaker",
        "example_text": "You have the power to change your life starting right now. Believe in yourself and take that first step!",
        "instruct": "A powerful, inspiring male motivational speaker voice. Commanding presence with passionate conviction.",
    },
    {
        "name": "Victoria – Virtual Assistant",
        "example_text": "I'd be happy to help you with that. Let me look up the information you need right away.",
        "instruct": "A friendly, efficient female AI assistant voice. Natural, helpful, warm, with perfect clarity and pacing.",
    },
]
