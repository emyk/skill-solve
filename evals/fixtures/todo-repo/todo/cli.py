import argparse

from .storage import JsonStore


def main(argv=None, store=None):
    parser = argparse.ArgumentParser(prog="todo")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("add").add_argument("title")
    ls = sub.add_parser("list")
    ls.add_argument("--all", action="store_true")
    sub.add_parser("done").add_argument("id", type=int)
    args = parser.parse_args(argv)
    store = store or JsonStore()

    if args.cmd == "add":
        t = store.add(args.title)
        print(f"added {t.id}: {t.title}")
    elif args.cmd == "list":
        for t in store.list(include_done=args.all):
            print(f"[{'x' if t.done else ' '}] {t.id}: {t.title}")
    elif args.cmd == "done":
        store.complete(args.id)
        print(f"completed {args.id}")


if __name__ == "__main__":
    main()
