from mock import Mock
from unittest import TestCase

from helga import settings
from helga.extensions.facts import FactExtension


_helga = Mock()
_helga.nick = 'helga'

settings.DISABLE_AUTOBOT = True


class FactExtensionTestCase(TestCase):

    def setUp(self):
        self.facts = FactExtension()
