import json
import os
import unittest
from mkvtoolsBridge import (
    MediaFile,
    TrackType,
    statFileAsJSON,
    changeDefaultTrackLanguage,
    changeDefaultTrackLanguageBatch,
)


class TrackTests(unittest.TestCase):
    FILE_PATH = "<PATH_TO_YOUR_MKV_FILE_HERE>"

    def test_createMediaFile(self):
        print()
        fileJson = statFileAsJSON(self.FILE_PATH)

        mf = MediaFile(fileJson)

        self.assertIsNotNone(mf)
        print(mf)

    def test_canChangeTrackLanguage(self):
        print()
        success = changeDefaultTrackLanguage(self.FILE_PATH, "en")
        self.assertTrue(success)

    def test_canFindDefaultTrack(self):
        mf = MediaFile(statFileAsJSON(self.FILE_PATH))

        dTrack: TrackType = None
        for track in mf.tracks:
            if track.type is TrackType.AUDIO:
                if track.isDefaultTrack:
                    dTrack = track
                    break

        self.assertIsNotNone(dTrack)

    def test_canChangeFullDir(self):
        print()
        containingDir = os.path.dirname(self.FILE_PATH)

        failures = changeDefaultTrackLanguageBatch(containingDir, "en")

        self.assertEqual(len(failures), 0)
