"""
Functions to test mysgen.
"""
import os 
from unittest.mock import patch, mock_open
from datetime import datetime
import markdown
from mysgen.main import init, parse, parse_metadata, build_menu, base_vars


this_dir = os.path.dirname(os.path.realpath(__file__))


@patch('mysgen.main.main')
@patch('mysgen.main.__name__', '__main__')
def test_unit_init(mock_main):
    """
    Test init function.
    """
    init()
    mock_main.assert_called_once()


def test_unit_parse_metadata(fs):
    """
    Test parse function for metadata.

    This does not test the whole function, yet.
    """
    metadata = {
        'author': ['A man has no name'],
        'category': ['Category'],
        'date': ['2021-01-24'],
        'image': ['20210124.jpg'],
        'status': ['published'],
        'tags': ['tag1,tag2'],
        'title': ['Test post'],
        'type': ['photo']
    }

    meta = parse_metadata(metadata)

    assert meta['title'] == 'Test post'
    assert meta['date'] == datetime(2021, 1, 24, 0, 0)
    assert meta['author'] == 'A man has no name'
    assert meta['category'] == 'Category'
    assert meta['tags'] == ['tag1', 'tag2']
    assert meta['type'] == 'photo'
    assert meta['image'] == '20210124.jpg'
    assert meta['status'] == 'published'


with open(this_dir + '/fixtures/test_post.md', 'r') as file:
    test_post = file.read()


@patch('mysgen.main.CONTENT', 'content')
@patch('builtins.open', mock_open(read_data=test_post))
def test_unit_parse_post(fs):
    """
    Test parse function for posts.
    """
    fs.create_file('content/posts/test_post.md')

    posts = {}
    parse(posts, 'posts')

    post = list(posts.keys())[0]
    assert os.path.exists('content/posts/test_post.md')
    assert post == 'test_post.md'
    assert posts[post].meta['title'] == 'Test post'
    assert posts[post].meta['date'] == datetime(2021, 1, 24, 0, 0)
    assert posts[post].meta['author'] == 'A man has no name'
    assert posts[post].meta['category'] == 'Category'
    assert posts[post].meta['tags'] == ['tag1', 'tag2']
    assert posts[post].meta['type'] == 'photo'
    assert posts[post].meta['image'] == '20210124.jpg'
    assert posts[post].meta['status'] == 'published'
    assert posts[post].content == '<p>Text.</p>'


with open(this_dir + '/fixtures/test_page.md', 'r') as file:
    test_page = file.read()


@patch('mysgen.main.CONTENT', 'content')
@patch('builtins.open', mock_open(read_data=test_page))
def test_unit_parse_page(fs):
    """
    Test parse function for pages.
    """
    fs.create_file('content/pages/test_page.md')

    pages = {}
    parse(pages, 'pages')

    page = list(pages.keys())[0]
    assert os.path.exists('content/pages/test_page.md')
    assert page == 'test_page.md'
    assert pages[page].meta['title'] == 'Test page'
    assert pages[page].meta['date'] == datetime(2021, 1, 24, 0, 0)
    assert pages[page].meta['author'] == 'A man has no name'
    assert pages[page].meta['url'] == 'test.html'
    assert pages[page].meta['status'] == 'published'
    assert pages[page].content == '<p>Text.</p>'


@patch.dict(base_vars, {'MENUITEMS': [
    ['home', ''], ['archive', '/' + 'archive']
]})
def test_unit_build_menu():
    """
    Test build menu function.
    """
    pages = ['test_page1.md', 'test_page2.md']

    build_menu(pages)

    menu = base_vars['MENUITEMS']
    assert menu[0] == ['home', '']
    assert menu[1] == ['archive', '/archive']
    assert menu[2] == ['test_page1', '/test_page1']
    assert menu[3] == ['test_page2', '/test_page2']