import argparse
import click  # pytype: disable=import-error
import taglib  # pytype: disable=import-error
import os
import re


def apply_tags(
    path, artist, album, title, tracknumber, confirm=False, verbose=False):
  update_tags = {
    'ALBUM': [album],
    'TITLE': [title],
  }
  if artist:
    update_tags['ARTIST'] = [artist]
  if tracknumber:
    update_tags['TRACKNUMBER'] = [str(tracknumber)]

  if confirm:
    print(f'\nFile {repr(path)}:')

  try:
    with taglib.File(path, save_on_exit=True) as song:
      update = True
      if confirm:
        print(f'  Original tags: {song.tags}')
        print(f'  Proposed changes: {update_tags}')
        update = click.confirm(f'Update file {repr(path)}?')

      if update:
        song.tags.update(update_tags)

    if verbose:
      print(f'\nTags for {repr(path)} are now:')
      with taglib.File(path) as song:
        print(f'  {song.tags}')
  except OSError as err:
    print(f'\nIgnoring {repr(path)} because of {repr(err)}')


def get_all_files_in_path(path):
  return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]


TRACK_NO_RE = re.compile(r'Track ([0-9]+)\.(wav|mp3)')
TITLE_NO_RE = re.compile(r'(?P<no>[0-9]+)(\.| -)? (?P<name>.+)\.(wav|mp3)')


# Return track no
def parse_track_no(filename):
  m = TRACK_NO_RE.match(filename)
  if m:
    return int(m.group(1))
  m = TITLE_NO_RE.match(filename)
  if m:
    return int(m.group('no'))
  return None


# Return title
def parse_title(filename):
  m = TITLE_NO_RE.match(filename)
  if m:
    return m.group('name')
  return os.path.splitext(filename)[0]


def get_all_dirs_in_path(path):
  return [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]


parser = argparse.ArgumentParser(
    prog='FixMetadata',
    description='Fix metadata of tracks for violin')
parser.add_argument('-c', '--confirm_each_file', action='store_true',
                    default=False)
parser.add_argument('-v', '--verbose', action='store_true', default=False)
parser.add_argument('-d', '--directories', nargs='+', default=None)


def main():
  args = parser.parse_args()

  if not args.directories:
    dirs = get_all_dirs_in_path('.')
  else:
    dirs = args.directories

  for d in dirs:
    if not click.confirm(f'Work on directory {repr(d)}?', default=True):
      continue

    artist = click.prompt('What artist to use? [empty for None]', default='',
                          show_default=False)
    if not artist:
      artist = None

    files = get_all_files_in_path(d)

    with click.progressbar(files) as filenames:
      for filename in filenames:
        file_path = os.path.join(d, filename)
        title = parse_title(filename)
        tracknumber = parse_track_no(filename)
        apply_tags(
          path=file_path,
          artist=artist,
          album=d,
          title=title,
          tracknumber=tracknumber,
          confirm=args.confirm_each_file,
          verbose=args.verbose,
        )


if __name__ == "__main__":
  main()
