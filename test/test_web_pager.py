from piestats.web.pager import PaginationHelper


def test_pager_page1():
    pager = PaginationHelper(
        bare_route='/server/players',
        num_items=40,
        offset=0,
        interval=20)

    assert pager.next_url == '/server/players/pos/20'
    assert pager.prev_url is None


def test_pager_page2():
    pager = PaginationHelper(
        bare_route='/server/players',
        num_items=40,
        offset=20,
        interval=20)

    assert pager.next_url == '/server/players/pos/40'
    assert pager.prev_url is '/server/players'


def test_pager_page3():
    pager = PaginationHelper(
        bare_route='/server/players',
        num_items=60,
        offset=40,
        interval=20)

    assert pager.next_url == '/server/players/pos/60'
    assert pager.prev_url == '/server/players/pos/20'


def test_pager_last_page():
    pager = PaginationHelper(
        bare_route='/server/players',
        num_items=40,
        offset=40,
        interval=20)

    assert pager.next_url is False
    assert pager.prev_url == '/server/players/pos/20'


def test_pager_incorrect_page():
    pager = PaginationHelper(
        bare_route='/server/players',
        num_items=40,
        offset=41,
        interval=20)

    assert pager.next_url == '/server/players/pos/20'
    assert pager.prev_url is None
