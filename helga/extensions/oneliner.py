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
        r'(gross|disgusting|eww)': (imgur('XEEI0Rn'),),

        r'(GFY|GTFO|Fuck (You|Off))': (imgur('VPqgYjF'),),

        r'womp womp': ("http://www.sadtrombone.com/?play=true",
                       "http://www.youtube.com/watch?v=_-GaXa8tSBE"),

        r'^:w?q': ("this ain't your vi",
                   "this ain't your vi, but at least you're not using emacs"),

        r'^((sudo|ls|cd|rm)( .+)?|pwd)': "%(nick)s, this ain't your shell",

        r'php': ("php is just terrible",
                 "MERGE ALL THE PULL REQUESTS"),

        r'^select( .* )from(.*)': "'; DROP TABLES;",

        r'mongo(db)?': 'http://youtu.be/b2F-DItXtZs',

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
        r'(bravo|well done)': (imgur('wSvsV'),
                               imgur('HUKCsCv'),
                               imgur('FwqHZ6Z')),

        r'is \w+ down\?': imgur('yX5o8rZ'),  # THE F5 HAMMER

        r"(i don't care|do i look like i care|zero fucks)": (imgur('oKydfNm'),
                                                             imgur('KowlC'),
                                                             imgur('xYOqXJv')),

        r'^nope$': (imgur('iSm1aZu'),
                    imgur('2xwe756'),
                    imgur('zCtbl'),
                    imgur('ErtgS'),
                    imgur('foEHo'),
                    imgur('xKYs9'),
                    imgur('ST9lw3U'),
                    imgur('c4gTe5p')),

        r'tl;?dr': (imgur('dnMjc'),
                    imgur('V2H9y')),

        r'panic': (imgur('tpGQV'),
                   imgur('Jz2Iu'),
                   imgur('WS4S2'),
                   imgur('rhNOy3I'),
                   imgur('SNvM6CZ'),
                   imgur('H7PXV'),
                   imgur('fH9e2')),

        r'shock(ed|ing)?': (imgur('zVyOBlR'),
                            imgur('Q4bI5'),
                            imgur('wdA2Z'),
                            imgur('nj3yp'),
                            imgur('AGnOQ'),
                            imgur('wkY1FUI'),
                            imgur('AXuUYIj')),

        r'(bloody mary|vodka)': imgur('W9SS4iJ'),

        r'popcorn': (imgur('00IJgSZ'),
                     imgur('5px9l')),

        r'deal with it': (imgur('12WoH'),
                          imgur('6E6n1'),
                          imgur('hYdy4'),
                          imgur('pqmfX'),
                          imgur('9WbAL'),
                          imgur('KdldmZk'),
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

        r'(mind blown|blew my mind)': (imgur('U6kCXUp'),
                                       imgur('1HMveGj')),

        r'(sweet jesus|mother of god)': (imgur('5vXdAOV'),
                                         imgur('g155Wra'),
                                         imgur('dyeHb'),
                                         imgur('VkHiG6D'),
                                         imgur('aiH4Mts'),
                                         imgur('nOJme'),
                                         imgur('KtdHWhs'),
                                         imgur('z5hhSsU'),
                                         imgur('zuc9tAm')),

        r'nailed it': (imgur('KsQzQTF'),
                       imgur('5nrEk'),
                       imgur('n9zw0'),
                       imgur('puZy04m'),
                       imgur('MBdxv'),
                       imgur('6XRqt'),
                       imgur('dFuBE'),
                       imgur('vUACp'),
                       imgur('59h9A8e')),

        r'unacceptable': imgur('BwdP2xl'),

        r'^(iknorite|right)\?$': imgur('RvquHs0'),

        r'fuck yea': (imgur('GZ5CD5r'),
                      imgur('nEmrMkq')),

        r'\w+ broke prod': imgur('SuCGnum'),

        r'^indeed$': imgur('bQcbpki'),

        r'f(f{6}|7)u(u{11}|12)': 'http://i.minus.com/ibnfJRQi1h4z30.gif',


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
