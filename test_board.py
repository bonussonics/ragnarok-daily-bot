import unittest
import cv2
from unittest.mock import Mock
from run_board import verified_click, BoardStateChanged
from detect_activity import ROOT,read_image
from board_status import board_state

class BoardTests(unittest.TestCase):
    def test_live_completed_card_and_neighbor_isolation(self):
        f=read_image(ROOT/'tests/fixtures/board_completed_live.png')
        for size in ((2048,1280),(2560,1600)):
            self.assertEqual(board_state(cv2.resize(f,size))['state'],'completed')
        # Guild/Cat Cargo remain completed nearby. Their evidence must never
        # substitute for missing Board evidence in the same card.
        for x,y,r,b in ((760,510,920,560),(850,625,1010,675),(1120,565,1250,680)):
            damaged=f.copy(); damaged[y:b,x:r]=0
            self.assertNotEqual(board_state(damaged)['state'],'completed')

    def test_scrolling_confirmation_label_and_missing_button(self):
        for name in ('board_after_start.png','board_workflow_last.png'):
            f=read_image(ROOT/f'tests/fixtures/board_scroll_{name}')
            for size in ((2048,1280),(2560,1600)):
                state=board_state(cv2.resize(f,size))
                self.assertEqual(state['state'],'confirm')
                x,y,w,h=state['box']
                self.assertAlmostEqual((x+w/2)/size[0],1273/2048,delta=.003)
            for region in ((810,970,1020,1510),(285,410,790,1260),(510,700,550,1500)):
                damaged=f.copy(); y,b,x,r=region; damaged[y:b,x:r]=0
                self.assertNotEqual(board_state(damaged)['state'],'confirm')

    def test_transient_state_reobserved_before_one_click(self):
        good=(.99,(1080,840,390,114))
        detector=Mock(side_effect=[good,BoardStateChanged(),good,good])
        send=Mock()
        verified_click(detector,Mock(),Mock(),Mock(),send)
        send.assert_called_once_with(1275,897)

    def test_unstable_state_and_guard_failure_never_click(self):
        send=Mock()
        with self.assertRaises(BoardStateChanged):
            verified_click(Mock(side_effect=BoardStateChanged()),Mock(),Mock(),Mock(),send)
        send.assert_not_called()
        with self.assertRaisesRegex(RuntimeError,'Foreground'):
            verified_click(Mock(return_value=(.99,(1080,840,390,114))),Mock(),Mock(),
                           Mock(side_effect=RuntimeError('Foreground changed')),send)
        send.assert_not_called()

    def test_observations_and_physical_click_coordinates(self):
        for state in ('start','confirm','pending','completed'):
            f=read_image(ROOT/f'tests/fixtures/board_{state}.png')
            base=board_state(f)
            self.assertEqual(base['state'],state)
            large=board_state(cv2.resize(f,(2560,1600)))
            self.assertEqual(large['state'],state)
            if 'box' in base:
                self.assertTrue(all(abs(a*1.25-b)<=2 for a,b in zip(base['box'],large['box'])))

    def test_missing_confirmation_body_prevents_click(self):
        f=read_image(ROOT/'tests/fixtures/board_confirm.png')
        f[510:700,550:1500]=0
        self.assertNotIn(board_state(f)['state'],('start','confirm'))

    def test_completion_requires_count_and_check(self):
        for box in [(250,415,425,485),(520,350,650,480)]:
            f=read_image(ROOT/'tests/fixtures/board_completed.png')
            x,y,r,b=box;f[y:b,x:r]=0
            self.assertNotEqual(board_state(f)['state'],'completed')

    def test_wrong_aspect_rejected(self):
        f=read_image(ROOT/'tests/fixtures/board_start.png')
        with self.assertRaises(ValueError):board_state(cv2.resize(f,(1920,1080)))

if __name__=='__main__':unittest.main()
