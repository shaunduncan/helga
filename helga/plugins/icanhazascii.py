import re
import time

from helga.plugins import match

FLOOD_RATE = 30

LAST_USED = {}

ANIMALZ = {
    r'((p|br)oniez|pony|brony)': """
            .,,.
         ,;;*;;;;,
        .-'``;-');;.
       /'  .-.  /*;;
     .'    \\d    \\;;               .;;;,
    | o      `    \\;             ,;*;;;*;,
    \\__, _.__,'   \\_.-') __)--.;;;;;*;;;;,
     `\"\"`;;;\\       /-')_) __)  `\\' ';;;;;;
        ;*;;;        -') `)_)  |\\ |  ;;;;*;
        ;;;;|        `---`    O | | ;;*;;;
        *;*;\\|                 O  / ;;;;;*
       ;;;;;/|    .-------\\      / ;*;;;;;
      ;;;*;/ \\    |        '.   (`. ;;;*;;;
      ;;;;;'. ;   |          )   \\ | ;;;;;;
      ,;*;;;;\\/   |.        /   /` | ';;;*;
       ;;;;;;/    |/       /   /__/   ';;;
       '*;;*/     |       /    |      ;*;
            `\"\"\"\"`        `\"\"\"\"`     ;'""",

    r'(pupp|dogg)iez': """
                              _
                           ,:'/   _..._
                          // ( `\"\"-.._.'
                          \\| /    0\\___
                          |            4
                          |            /
                          \\_       .--'
                          (_'---'`)
                          / `'---`()
                        ,'        |
        ,            .'`          |
        )\\       _.-'             ;
       / |    .'`   _            /
     /` /   .'       '.        , |
    /  /   /           \\   ;   | |
    |  \\  |            |  .|   | |
     \\  `\"|           /.-' |   | |
      '-..-\\       _.;.._  |   |.;-.
            \\    <`.._  )) |  .;-. ))
            (__.  `  ))-'  \\_    ))'
                `'--\"`       `\"\"\"`""",

    r'dolphinz': """
                                       __     HAI!
                                   _.-~  )
                        _..--~~~~,'   ,-/     _
                     .-'. . . .'   ,-','    ,' )
                   ,'. . . _   ,--~,-'__..-'  ,'
                 ,'. . .  (@)' ---~~~~      ,'
                /. . . . '~~             ,-'
               /. . . . .             ,-'
              ; . . . .  - .        ,'
             : . . . .       _     /
            . . . . .          `-.:
           . . . ./  - .          )
          .  . . |  _____..---.._/
    ~---~~~~----~~~~             ~~~~~~~~~~~~~~~""",

    r'kitt(iez|[ie]nz|eh)': """
       _             _
      | '-.       .-' |
       \\'-.'-\"\"\"-'.-'/    _
        |= _:'.':_ =|    /:`)
        \\ <6>   <6> /   /  /
        |=   |_|   =|   |:'\\
        >\\:.  \"  .:/<    ) .|
         /'-._^_.-'\\    /.:/
        /::.     .::\\  /' /
      .| '::.  .::'  |;.:/
     /`\\:.         .:/`\\(
    |:. | ':.   .:' | .:|
    | ` |:.;     ;.:| ` |
     \\:.|  |:. .:|  |.:/
      \\ |:.|     |.:| /
      /'|  |\\   /|  |`\\
     (,,/:.|.-'-.|.:\\,,)
       (,,,/     \\,,,)""",

    r'bat.?signal': """
       _==/          i     i          \==_
     /XX/            |\___/|            \XX\\
   /XXXX\            |XXXXX|            /XXXX\\
  |XXXXXX\_         _XXXXXXX_         _/XXXXXX|
 XXXXXXXXXXXxxxxxxxXXXXXXXXXXXxxxxxxxXXXXXXXXXXX
|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
 XXXXXX/^^^^"\XXXXXXXXXXXXXXXXXXXXX/^^^^^\XXXXXX
  |XXX|       \XXX/^^\XXXXX/^^\XXX/       |XXX|
    \XX\       \X/    \XXX/    \X/       /XX/
       "\       "      \X/      "      /" """,
}


def find_animal(message):
    for pat, ascii in ANIMALZ.iteritems():
        if re.match(pat, message, re.I):
            return ascii


@match(find_animal, priority=0)
def icanhazascii(client, channel, nick, message, found):
    """
    A plugin for generating showing ascii artz
    """
    global FLOOD_RATE, LAST_USED
    now = time.time()

    if channel in LAST_USED and (now - LAST_USED[channel]) < FLOOD_RATE:
        return

    LAST_USED[channel] = now
    return found
