import pytest

from todo.cli import main
from todo.storage import JsonStore


@pytest.fixture
def store(tmp_path):
    return JsonStore(str(tmp_path / "todo.json"))


def test_add_and_list(store):
    store.add("buy milk")
    assert [t.title for t in store.list()] == ["buy milk"]


def test_ids_increment(store):
    assert store.add("a").id == 1
    assert store.add("b").id == 2


def test_complete_hides_from_default_list(store):
    t = store.add("a")
    store.complete(t.id)
    assert store.list() == []
    assert store.list(include_done=True)[0].done


def test_complete_missing_raises(store):
    with pytest.raises(KeyError):
        store.complete(99)


def test_cli_roundtrip(store, capsys):
    main(["add", "write report"], store=store)
    main(["list"], store=store)
    assert "1: write report" in capsys.readouterr().out
