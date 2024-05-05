from dataclasses import dataclass

from anulataggingpkg.tags_fixer.abstract_tags_provider import AbstractTagProvider


@dataclass(frozen=True)
class ManualTagsProviderArgs:
  """Arguments for ManualTagsProvider.

  ManualTagsProvider sets the following tags:
    - artist, based on the value provided in flags or during runtime
    - album, based on the immediate parent directory name. Can be overwritten
    with a flag
    - title, based on file name of the track (without extension)
    - track number, optionally, tries to extract it from track number
  """

  artist: str | None
  """Artist to use for all encountered music files.
  Will be asked for if left empty.
  """

  album: str | None
  """Album to use for all encountered music files.
  Will default to the immediate parent directory name if left empty.
  """

  guess_track_number: bool = False
  """When True, tries to extract track numbers from file names.
  Does not set track numbers otherwise.
  """


class ManualTagsProvider(AbstractTagProvider[ManualTagsProviderArgs]):
  pass
