"""Defines abstract class for tags providers.

Tag provider is responsible for:
  * parsing its options from provided command line flags and interactively ask
  the user for missing information
  * based on the provided options, returning a full set of tags to apply for
  a given file
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from anulataggingpkg.common.data_model import TagSet


ArgsType = TypeVar('ArgsType')


class AbstractTagProvider(ABC, Generic[ArgsType]):

  @abstractmethod
  def prepare_context_data(self, args: ArgsType, directory_name: str):
    """Initialize context data needed to decide tags per file.

    The context might be all based on the provided command line arguments but
    it also might interactivelly as user for additional details or fetch them
    from the Internet.
    """
    pass

  @abstractmethod
  def tags_for_file(self, filename: str) -> TagSet:
    pass
