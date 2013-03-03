from mock import Mock, patch
from unittest import TestCase

from helga.extensions.operator import OperatorExtension
from helga.tests.util import mock_bot


class OperatorExtensionTestCase(TestCase):

    def setUp(self):
        self.oper = OperatorExtension(mock_bot())

    def test_handle_message_exits_for_non_operator(self):
        msg = Mock(response=None)
        self.oper.is_operator = Mock(return_value=False)
        self.oper.handle_message(None, msg)

        assert msg.response in self.oper.nopes

    def test_handle_message_does_nothing(self):
        msg = Mock(response=None)
        self.oper.is_operator = Mock(return_value=True)
        self.oper.handle_message({'autojoin': False}, msg)

        assert msg.response is None

    @patch('helga.extensions.operator.db')
    def test_add_autojoin_exists(self, db):
        db.autojoin.find.return_value = db
        db.count.return_value = 1
        ret = self.oper.add_autojoin('foo')

        assert ret not in self.oper.acks

    @patch('helga.extensions.operator.db')
    def test_add_autojoin_adds(self, db):
        db.autojoin.find.return_value = db
        db.count.return_value = 0
        self.oper.add_autojoin('foo')

        db.autojoin.insert.assertCalledWith({'channel': 'foo'})

    @patch('helga.extensions.operator.db')
    def test_remove_autojoin(self, db):
        self.oper.remove_autojoin('foo')

        db.autojoin.remove.assertCalledWith({'channel': 'foo'})
