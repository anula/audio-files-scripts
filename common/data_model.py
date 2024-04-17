"""Various dataclases for defining the data used."""
from dataclasses import dataclass
from collections.abc import Collection


@dataclass(frozen=True)
class Id3Tag:
  label: str
  value: str


@dataclass(frozen=True)
class TagSet:
  tags: Collection[Id3Tag]
