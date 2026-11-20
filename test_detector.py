import unittest
import cv2
import numpy as np
from detect_activity import detect, read_image, ROOT


class DetectorTests(unittest.TestCase):
    def test_coordinates_after_scaling(self):
        template = read_image(ROOT / "assets/templates/activity.png")
        frame = np.zeros((1280, 2048, 3), dtype=np.uint8)
        frame[30:102, 1584:1648] = template
        for size, expected in [((2048, 1280), (1584, 30, 64, 72)),
                               ((2560, 1600), (1980, 38, 80, 90))]:
            score, box = detect(cv2.resize(frame, size), template)
            self.assertGreaterEqual(score, 0.85)
            self.assertEqual(box, expected)

    def test_blank_and_wrong_aspect(self):
        template = read_image(ROOT / "assets/templates/activity.png")
        self.assertLess(detect(np.zeros((1280, 2048, 3), np.uint8), template)[0], 0.85)
        with self.assertRaises(ValueError):
            detect(np.zeros((1080, 1920, 3), np.uint8), template)


if __name__ == "__main__":
    unittest.main()
