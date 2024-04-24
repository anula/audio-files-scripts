# A small utility to download new episodes of specified podcasts and tag
# them accordingly.
import argparse
import click  # pytype: disable=import-error
import feedparser  # pytype: disable=import-error
import json
import logging
import mutagen  # pytype: disable=import-error
import os
import re
import requests
import taglib  # pytype: disable=import-error
import time
import urllib
import xmltodict

from dataclasses import dataclass
from typing import List, Optional


ID_TAG_NAME = 'RSS_ID'

PODCAST_METADATA_FILENAME = 'PODCAST_METADATA'


@dataclass
class EpisodeMetadata:
  title: str
  artist: str
  album: str
  id: str
  download_link: str
  cover_art_link: Optional[str]
  creation_date: str
  genre: str = 'podcast'


@dataclass
class PodcastMetadata:
  title: str = ''
  rss_feed_url: str = ''
  podcast_dir: str = ''


REQUIRED_METADATA_FIELDS = ['title', 'rss_feed_url']


def get_all_files_in_path(path):
  return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]


def get_all_existing_ids(path: str) -> set[str]:
  ids = set()
  for file in get_all_files_in_path(path):
    file = os.path.join(path, file)
    try:
      with taglib.File(file) as episode:
        if episode.tags.get(ID_TAG_NAME, None):
          ids.add(episode.tags[ID_TAG_NAME][0])
    except OSError as err:
      logging.info(f'\nIgnoring {repr(path)} because of {repr(err)}')
      continue
  return ids


def parse_rss_item(feed: feedparser.util.FeedParserDict, rss_item:
                   feedparser.util.FeedParserDict) -> Optional[EpisodeMetadata]:
  if not rss_item.enclosures:
    return None
  if not rss_item.enclosures[0].type.startswith('audio'):
    return None
  image = None
  if 'image' in rss_item.keys():
    image = rss_item.image
  return EpisodeMetadata(
    title=rss_item.title,
    artist=feed.author,
    album=feed.title,
    id=rss_item.id,
    download_link=rss_item.enclosures[0].href,
    cover_art_link=image,
    creation_date=time.strftime('%Y-%m-%d', rss_item.published_parsed),
  )


# Workaround for taglib printing errors on unrecognized tags.
# https://stackoverflow.com/questions/5944370/taglib-errors-warnings
def remove_existing_tags(filename: str):
  f = mutagen.File(filename)
  f.delete()
  f.save()


def fix_episode_metadata(filename: str, metadata: EpisodeMetadata):
  new_tags = {
    'TITLE': [metadata.title],
    'ARTIST': [metadata.artist],
    'ALBUM': [metadata.album],
    ID_TAG_NAME: [metadata.id],
    'DATE': [metadata.creation_date],
    'GENRE': [metadata.genre],
  }
  with taglib.File(filename, save_on_exit=True) as episode:
    episode.tags = new_tags


NON_FILENAME_CHAR_RE = re.compile('[^a-zA-Z0-9 ._-]')


def escape_filename(filename: str) -> str:
  return re.sub(NON_FILENAME_CHAR_RE, '_', filename)


def download_episode(episode: EpisodeMetadata, working_dir: str):
  # DIFFERENCE! removed date from title
  filenamebase = escape_filename(f'{episode.title}')
  filepath = os.path.join(working_dir, filenamebase + '.mp3')
  filepath_inprogress = os.path.join(
    working_dir, filenamebase + '.inprogress.mp3')
  urllib.request.urlretrieve(episode.download_link, filepath_inprogress)
  remove_existing_tags(filepath_inprogress)
  fix_episode_metadata(filepath_inprogress, episode)
  os.rename(filepath_inprogress, filepath)


def download_missing_episodes(
    rss_feed, existing_ids: set[str], working_dir: str):
  to_download = []
  for entry in rss_feed.entries:
    episode = parse_rss_item(rss_feed.feed, entry)
    if not episode:
      continue
    if episode.id in existing_ids:
      continue
    to_download.append(episode)

  print(f'Downloading {len(to_download)} episodes...')
  with click.progressbar(to_download) as episodes:
    for episode in episodes:
      download_episode(episode, working_dir)


# Workaround for https://github.com/kurtmckee/feedparser/issues/316
def fix_feed_metadata(feed: feedparser.util.FeedParserDict, rss_url: str):
  resp = requests.get(rss_url)
  raw_xml = xmltodict.parse(resp.content)
  feed.author = raw_xml['rss']['channel']['itunes:author']


# Download episodes for a given podcast
def process_podcast(metadata: PodcastMetadata):
  print(f'Working on "{metadata.title}"...')
  rss_feed = feedparser.parse(metadata.rss_feed_url)
  fix_feed_metadata(rss_feed.feed, metadata.rss_feed_url)
  existing_ids = get_all_existing_ids(metadata.podcast_dir)
  download_missing_episodes(rss_feed, existing_ids, metadata.podcast_dir)


# Returns None if podcast_dir contains no or incorrect podcast metadata file.
def parse_metadata(podcast_dir: str) -> Optional[PodcastMetadata]:
  metadata_file = os.path.join(podcast_dir, PODCAST_METADATA_FILENAME)
  try:
    with open(metadata_file) as meta_file:
      metadata_parsed = json.load(meta_file)
      metadata = PodcastMetadata()
      for field in REQUIRED_METADATA_FIELDS:
        setattr(metadata, field, metadata_parsed[field])

      metadata.podcast_dir = podcast_dir
      return metadata
  except FileNotFoundError:
    return None
  except json.decoder.JSONDecodeError as err:
    logging.warning(
      f'Failed to parse "{metadata_file}" as metadata. Error: {err}')
    return None
  except KeyError as err:
    logging.warning(f'File "{metadata_file}" missing required key: {err}.')
    return None


def list_podcasts(working_dir: str) -> List[PodcastMetadata]:
  podcasts = []
  for d in os.listdir(working_dir):
    if not os.path.isdir(d):
      continue
    meta = parse_metadata(d)
    if meta:
      podcasts.append(meta)

  return podcasts


parser = argparse.ArgumentParser(
  prog='PodcastDownloader',
  description='Download new episodes and fix their metadata')
parser.add_argument('-d', '--working_dir', type=str,
                    default='.',
                    help='Catalog to be searched for subdirs with podcasts')


def main():
  args = parser.parse_args()

  podcasts = list_podcasts(args.working_dir)
  if not podcasts:
    print('Found no podcasts in the given directory')
    return

  print('Found the following podcasts:')
  for idx, podcast in enumerate(podcasts):
    print(f'  [{idx}] {podcast.title}')

  print('What podcasts to work on? [no=cancel/empty=all]: ')
  resp = input().strip().lower()
  if resp == 'no':
    print('Cancelling...')
    return
  to_process = []
  if resp == '' or resp == 'all':
    to_process = list(range(len(podcasts)))
  else:
    for num in resp.split(','):
      try:
        to_process.append(int(num.strip()))
      except ValueError as err:
        logging.warning(f'{err}')

  if not to_process:
    print('No podcasts to process, cancelling...')
    return

  for idx in to_process:
    process_podcast(podcasts[idx])


if __name__ == "__main__":
  main()
