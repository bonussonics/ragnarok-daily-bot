import unittest
from unittest.mock import Mock
from run_daily import run_sequence


class DailyTests(unittest.TestCase):
    def test_success_handoff_preserves_foreground_and_reopens_activity(self):
        guild=Mock(return_value={'state':'completed','completion_verified':True,'foreground':123})
        board=Mock(return_value={'state':'completed','completion_verified':True})
        states=[]
        run_sequence(60,guild,board,states.append)
        board.assert_called_once_with(['--run','--timeout','60','--reopen-activity'],expected_foreground=123,start_delay=0)
        self.assertEqual(states,['guild_running','guild_completed_board_running','completed'])

    def test_no_board_after_unverified_or_failed_guild(self):
        for result in (None,{'state':'completed','completion_verified':False}, {'state':'stopped_unverified'}):
            board=Mock()
            with self.assertRaises(RuntimeError):
                run_sequence(60,Mock(return_value=result),board,lambda _:None)
            board.assert_not_called()
        board=Mock()
        with self.assertRaises(RuntimeError):
            run_sequence(60,Mock(side_effect=RuntimeError('cancelled')),board,lambda _:None)
        board.assert_not_called()

    def test_failed_board_cannot_complete_sequence(self):
        states=[]
        with self.assertRaises(RuntimeError):
            run_sequence(60,Mock(return_value={'state':'completed','completion_verified':True,'foreground':123}),
                         Mock(return_value={'state':'stopped_unverified'}),states.append)
        self.assertNotIn('completed',states)
