import typing

import pytest

from banner_engine import (
    BannerStat, Banner, BannerStorage, EpsilonGreedyBannerEngine, EmptyBannerStorageError
)

TEST_DEFAULT_CTR = 0.1


@pytest.fixture(scope="function")
def test_banners() -> list[Banner]:
    return [
        Banner("b1", cost=1, stat=BannerStat(10, 20)),
        Banner("b2", cost=250, stat=BannerStat(20, 20)),
        Banner("b3", cost=100, stat=BannerStat(0, 20)),
        Banner("b4", cost=100, stat=BannerStat(1, 20)),
    ]


@pytest.mark.parametrize("clicks, shows, expected_ctr", [(1, 1, 1.0), (20, 100, 0.2), (5, 100, 0.05)])
def test_banner_stat_ctr_value(clicks: int, shows: int, expected_ctr: float) -> None:
    stat = BannerStat(clicks, shows)
    assert stat.compute_ctr(TEST_DEFAULT_CTR) == expected_ctr


def test_empty_stat_compute_ctr_returns_default_ctr() -> None:
    stat = BannerStat(0, 0)
    assert stat.compute_ctr(TEST_DEFAULT_CTR) == TEST_DEFAULT_CTR


def test_banner_stat_add_show_lowers_ctr() -> None:
    stat = BannerStat(1, 1)
    ctr_before = stat.compute_ctr(TEST_DEFAULT_CTR)
    stat.add_show()
    ctr_after = stat.compute_ctr(TEST_DEFAULT_CTR)
    assert ctr_after < ctr_before


def test_banner_stat_add_click_increases_ctr() -> None:
    stat = BannerStat(1, 2)
    ctr_before = stat.compute_ctr(TEST_DEFAULT_CTR)
    stat.add_click()
    ctr_after = stat.compute_ctr(TEST_DEFAULT_CTR)
    assert ctr_after > ctr_before


def test_get_banner_with_highest_cpc_returns_banner_with_highest_cpc(test_banners: list[Banner]) -> None:
    storage = BannerStorage(test_banners, TEST_DEFAULT_CTR)
    expected_banner = test_banners[0]
    max_cpc = expected_banner.cost * expected_banner.stat.compute_ctr(TEST_DEFAULT_CTR)

    for banner in test_banners:
        current_cpc = banner.cost * banner.stat.compute_ctr(TEST_DEFAULT_CTR)
        if current_cpc > max_cpc:
            max_cpc = current_cpc
            expected_banner = banner

    actual_banner = storage.banner_with_highest_cpc()
    assert actual_banner.banner_id == expected_banner.banner_id


def test_banner_engine_raise_empty_storage_exception_if_constructed_with_empty_storage() -> None:
    storage = BannerStorage([])
    with pytest.raises(EmptyBannerStorageError):
        EpsilonGreedyBannerEngine(storage, 0.1)


def test_engine_send_click_not_fails_on_unknown_banner(test_banners: list[Banner]) -> None:
    storage = BannerStorage(test_banners)
    engine = EpsilonGreedyBannerEngine(storage, 0.1)
    try:
        engine.send_click("unknown_banner_123")
    except Exception as e:
        pytest.fail(f"Exception was raised: {e}")


def test_engine_with_zero_random_probability_shows_banner_with_highest_cpc(test_banners: list[Banner]) -> None:
    storage = BannerStorage(test_banners, TEST_DEFAULT_CTR)
    engine = EpsilonGreedyBannerEngine(storage, random_banner_probability=0.0)

    expected_banner = storage.banner_with_highest_cpc()
    shown_banner_id = engine.show_banner()

    assert shown_banner_id == expected_banner.banner_id


@pytest.mark.parametrize("expected_random_banner", ["b1", "b2", "b3", "b4"])
def test_engine_with_1_random_banner_probability_gets_random_banner(
        expected_random_banner: str,
        test_banners: list[Banner],
        monkeypatch: typing.Any
) -> None:
    storage = BannerStorage(test_banners)

    monkeypatch.setattr("banner_engine.random.choice", lambda seq: expected_random_banner)
    monkeypatch.setattr("banner_engine.random.random", lambda: 0.0)

    engine = EpsilonGreedyBannerEngine(storage, random_banner_probability=1.0)
    shown_banner_id = engine.show_banner()

    assert shown_banner_id == expected_random_banner


def test_total_cost_equals_to_cost_of_clicked_banners(test_banners: list[Banner]) -> None:
    storage = BannerStorage(test_banners)
    engine = EpsilonGreedyBannerEngine(storage, 0.1)

    banner_1 = test_banners[0]
    banner_2 = test_banners[1]

    engine.send_click(banner_1.banner_id)
    assert engine.total_cost == banner_1.cost

    engine.send_click(banner_2.banner_id)
    assert engine.total_cost == banner_1.cost + banner_2.cost


def test_engine_show_increases_banner_show_stat(test_banners: list[Banner]) -> None:
    storage = BannerStorage(test_banners)
    engine = EpsilonGreedyBannerEngine(storage, 0.5)

    shows_before = {b.banner_id: b.stat.shows for b in test_banners}
    shown_banner_id = engine.show_banner()
    shows_after = {b.banner_id: b.stat.shows for b in test_banners}

    assert shows_after[shown_banner_id] == shows_before[shown_banner_id] + 1


def test_engine_click_increases_banner_click_stat(test_banners: list[Banner]) -> None:
    storage = BannerStorage(test_banners)
    engine = EpsilonGreedyBannerEngine(storage, 0.5)

    banner_id = test_banners[0].banner_id
    clicks_before = storage.get_banner(banner_id).stat.clicks

    engine.send_click(banner_id)
    clicks_after = storage.get_banner(banner_id).stat.clicks

    assert clicks_after == clicks_before + 1
