# -*- coding: utf8 -*-
import random
import re

from helga import settings
from helga.extensions.base import HelgaExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


def imgur(image):
    return 'http://i.imgur.com/%s.gif' % image


class OneLinerExtension(HelgaExtension):
    """
    Maybe some of these will become their own thing, but for
    now, they live here.

    DEAL WITH IT
    """

    NAME = 'oneliner'

    responses = {
        # Direct text responses
        r'(gross|disgusting|eww)': (imgur('XEEI0Rn'),),  # Dumb and Dumber Gag

        r'(GFY|GTFO|Fuck (You|Off))': (imgur('VPqgYjF'),), # Ryan Stiles, Whose Line, pulling middle finger from pocket

        r'womp womp': ("http://www.sadtrombone.com/?play=true",
                       "http://www.youtube.com/watch?v=_-GaXa8tSBE"),

        r'^:w?q': ("this ain't your vi",
                   "this ain't your vi, but at least you're not using emacs"),

        r'^((sudo|ls|cd|rm)( .+)?|pwd)': "%(nick)s, this ain't your shell",

        r'php': ("php is just terrible",
                 "MERGE ALL THE PULL REQUESTS"),

        r'^select( .* )from(.*)': "'; DROP TABLES;",

        r'mongo(db)?': 'http://youtu.be/b2F-DItXtZs',  # MongoDB is webscale

        r'gem install': "%(nick)s, don't. just don't",

        r'^(logger|logs)\?$': "http://logger.ddtc.cmgdigital.com/%(norm_channel)s",

        r'^docs\?$': 'http://docs.cmgdigital.com/',

        r'alfredo(deza)?': [
            "trollfredo:::everything you are doing is wrong",
            "trollfredo:::if you aren't using zsh, %(nick)s, you are doing it wrong",
            "trollfredo:::you are wrong %(nick)s",
            "trollfredo:::i have a vim plugin that shows you how wrong you are",
            "trollfredo:::i can't believe how wrong you are",
            "trollfredo:::wrong wrong wrong",
            "trollfredo:::what is dis? WRONG",
        ],

        r'random': "trollfredo:::there is no such thing as random",

        r'\\m/': 'rock on, %(nick)s',

        r'((beetle|betel)(geuse|juice)\s?){3}': "beetlejuice:::i'm the ghost with the most",

        r'javascript': 'yo dawg, i heard you like functions',


        # lol, gifs
        r'(bravo|well done)': (imgur('wSvsV'),     # Citizen Kane slow clap
                               imgur('HUKCsCv'),   # Colbert & Stewart bravo
                               imgur('FwqHZ6Z')),  # Gamer conceding defeat

        r'is \w+ down\?': imgur('yX5o8rZ'),  # THE F5 HAMMER

        r"(i don't care|do i look like i care|zero fucks)": (imgur('oKydfNm'),   # Bird bouncing on hawk's head
                                                             imgur('KowlC'),     # Gangam style 'do i look like i care'
                                                             imgur('xYOqXJv')),  # Dog hitting cat with tail

        r'^nope$': (imgur('iSm1aZu'),   # Arrested development NOPE
                    imgur('2xwe756'),   # Lonley island like a boss NOPE
                    imgur('zCtbl'),     # Tracy Morgan NOPE
                    imgur('ErtgS'),     # Spok NOPE button
                    imgur('foEHo'),     # Spongebob buried in sand
                    imgur('xKYs9'),     # Puppy does not like lime
                    imgur('ST9lw3U'),   # Seinfeld I'm Out
                    imgur('c4gTe5p')),  # Cat thriller walk I'm Out

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

        r'(bloody mary|vodka)': imgur('W9SS4iJ'),  # Sterling Archer: Bloody Mary, full of vodka, blessed are you among cocktails

        r'popcorn': (imgur('00IJgSZ'),  # Thriller popcorn
                     imgur('5px9l')),   # Colbert popcorn

        r'deal with it': (imgur('12WoH'),    # Slip n slide DWI
                          imgur('6E6n1'),    # WTF Oprah
                          imgur('hYdy4'),    # Baseball catch deal with it
                          imgur('pqmfX'),    # WTF pouring water from nose
                          imgur('9WbAL'),    # A three toed sloth in a chair
                          imgur('KdldmZk'),  # Polar bear jumping out of water
                          imgur('49UtI5N'),  # The Fresh Prince of DEAL WITH IT
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

        r'\w+ broke prod': imgur('SuCGnum'),  # Anchorman: You ate the whole wheel of cheese?

        r'^indeed$': imgur('bQcbpki'),  # Leonardo DiCaprio in Django Unchained

        r'f(f{6}|7)u(u{11}|12)': 'http://i.minus.com/ibnfJRQi1h4z30.gif',  # Workaholics: FUUUUUUUUUUUUUU


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

    def decompose_response(self, response):
        """
        Decomposes a response into a 'send as' nick and the
        reponse itself
        """
        try:
            parts = response.split(':::')
        except AttributeError:
            # For multiline responses. NOTE: this will probably break if they should nick change
            return self.decompose_response('\n'.join(response))
        else:
            if len(parts) == 2:
                return parts[0], parts[1]
            else:
                return None, parts[0]

    def find_all_matches(self, message):
        match_pat = lambda pat: re.findall(pat, message.message, re.I)
        return [data for pat, data in self.responses.iteritems() if match_pat(pat)]

    def process(self, message):
        matches = self.find_all_matches(message)

        if not matches:
            return

        response = matches[0]

        if hasattr(response, '__iter__'):
            response = random.choice(response)

        newnick, response = self.decompose_response(response)

        if getattr(settings, 'ALLOW_NICK_CHANGE', False) and newnick is not None:
            self.bot.client.setNick(newnick)

        message.response = response
