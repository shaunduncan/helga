# -*- coding: utf8 -*-
import random
import re

from helga import settings
from helga.extensions.base import HelgaExtension
from helga.log import setup_logger


logger = setup_logger(__name__)


class OneLinerExtension(HelgaExtension):
    """
    Maybe some of these will become their own thing, but for
    now, they live here.

    DEAL WITH IT
    """

    responses = {
        r'^:.+': [
            "%(nick)s, this ain't your vi",
            "this ain't your vi, but at least you're not using emacs, %(nick)s"
        ],

        r'^((sudo|ls|cd|rm)( .+)?|pwd)': [
            "%(nick)s, this ain't your shell"
        ],

        r'php': [
            "php is just terrible",
            "MERGE ALL THE PULL REQUESTS"
        ],

        r'^select( .* )from(.*)': [
            "'; DROP TABLES;"
        ],

        r'mongo(db)?': [
            'http://youtu.be/b2F-DItXtZs',
        ],

        r'(ruby\s?gem|gem install)': [
            "%(nick)s, don't. just don't",
        ],

        r'^(logger|logs)\?$': [
            "http://logger.ddtc.cmgdigital.com/%(norm_channel)s"
        ],

        r'^docs\?$': [
            'http://docs.cmgdigital.com/'
        ],

        r'alfredo(deza)?': [
            "trollfredo:::everything you are doing is wrong",
            "trollfredo:::if you aren't using zsh, %(nick)s, you are doing it wrong",
            "trollfredo:::you are wrong %(nick)s",
            "trollfredo:::i have a vim plugin that shows you how wrong you are",
            "trollfredo:::i can't believe how wrong you are",
            "trollfredo:::wrong wrong wrong",
            "trollfredo:::what is dis? WRONG",
        ],

        r'random': [
            "trollfredo:::there is no such thing as random"
        ],

        r'(bravo|well done)': [
            'http://i.imgur.com/wSvsV.gif',
            'http://i.imgur.com/4f6SDaO.gif'
        ],

        r'((beetle|betel)(geuse|juice)\s?){3}': [
            "beetlejuice:::i'm the ghost with the most"
        ],

        r'(is )?(jira|medley) (is )?down': [
            'http://i.imgur.com/yX5o8rZ.gif'
        ],

        r"(i don't care|do i look like i care|whatever)": [
            'http://i.imgur.com/KowlC.gif'
        ],

        r'^nope$': [
            'http://i.imgur.com/2xwe756.gif',
            'http://i.imgur.com/zCtbl.gif',
            'http://i.imgur.com/ErtgS.gif',
            'http://i.imgur.com/foEHo.gif',
            'http://i.imgur.com/xKYs9.gif',
            'http://i.imgur.com/ST9lw3U.gif',
            'http://i.imgur.com/c4gTe5p.gif',
        ],

        r'tl;?dr': [
            'http://i.imgur.com/dnMjc.gif',
            'http://i.imgur.com/V2H9y.gif',
        ],

        r'panic': [
            'http://i.imgur.com/tpGQV.gif',
            'http://i.imgur.com/Jz2Iu.gif',
            'http://i.imgur.com/WS4S2.gif',
            'http://i.imgur.com/rhNOy3I.gif',
            'http://i.imgur.com/SNvM6CZ.gif',
            'http://i.imgur.com/H7PXV.gif',
            'http://i.imgur.com/fH9e2.gif'
        ],

        r'shock(ed|ing)?': [
            'http://i.imgur.com/zVyOBlR.gif',
            'http://i.imgur.com/Q4bI5.gif',
            'http://i.imgur.com/wdA2Z.gif',
            'http://i.imgur.com/nj3yp.gif',
            'http://i.imgur.com/AGnOQ.gif',
            'http://i.imgur.com/wkY1FUI.gif',
            'http://i.imgur.com/AXuUYIj.gif',
        ],

        r'(bloody mary|vodka)': [
            'http://i.imgur.com/W9SS4iJ.gif'
        ],

        r'popcorn': [
            'http://i.imgur.com/00IJgSZ.gif',
            'http://i.imgur.com/5px9l.gif'
        ],

        r'deal with it': [
            'http://i.imgur.com/12WoH.gif',
            'http://i.imgur.com/6E6n1.gif',
            'http://i.imgur.com/hYdy4.gif',
            'http://i.imgur.com/pqmfX.gif',
            'http://i.imgur.com/9WbAL.gif',
            'http://i.imgur.com/KdldmZk.gif',
            u'(⌐■_■)',
        ],

        r'(mind blown|blew my mind)': [
            'http://i.imgur.com/1HMveGj.gif'
        ],

        r'(sweet jesus|mother of god)': [
            'http://i.imgur.com/5vXdAOV.gif',
            'http://i.imgur.com/g155Wra.gif',
            'http://i.imgur.com/dyeHb.gif',
            'http://i.imgur.com/VkHiG6D.gif',
            'http://i.imgur.com/aiH4Mts.gif',
            'http://i.imgur.com/nOJme.gif',
        ],

        r'nailed it': [
            'http://i.imgur.com/KsQzQTF.gif',
            'http://i.imgur.com/5nrEk.gif',
        ],

        r'unacceptable': [
            'http://i.imgur.com/BwdP2xl.gif',
        ],

        r'javascript': [
            'yo dawg, i heard you like functions',
        ],

        r'^(iknorite|right)\?$': [
            'http://i.imgur.com/RvquHs0.gif',
        ],

        # Various modern unicode emoticons
        r'(why|y) (u|you) no':                  [u'ლ(ಠ益ಠლ)'],
        r'i (don\'?t know|dunno),? lol':        [u'¯\(°_o)/¯'],
        r'look.?of.?disapproval(\.jpg|\.gif)?': [u'ಠ_ಠ'],
        r'i disapprove':                        [u'ಠ_ಠ'],
        r'^not sure if \w+':                    [u'ﺟ_ﺟ', u'≖_≖'],
        r'flip (a|the|some) tables?':           [u'(╯°□°）╯︵ ┻━┻', u'(ノಠ益ಠ)ノ彡┻━┻'],
        r'(gonna|going to) (make \w+ )?cry':    [u'(ಥ﹏ಥ)'],
        r'(bro ?fist|fist ?bump)':              [u'( _)=mm=(^_^ )'],
        r'hi(gh)?[ -]?five':                    ['\o', u'( ‘-’)人(ﾟ_ﾟ )'],
        r'(^|[^\])o/$':                         ['\o'],
        r'^\o$':                                ['o/'],
    }

    def decompose_response(self, response):
        """
        Decomposes a response into a 'send as' nick and the
        reponse itself
        """
        parts = response.split(':::')
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            return None, parts[0]

    def dispatch(self, nick, channel, message, is_public):
        for pat, responses in self.responses.iteritems():
            if not re.findall(pat, message, re.I):
                continue

            resp = random.choice(responses)
            newnick, resp = self.decompose_response(resp)

            if getattr(settings, 'ALLOW_NICK_CHANGE', False) and newnick is not None:
                self.bot.client.setNick(newnick)

            return resp
