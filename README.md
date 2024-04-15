# audio-files-scripts
Various scripts for managing of audio files, mostly related to ID3 tags
management.

Warning: I am in progress of documenting and updating these scripts for public
consumption. I would not suggest using them yet.

Currently there are two scripts in this repo:

## Metadata fixer

In [metadata_fixer/ directory](metadata_fixer/).

This one is currently very simple - it updates ID3 tags based on file names and
additional information provided manually during the run.

Planned improvement: use https://musicbrainz.org/doc/MusicBrainz_API for auto
tagging of published music files.


## Podcasts fetcher

In [podcasts_fetcher/ directory](podcasts_fetcher/).

A simple management script for podcasts. It iterates over all subdirectories,
and for the ones containing `PODCAST_METADATA` files it will check for new
episodes and download them, setting ID3 tags based on the information from the
podcast's RSS file.

For each episode, it saves its "ID" as given by the RSS feed, to the ID3 tags to
be able to skip these episodes on subsequent runs.

Example `PODCAST_METADATA` file:
```
{
  "title": "Criminal Records",
  "rss_feed_url": "http://criminalrecords.libsyn.com/rss"
}
```
