import unittest
from unittest.mock import Mock,patch
import cv2
from detect_activity import ROOT,read_image
from guild_accept import observe
from window_guard import require_foreground

class GuildNpcTests(unittest.TestCase):
    def test_new_npc_and_missing_identity(self):
        f=read_image(ROOT/'tests/fixtures/guild_npc_talk.png')
        self.assertEqual(observe(f)[0],'talk')
        self.assertEqual(observe(cv2.resize(f,(2560,1600)))[0],'talk')
        f[710:740,960:1100]=0
        self.assertEqual(observe(f)[0],'unknown')

    def test_yellow_name_requires_guild_scene_and_talk(self):
        f=read_image(ROOT/'tests/fixtures/guild_npc_talk_variant.png')
        for width,height in [(2048,1280),(2560,1600)]:
            self.assertEqual(observe(cv2.resize(f,(width,height)))[0],'talk')
        for y1,y2,x1,x2 in [(0,100,1750,1980),(710,750,960,1100),(650,750,1150,1400)]:
            missing=f.copy();missing[y1:y2,x1:x2]=0
            self.assertEqual(observe(missing)[0],'unknown')

    def test_camera_rotation_and_activity_routing(self):
        from run_guild import should_open_activity
        f=read_image(ROOT/'tests/fixtures/guild_npc_camera.png')
        for size in [(2048,1280),(2560,1600)]:
            self.assertEqual(observe(cv2.resize(f,size))[0],'talk')
        for roi in [(1100,830,1280,900),(1750,0,1980,100),(1150,650,1400,750)]:
            x,y,r,b=roi; missing=f.copy();missing[y:b,x:r]=0
            self.assertEqual(observe(missing)[0],'unknown')
        self.assertFalse(should_open_activity(False,False,False,{'talk_score':.94}))
        self.assertTrue(should_open_activity(False,False,False,{'talk_score':.4}))
        self.assertFalse(should_open_activity(True,False,False,{'talk_score':.4}))

    def test_live_dialog_callback_and_stable_target(self):
        from run_guild import dialog_detector
        from open_activity import stable_target
        frame=read_image(ROOT/'tests/fixtures/guild_npc_camera.png')
        detector=dialog_detector('talk')
        first=detector(frame);second=detector(frame)
        self.assertEqual(len(stable_target(first,second)),2)
        with self.assertRaises(RuntimeError): dialog_detector('confirm')(frame)
        with patch('run_guild.observe',return_value=('confirm',(.96,(1400,800,100,40)))):
            self.assertEqual(dialog_detector('confirm')(frame),(.96,(1400,800,100,40)))

    def test_focus_recovers_only_to_original_window(self):
        u=Mock();u.GetForegroundWindow.side_effect=[22,11];u.GetAsyncKeyState.return_value=0
        with patch('window_guard.time.sleep'):
            require_foreground(u,11,Mock())

    def test_unrelated_window_stops(self):
        u=Mock();u.GetForegroundWindow.return_value=22
        with patch('window_guard.window_info',return_value='other'):
            with self.assertRaises(RuntimeError):require_foreground(u,11,Mock(),grace=0)
