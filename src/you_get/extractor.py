#!/usr/bin/env python
import json
import os
import sys

from . import json_output
from .common import download_urls, dry_run, get_filename, maybe_print, parse_host, player, \
    print_more_compatible as print, set_proxy, unset_proxy
from .util import log


class Extractor():
    def __init__(self, *args):
        self.url = None
        self.title = None
        self.vid = None
        self.streams = {}
        self.streams_sorted = []

        if args:
            self.url = args[0]

class VideoExtractor():
    def __init__(self, *args):
        self.url = None
        self.title = None
        self.vid = None
        self.m3u8_url = None
        self.streams = {}
        self.streams_sorted = []
        self.audiolang = None
        self.password_protected = False
        self.dash_streams = {}
        self.caption_tracks = {}
        self.out = False
        self.ua = None
        self.referer = None
        self.danmaku = None
        self.lyrics = None

        self.data = {}

        if args:
            self.url = args[0]

    def download_by_url(self, url, **kwargs):
        self.url = url
        self.vid = None

        if 'extractor_proxy' in kwargs and kwargs['extractor_proxy']:
            set_proxy(parse_host(kwargs['extractor_proxy']))
        self.prepare(**kwargs)
        if self.out:
            return
        if 'extractor_proxy' in kwargs and kwargs['extractor_proxy']:
            unset_proxy()

        try:
            self.streams_sorted = [dict([('id', stream_type['id'])] + list(self.streams[stream_type['id']].items())) for stream_type in self.__class__.stream_types if stream_type['id'] in self.streams]
        except:
            self.streams_sorted = [dict([('itag', stream_type['itag'])] + list(self.streams[stream_type['itag']].items())) for stream_type in self.__class__.stream_types if stream_type['itag'] in self.streams]

        self.extract(**kwargs)

        self.download(**kwargs)

    def download_by_vid(self, vid, **kwargs):
        self.url = None
        self.vid = vid

        if 'extractor_proxy' in kwargs and kwargs['extractor_proxy']:
            set_proxy(parse_host(kwargs['extractor_proxy']))
        self.prepare(**kwargs)
        if 'extractor_proxy' in kwargs and kwargs['extractor_proxy']:
            unset_proxy()

        try:
            self.streams_sorted = [dict([('id', stream_type['id'])] + list(self.streams[stream_type['id']].items())) for stream_type in self.__class__.stream_types if stream_type['id'] in self.streams]
        except:
            self.streams_sorted = [dict([('itag', stream_type['itag'])] + list(self.streams[stream_type['itag']].items())) for stream_type in self.__class__.stream_types if stream_type['itag'] in self.streams]

        self.extract(**kwargs)

        self.download(**kwargs)

    def prepare(self, **kwargs):
        pass
        #raise NotImplementedError()

    def extract(self, **kwargs):
        pass
        #raise NotImplementedError()

    def p_stream(self, stream_id):
    
        if stream_id in self.streams:
            stream = self.streams[stream_id]
        else:
            stream = self.dash_streams[stream_id]

        if 'itag' in stream:
            self.data['itag'] = stream_id
            print("    - itag:          %s" % log.sprint(stream_id, log.NEGATIVE))
        else:
            self.data['format'] = stream_id
            print("    - format:        %s" % log.sprint(stream_id, log.NEGATIVE))

        if 'container' in stream:
            self.data['container'] = stream['container']
            print("      container:     %s" % stream['container'])

        if 'video_profile' in stream:
            self.data['container'] = stream['video_profile']
            maybe_print("      video-profile: %s" % stream['video_profile'])

        if 'quality' in stream:
            self.data['quality'] = stream['quality']
            print("      quality:       %s" % stream['quality'])

        if 'size' in stream and 'container' in stream and stream['container'].lower() != 'm3u8':
            if stream['size'] != float('inf')  and stream['size'] != 0:
                print("      size:          %s MiB (%s bytes)" % (round(stream['size'] / 1048576, 1), stream['size']))
                self.data['size'] = "%s MiB (%s bytes)" % (round(stream['size'] / 1048576, 1), stream['size'])

        if 'm3u8_url' in stream:
            print("      m3u8_url:      {}".format(stream['m3u8_url']))
            self.data['m3u8_url'] = stream['m3u8_url']

        if 'itag' in stream:
            print("    # download-with: %s" % log.sprint("you-get --itag=%s [URL]" % stream_id, log.UNDERLINE))
        else:
            print("    # download-with: %s" % log.sprint("you-get --format=%s [URL]" % stream_id, log.UNDERLINE))

        print()
    
        with open('tem.json', 'w') as f:
            f.write(json.dumps(self.data))

    def p_i(self, stream_id):
    
        if stream_id in self.streams:
            stream = self.streams[stream_id]
        else:
            stream = self.dash_streams[stream_id]

        maybe_print("    - title:         %s" % self.title)
        self.data['title'] = self.title
        self.data['size'] = "%s MiB (%s bytes)" % (round(stream['size'] / 1048576, 1), stream['size'])
        self.data['url'] = self.url
        print("       size:         %s MiB (%s bytes)" % (round(stream['size'] / 1048576, 1), stream['size']))
        print("        url:         %s" % self.url)
        print()
        with open('tem.json', 'w') as f:
            f.write(json.dumps(self.data))
        sys.stdout.flush()

    def p(self, stream_id=None):
    
        maybe_print("site:                %s" % self.__class__.name)
        try:
            self.data['site'] = self.__class__.name
        except:
            parse_host()
        maybe_print("title:               %s" % self.title)
        try:
            self.data['title'] = self.title
        except:
            pass
            parse_host()
        if stream_id:
            # Print the stream
            print("stream:")
            self.p_stream(stream_id)

        elif stream_id is None:
            # Print stream with best quality
            print("stream:              # Best quality")
            stream_id = self.streams_sorted[0]['id'] if 'id' in self.streams_sorted[0] else self.streams_sorted[0]['itag']
            self.p_stream(stream_id)

        elif stream_id == []:
            print("streams:             # Available quality and codecs")
            # Print DASH streams
            if self.dash_streams:
                print("    [ DASH ] %s" % ('_' * 36))
                itags = sorted(self.dash_streams,
                               key=lambda i: -self.dash_streams[i]['size'])
                for stream in itags:
                    self.p_stream(stream)
            # Print all other available streams
            if self.streams_sorted:
                print("    [ DEFAULT ] %s" % ('_' * 33))
                for stream in self.streams_sorted:
                    self.p_stream(stream['id'] if 'id' in stream else stream['itag'])

        if self.audiolang:
            print("audio-languages:")
            for i in self.audiolang:
                print("    - lang:          {}".format(i['lang']))
                print("      download-url:  {}\n".format(i['url']))
        with open('tem.json', 'w') as f:
            f.write(json.dumps(self.data))
        sys.stdout.flush()

    def p_playlist(self, stream_id=None):
        maybe_print("site:                %s" % self.__class__.name)
        print("playlist:            %s" % self.title)
        print("videos:")

    def download(self, **kwargs):
        if 'json_output' in kwargs and kwargs['json_output']:
            json_output.output(self)
        elif 'info_only' in kwargs and kwargs['info_only']:
            if 'stream_id' in kwargs and kwargs['stream_id']:
                # Display the stream
                stream_id = kwargs['stream_id']
                if 'index' not in kwargs:
                    self.p(stream_id)
                else:
                    self.p_i(stream_id)
            else:
                # Display all available streams
                if 'index' not in kwargs:
                    self.p([])
                else:
                    stream_id = self.streams_sorted[0]['id'] if 'id' in self.streams_sorted[0] else self.streams_sorted[0]['itag']
                    self.p_i(stream_id)

        else:
            if 'stream_id' in kwargs and kwargs['stream_id']:
                # Download the stream
                stream_id = kwargs['stream_id']
            else:
                # Download stream with the best quality
                from .processor.ffmpeg import has_ffmpeg_installed
                if has_ffmpeg_installed() and player is None and self.dash_streams or not self.streams_sorted:
                    #stream_id = list(self.dash_streams)[-1]
                    itags = sorted(self.dash_streams,
                                   key=lambda i: -self.dash_streams[i]['size'])
                    stream_id = itags[0]
                else:
                    stream_id = self.streams_sorted[0]['id'] if 'id' in self.streams_sorted[0] else self.streams_sorted[0]['itag']

            if 'index' not in kwargs:
                self.p(stream_id)
            else:
                self.p_i(stream_id)

            if stream_id in self.streams:
                urls = self.streams[stream_id]['src']
                ext = self.streams[stream_id]['container']
                total_size = self.streams[stream_id]['size']
            else:
                urls = self.dash_streams[stream_id]['src']
                ext = self.dash_streams[stream_id]['container']
                total_size = self.dash_streams[stream_id]['size']

            if ext == 'm3u8' or ext == 'm4a':
                ext = 'mp4'

            if not urls:
                log.wtf('[Failed] Cannot extract video source.')
            # For legacy main()
            headers = {}
            if self.ua is not None:
                headers['User-Agent'] = self.ua
            if self.referer is not None:
                headers['Referer'] = self.referer
            download_urls(urls, self.title, ext, total_size, headers=headers,
                          output_dir=kwargs['output_dir'],
                          merge=kwargs['merge'],
                          av=stream_id in self.dash_streams)

            if 'caption' not in kwargs or not kwargs['caption']:
                print('Skipping captions or danmaku.')
                return

            for lang in self.caption_tracks:
                filename = '%s.%s.srt' % (get_filename(self.title), lang)
                print('Saving %s ... ' % filename, end="", flush=True)
                srt = self.caption_tracks[lang]
                with open(os.path.join(kwargs['output_dir'], filename),
                          'w', encoding='utf-8') as x:
                    x.write(srt)
                print('Done.')

            if self.danmaku is not None and not dry_run:
                filename = '{}.cmt.xml'.format(get_filename(self.title))
                print('Downloading {} ...\n'.format(filename))
                with open(os.path.join(kwargs['output_dir'], filename), 'w', encoding='utf8') as fp:
                    fp.write(self.danmaku)

            if self.lyrics is not None and not dry_run:
                filename = '{}.lrc'.format(get_filename(self.title))
                print('Downloading {} ...\n'.format(filename))
                with open(os.path.join(kwargs['output_dir'], filename), 'w', encoding='utf8') as fp:
                    fp.write(self.lyrics)

            # For main_dev()
            #download_urls(urls, self.title, self.streams[stream_id]['container'], self.streams[stream_id]['size'])
        keep_obj = kwargs.get('keep_obj', False)
        if not keep_obj:
            self.__init__()
