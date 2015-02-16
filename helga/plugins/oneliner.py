# -*- coding: utf8 -*-
import random
import re

from helga.plugins import match


def imgur(image):
    """
    Returns an imgur link with a given hash
    """
    return 'http://i.imgur.com/{0}.gif'.format(image)


RESPONSES = {
    # Direct text responses
    r'(gross|disgusting|eww)': (imgur('XEEI0Rn'),),  # Dumb and Dumber Gag

    r'(\sGFY\s|GTFO|Fuck (You|Off))': (imgur('VPqgYjF'),    # Ryan Stiles pulling middle finger from pocket
                                       imgur('rWhZY3k'),),  # half baked

    r'womp womp': ("http://www.sadtrombone.com/?play=true",
                   "http://www.youtube.com/watch?v=_-GaXa8tSBE"),

    r'^:w?q$': ("this ain't your vi",),

    r'^(pwd$|(sudo|ls|cd|rm)(\s\w+|$))': "this ain't your shell",

    r'php': ("php is just terrible",
             "php's motto: MERGE ALL THE PULL REQUESTS"),

    r'^select( .* )from(.*)': "'; DROP TABLES;",

    r'mongo(db)?\s': 'http://youtu.be/b2F-DItXtZs',  # MongoDB is webscale

    r'gem install': "ruby. not even once.",

    r'^(logger|logs)\?$': "http://logger.ddtc.cmgdigital.com/",

    r'^docs\?$': 'http://docs.cmgdigital.com/',

    r'\\m/': 'rock on',

    r'((beetle|betel)(geuse|juice)\s?){3}': "i'm the ghost with the most",

    # lol, gifs
    r'(bravo|well done)': (imgur('wSvsV'),     # Citizen Kane slow clap
                           imgur('HUKCsCv'),   # Colbert & Stewart bravo
                           imgur('FwqHZ6Z')),  # Gamer conceding defeat

    r'is \w+ down\?': imgur('yX5o8rZ'),  # THE F5 HAMMER

    r"(i don't care|do i look like i care|zero fucks)": (
        imgur('oKydfNm'),  # Bird bouncing on hawk's head
        imgur('KowlC'),    # Gangam style 'do i look like i care'
        imgur('xYOqXJv'),  # Dog hitting cat with tail
        imgur('1b2YNU3'),  # But wait! bubble
    ),

    r'^nope$': (imgur('iSm1aZu'),   # Arrested development NOPE
                imgur('2xwe756'),   # Lonley island like a boss NOPE
                imgur('zCtbl'),     # Tracy Morgan NOPE
                imgur('foEHo'),     # Spongebob buried in sand
                imgur('xKYs9'),     # Puppy does not like lime
                imgur('ST9lw3U'),   # Seinfeld I'm Out
                imgur('c4gTe5p'),   # Cat thriller walk I'm out
                'http://i.minus.com/iUgVCKwjISSke.gif',  # The Nope Bader
                ),

    r'tl;?dr': (imgur('dnMjc'),   # Lightsaber did not read
                imgur('V2H9y')),  # Craig Robinson did not read

    r'panic': (imgur('tpGQV'),    # Aladding start panicking
               imgur('WS4S2'),    # Colbert screaming in terror
               imgur('rhNOy3I'),  # Panic cat bug eyes
               imgur('SNvM6CZ'),  # Girl leans on escalator handrail
               imgur('H7PXV'),    # Ain't nobody got time for that
               imgur('fH9e2')),   # Out of control truck on collision course

    r'shock(ed|ing)?': (imgur('zVyOBlR'),   # Cartoon is shocked
                        imgur('Q4bI5'),     # Shocked cat is shocked
                        imgur('wdA2Z'),     # Monsters Inc watching Boo in compactor
                        imgur('nj3yp'),     # Spock is shocked
                        imgur('AGnOQ'),     # PeeWee is shocked
                        imgur('wkY1FUI'),   # Shocked looks around
                        imgur('AXuUYIj')),  # Simpsons jaw drop

    r'(bloody mary|vodka)': imgur('W9SS4iJ'),  # Archer: Bloody Mary, blessed are you among cocktails

    r'popcorn': (imgur('00IJgSZ'),  # Thriller popcorn
                 imgur('5px9l')),   # Colbert popcorn

    r'deal with it': (imgur('12WoH'),    # Slip n slide DWI
                      imgur('6E6n1'),    # WTF Oprah
                      imgur('hYdy4'),    # Baseball catch deal with it
                      imgur('pqmfX'),    # WTF pouring water from nose
                      imgur('9WbAL'),    # A three toed sloth in a chair
                      imgur('KdldmZk'),  # Polar bear jumping out of water
                      imgur('49UtI5N'),  # The Fresh Prince of DEAL WITH IT
                      imgur('1pkNeOy'),  # Skyler
                      imgur('KzEXQDq'),  # Tom & Jerry
                      imgur('1kxk9z6'),  # deal with it dance
                      u'(⌐■_■)',

                      # Multiline
                      (u'( •_•)',
                       u'( •_•)>⌐■-■',
                       u'(⌐■_■)',
                       'deal with it'),

                      (u'. B     :-|',
                       u'.   B   :-|',
                       u'.     B :-|',
                       u'.       B-| deal with it')),

    r'(mind blown|blew my mind)': (imgur('U6kCXUp'),   # Head asploding
                                   imgur('1HMveGj')),  # Tim and Eric mind blown

    r'(sweet jesus|mother of god)': (imgur('5vXdAOV'),   # Captain Kirk
                                     imgur('g155Wra'),   # Star Trek freaking out
                                     imgur('dyeHb'),     # BJ Novak looks confused
                                     imgur('VkHiG6D'),   # Face twitching
                                     imgur('aiH4Mts'),   # Christopher Lloyd realizes something
                                     imgur('nOJme'),     # Cookie monster sweet jesus
                                     imgur('KtdHWhs'),   # Fight club realization
                                     imgur('z5hhSsU'),   # Cat with toy: OMG it was you!
                                     imgur('zuc9tAm')),  # Dinosaurs show - drops beer

    r'nailed it': (imgur('KsQzQTF'),   # Cat not trying to catch rat
                   imgur('5nrEk'),     # Olympic diving fail
                   imgur('n9zw0'),     # squirrel spinning on bird feeder
                   imgur('puZy04m'),   # Kid jumping into pool fail
                   imgur('MBdxv'),     # Girl trying to jump bike ramp fail
                   imgur('6XRqt'),     # FIXME
                   imgur('dFuBE'),     # Cat jumps into a box
                   imgur('vUACp'),     # Backflip off bleachers
                   imgur('59h9A8e')),  # Backflip off tree

    r'unacceptable': imgur('BwdP2xl'),  # 3D rendering goes wrong

    r'^(iknorite|right)\?$': imgur('RvquHs0'),  # Breaking Bad: You're god damn right

    r'fuck yea': (imgur('GZ5CD5r'),   # Data shooting dice
                  imgur('nEmrMkq')),  # Top Gun ... DANGER ZONE

    r'\w+ broke prod': (imgur('SuCGnum'),  # Anchorman: You ate the whole wheel of cheese?
                        imgur('sbQUDbF'),),  # fail boat

    r'^indeed$': imgur('bQcbpki'),  # Leonardo DiCaprio in Django Unchained

    r'f(f{6}|7)u(u{11}|12)': 'http://i.minus.com/ibnfJRQi1h4z30.gif',  # Workaholics: FUUUUUUUUUUUUUU

    r'wtf': imgur('bpW6Xkd'),  # WTF supercut


    # Various modern unicode emoticons
    r'(why|y) (u|you) no':                      u'ლ(ಠ益ಠლ)',
    r'i (don\'?t know|dunno),? lol':            u'¯\(°_o)/¯',
    r'look.?of.?disapproval(\.jpg|\.gif)?':     u'ಠ_ಠ',
    r'i (am disappoint|disapprove)':            u'ಠ_ಠ',
    r'^not sure if \w+':                        u'≖_≖',

    r'(tableflip|flip (a|the|some) tables?)':   (u'(╯°□°）╯︵ ┻━┻',
                                                 u'(ノಠ益ಠ)ノ彡┻━┻'),

    r'(gonna|going to) (make \w+ )?cry':        u'(ಥ﹏ಥ)',
    r'(bro ?fist|fist ?bump)':                  u'( _)=mm=(^_^ )',

    r'hi(gh)?[ -]?five':                        ('\o',
                                                 u'( ‘-’)人(ﾟ_ﾟ )'),

    r'(^|[^\\])o/$':                            '\o',
    r'^\\o$':                                   'o/'
}


def find_response(message):
    for pat, resp in RESPONSES.iteritems():
        if re.findall(pat, message, re.I):
            found = resp
            break
    else:
        return None

    if isinstance(resp, (tuple, list)):
        return random.choice(found)
    return found


@match(find_response, priority=0)
def oneliner(client, channel, nick, message, match):
    """
    Maybe some of these will become their own thing, but for
    now, they live here.

    DEAL WITH IT
    """
    return match  # pragma: no cover
