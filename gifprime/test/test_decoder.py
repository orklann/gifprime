import pytest
import PIL.Image
from StringIO import StringIO


from gifprime.__main__ import GIF, Image


def get_test_gif_path(name):
    """Return the path to the test gif with the given name."""
    return 'gifprime/test/data/{}'.format(name)


def load_test_gif(fp):
    """Load reference GIF using pillow."""
    img = PIL.Image.open(fp)
    images = []
    i = 0
    while True:
        try:
            img.seek(i)
        except EOFError:
            break
        i += 1
        images.append({'data': list(img.convert('RGBA').getdata())})
    return {
        'images': images,
        'size': img.size,
        'info': img.info,
    }


@pytest.mark.parametrize('name', [
    'whitepixel.gif',
    'whitepixel_87a.gif',
    '8x8gradient.gif',
    '8x8gradientanim.gif',
    'transparentcircle.gif',
])
def test_gif_decode(name):
    ref = load_test_gif(get_test_gif_path(name))
    gif = GIF(get_test_gif_path(name))

    assert gif.filename == get_test_gif_path(name), 'filename not set correctly'
    assert gif.size == ref['size'], 'size not set correctly'
    assert len(gif.images) == len(ref['images']), 'wrong number of frames'
    assert [d.rgba_data for d in gif.images] == \
            [i['data'] for i in ref['images']], 'wrong image data'


@pytest.mark.parametrize('name', [
    'whitepixel.gif',
])
def test_gif_encode(name):
    # load testcase image using PIL
    ref = load_test_gif(get_test_gif_path(name))

    # encode image as gif
    gif = GIF()
    gif.size = ref['size']
    gif.images = [Image(rgba_data=i['data'], size=ref['size']) for i in ref['images']]
    file_ = StringIO()
    gif.save(file_)

    # load resulting gif and compare to testcase
    file_.seek(0)
    ref2 = load_test_gif(file_)
    assert ref == ref2


def test_get_gif_comment():
    gif = GIF(get_test_gif_path('whitepixel.gif'))
    assert gif.comments == ["Created with GIMP"]
