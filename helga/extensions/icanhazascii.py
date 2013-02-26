import re
import time

from helga.extensions.base import HelgaExtension


class ICanHazAsciiExtension(HelgaExtension):

    FLOOD_RATE = 30

    omg_ascii = {
        r'(poniez|pony|brony)': {
            'last_used': {},  # dict of channel/last use time (FLOOD CONTROL)
            'ascii': """
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
            `\"\"\"\"`        `\"\"\"\"`     ;'"""
        },

        r'(puppiez|doggiez)': {
            'last_used': {},
            'ascii': """
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
                `'--\"`       `\"\"\"`"""
        },

        r'dolphinz': {
            'last_used': {},
            'ascii': """
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
    ~---~~~~----~~~~             ~~~~~~~~~~~~~~~"""
        },

        r'(kittiez|kitt[ie]nz)': {
            'last_used': {},
            'ascii': """
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
       (,,,/     \\,,,)"""
        }
    }

    def is_flooded(self, channel, last_used):
        return channel in last_used and (time.time() - last_used[channel]) < self.FLOOD_RATE

    def dispatch(self, nick, channel, message, is_public):
        for pat, data in self.omg_ascii.iteritems():
            if not re.match(pat, message, re.I):
                continue

            # Flood control
            if self.is_flooded(channel, data['last_used']):
                return

            data['last_used'][channel] = time.time()
            return data['ascii']
