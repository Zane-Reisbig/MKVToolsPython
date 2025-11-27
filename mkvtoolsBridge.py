from enum import Enum
import json
import re
import subprocess
from typing import List, Optional, Dict, Any
import os


class MediaFileParseException(Exception):
    def __init__(self, msg: str, *args):
        super().__init__(msg, *args)


class FailedToFindRequestedLanguageException(Exception):
    def __init__(self, msg: str, *args):
        super().__init__(msg, *args)


# fmt: off
class TrackType(Enum):
    VIDEO = 0
    AUDIO = 1
    SUB   = 2
    OTHER = 3

    @staticmethod
    def stringToTrack(string: str):
        match string.upper():
            case "AUDIO":
                return TrackType.AUDIO
            case "VIDEO":
                return TrackType.VIDEO
            case "SUB":
                return TrackType.SUB
            case _:
                return TrackType.OTHER

# fmt: on


class Track:
    codec: str = None
    id: int = None
    trackType: str
    properties: dict[str, Any]

    def __init__(self, codec: str, id: int, properties: Dict[str, Any], type: str):
        self.codec = codec
        self.id = id
        self.properties = properties
        self.type = TrackType.stringToTrack(type)

    @property
    def isDefaultTrack(self):
        return self.properties.get("default_track", False)

    @property
    def language(self):
        return self.properties.get("language", None)

    @property
    def ietfLanguage(self):
        return self.properties.get("language_ietf", None)

    def __repr__(self):
        return (
            f"Track(id={self.id}, type={self.type.name}, codec={self.codec}, "
            f"language={self.language}, default={self.isDefaultTrack})"
        )


class AudioTrack(Track):
    audio_channels: int = None
    audio_sampling_frequency: int

    def __init__(self, codec: str, id: int, properties: Dict[str, Any]):
        super().__init__(codec, id, properties, "audio")
        self.audio_channels = properties.get("audio_channels")
        self.audio_sampling_frequency = properties.get("audio_sampling_frequency")


class VideoTrack(Track):
    def __init__(self, codec: str, id: int, properties: Dict[str, Any]):
        super().__init__(codec, id, properties, "video")
        self.display_dimensions = properties.get("display_dimensions")
        self.pixel_dimensions = properties.get("pixel_dimensions")


class MediaFile:
    def __init__(self, data: Dict[str, Any]):
        self.file_name = data.get("file_name")
        self.container = data.get("container")
        self.chapters = data.get("chapters", [])
        self.tracks: List[Track] = []
        for t in data.get("tracks", []):
            if t["type"] == "audio":
                self.tracks.append(AudioTrack(t["codec"], t["id"], t["properties"]))
            elif t["type"] == "video":
                self.tracks.append(VideoTrack(t["codec"], t["id"], t["properties"]))
            else:
                self.tracks.append(
                    Track(t["codec"], t["id"], t["properties"], t["type"])
                )

        self.errors = data.get("errors", [])
        self.warnings = data.get("warnings", [])
        self.identification_format_version = data.get("identification_format_version")
        self.attachments = data.get("attachments", [])
        self.global_tags = data.get("global_tags", [])
        self.track_tags = data.get("track_tags", [])


def statFileAsJSON(absFilePath: str, output: bool = False):
    output = subprocess.getoutput(f'mkvmerge -J "{absFilePath}"')

    startIndex = output.find("{")
    endIndex = output.rfind("}") + 1

    if startIndex == -1:
        raise Exception("Failed to find valid json object")

    jsonBlob = output[startIndex:endIndex]

    if output:
        with open("./output.json", "w") as f:
            f.write(jsonBlob)

    return json.loads(jsonBlob)


def changeDefaultTrackLanguage(
    absFilePath: str, requestedLanguage: str, force: bool = True
):
    sep = "=============================="

    ourFile: MediaFile = None
    try:
        ourFile = MediaFile(statFileAsJSON(absFilePath))
    except:
        raise MediaFileParseException(
            f"Failed to read/parse file {repr(absFilePath)} as MediaFile"
        )

    dTrack: AudioTrack = None
    requestedLanguageTrack: AudioTrack = None
    for track in ourFile.tracks:
        if track.type is TrackType.AUDIO:
            if track.isDefaultTrack:
                dTrack = track

            if (
                track.language == requestedLanguage
                or track.ietfLanguage == requestedLanguage
            ):
                requestedLanguageTrack = track

            if dTrack is not None and requestedLanguageTrack is not None:
                break

    if requestedLanguageTrack is None:
        raise FailedToFindRequestedLanguageException(
            f"Failed to find requested language \"{requestedLanguage}\" in 'language' or 'language_ietf' fields!"
        )

    print(f"Default Track -> { repr(dTrack) }")
    print(f"    New Track -> { repr(requestedLanguageTrack) }")
    print()

    # fmt: off
    command = (
        f'mkvpropedit "{absFilePath}"'
        f" --edit track:a{dTrack.id} --set flag-default=0"
        f" --edit track:a{requestedLanguageTrack.id} --set flag-default=1"
    )
    if force:
        command = command + (
            f" --edit track:a{requestedLanguageTrack.id} --set flag-forced=1"
        )

    # fmt: on

    print(f"> {repr(command)}")
    print()

    output = subprocess.getoutput(command)
    print(output)
    print()

    return "Done" in output


def changeDefaultTrackLanguageBatch(absDirectoryPath: str, requestedLang: str):
    """
    returns filepaths of files that failed to be processed,
    I.E. "len(failures) == 0" means success
    """

    failures = []

    for root, _, files in os.walk(absDirectoryPath):
        for file in files:
            if file.lower().endswith(".mkv"):
                file_path = os.path.join(root, file)
                try:
                    changeDefaultTrackLanguage(file_path, requestedLang)
                except Exception as e:
                    failures.append(file_path)
                    print(f"Failed to process {file_path}: {e}")

    return failures


# Usage:
# import json
# with open("yourfile.json") as f:
#     data = json.load(f)
# media_file = MediaFile(data)
