"""Main entry point for gifprime."""

from argparse import ArgumentParser
from contextlib import contextmanager
from subprocess import check_output
import construct
import json
import os
import praw
import requests
import time

from gifprime.core import GIF, Image
from gifprime.util import readable_size
from gifprime.viewer import GIFViewer


@contextmanager
def measure_time(label, print_output):
    """Context manager for measuring execution time."""
    if print_output:
        print 'starting {}...'.format(label)
    start_sec = time.time()
    start_clock = time.clock()
    yield
    elapsed_sec = time.time() - start_sec
    elapsed_clock = time.clock() - start_clock
    if print_output:
        print ('... {} complete: {:.3f} seconds, {:.3f} cpu time'
               .format(label, elapsed_sec, elapsed_clock))


def parse_args():
    """Parse arguments and start the program."""
    parser = ArgumentParser('gifprime')
    parser.add_argument(
        '--time', '-t', help='report encoding and decoding times',
        default=False, action='store_true'
    )
    subparser = parser.add_subparsers()

    # Encoder
    encoder = subparser.add_parser('encode', help='create a gif')
    encoder.add_argument('images', nargs='+', help='image frame for gif')
    encoder.add_argument('--output', '-o', help='output filename')
    encoder.add_argument('--loop-count', '-l', default=0, type=int,
                         help='0 for infinite (default)')
    encoder.set_defaults(command='encode')

    # Decoder
    decoder = subparser.add_parser('decode', help='view a gif')
    decoder.add_argument('filename')
    decoder.set_defaults(command='decode')

    # Reddit Decoder
    reddit = subparser.add_parser('reddit', help='get a gif from reddit')
    reddit.add_argument('--subreddit', '-s', default='gifs')
    reddit.set_defaults(command='reddit')

    return parser.parse_args()


def run_encoder(args):
    """Encode new GIF and open it in the viewer."""
    run = lambda cmd, *args: check_output(cmd.format(*args).split(' '))
    gif = GIF()

    for filepath in args.images:
        rgba = run('convert -alpha on {} rgba:-', filepath)
        rgba_data = [tuple(col) for col in construct.Array(
            lambda ctx: len(rgba) / 4,
            construct.Array(4, construct.ULInt8('col')),
        ).parse(rgba)]
        raw_size = json.loads(run('exiftool -j {}', filepath))[0]['ImageSize']
        size = [int(value) for value in raw_size.split('x')]

        gif.images.append(Image(rgba_data, size, 1000))

    gif.size = size
    gif.loop_count = args.loop_count

    with open(args.output, 'wb') as file_:
        with measure_time('encode', args.time):
            gif.save(file_)

    show_gif(args.output, benchmark=args.time)


def run_decoder(args):
    """Decode GIF by opening it with the viewer."""
    show_gif(args.filename, benchmark=args.time)


def run_reddit(args):
    """Grab a random GIF from reddit."""
    client = praw.Reddit(user_agent='gifprime')
    post = client.get_random_submission(subreddit=args.subreddit)
    num_bytes = int(requests.head(post.url).headers['content-length'])

    print 'Found one! "{}", {}'.format(post.title, readable_size(num_bytes))
    show_gif(post.url, benchmark=args.time)


def show_gif(uri, benchmark=False):
    """Open a file or URL in the viewer."""
    if uri.startswith('http'):
        print 'Downloading...'
        gif = GIF.from_url(uri)
    elif os.path.isfile(uri):
        print 'Loading...'
        with measure_time('decode', benchmark):
            gif = GIF.from_file(uri)
    else:
        assert False, 'Expected a filename or URL'

    viewer = GIFViewer(gif)
    viewer.show()


def main():
    """Main entry point."""
    args = parse_args()

    if args.command == 'encode':
        run_encoder(args)
    elif args.command == 'decode':
        run_decoder(args)
    elif args.command == 'reddit':
        run_reddit(args)


if __name__ == '__main__':
    main()
