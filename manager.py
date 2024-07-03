from textual.app import App, ComposeResult
from rich.text import Text
from textual.coordinate import Coordinate
from textual.containers import (
    ScrollableContainer,
    Horizontal,
    Center,
    HorizontalScroll,
    Grid,
    VerticalScroll,
    Middle,
)
from textual.widget import Widget
from textual.widgets import (
    Button,
    Footer,
    Label,
    Header,
    Static,
    DataTable,
    OptionList,
    Select,
    ProgressBar,
)
from textual.widgets.option_list import Option
from textual.reactive import reactive
from textual import on
from glob import glob
import subprocess
import json

subjects_map = [
    ("Chemistry", "0620"),
    ("Physics", "0625"),
    ("ICT", "0417"),
    ("Business Studies", "0450"),
    ("English", "0500"),
    ("Hindi", "0549"),
    ("Mathematics", "0580"),
    ("Environmental Management", "0680"),
]


def bool_to_emoji(x: bool) -> str:
    return "✅" if x else "❌"


def save_status(status: list) -> None:
    with open("data.json", "w") as h:
        json.dump(status, h)


def load_status() -> list:
    with open("data.json", "r") as h:
        deserialized = json.load(h)
        return deserialized


def path_to_data(path: str) -> list:
    data = path.split("/")[1:]  # remove "Papers"
    data = [*data[:-1], data[-1].split(".")[0]]  # remove extension
    data = [*data[:-1], data[-1][3:], data[-1][:2]]  # get paper code and ms / qp
    data = [data[0], *data[1].split("_"), *data[2:]]  # get year and series
    return data


def data_to_path(data: list) -> str:
    path = f"Papers/{data[0]}/{data[1]}_{data[2]}/{data[4]}_{data[3]}"
    if data[4] == "sf" and data[0] == "0417":
        return f"{path}.zip"
    if data[4] == "sf" and data[0] == "0549":
        return f"{path}.mp3"
    return f"{path}.pdf"


def get_paper_data():
    files = glob("Papers/*/*/??_??.*")
    # files = glob("Papers/*/*/*.*")
    data = [path_to_data(x) for x in files]
    # data = [[*x[:-1], "qp", "ms", ""] for x in data]
    new_data = []
    for datum in data:
        prefix = datum[:-1]
        if any([prefix == x[: len(prefix)] for x in new_data]):
            continue
        matches = filter(lambda x: prefix == x[: len(prefix)], data)
        matches = [x[-1] for x in matches]
        suffix = [x if x in matches else "" for x in ["qp", "ms"]]
        if "sf" in matches:
            suffix.append("sf")
        if "in" in matches:
            suffix.append("in")
        suffix += [""] * (3 - len(suffix))
        new_data.append([*prefix, *suffix, False])
    return new_data


class CompletedDisplay(Widget):
    total = reactive(0)
    num = reactive(0)

    def render(self) -> str:
        return f"{ self.num }/{self.total}"


class PaperManagerApp(App):
    CSS_PATH = "manager.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("j", "cursor_down", "Move cursor down"),
        ("k", "cursor_up", "Move cursor up"),
    ]

    data = get_paper_data()
    filters = []
    filtered = data

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        self.bar = ProgressBar(total=len(self.data), show_eta=False)
        self.completed = CompletedDisplay()
        yield VerticalScroll(
            Middle(
                Horizontal(
                    Select(subjects_map, id="code_select"),
                    Select(
                        [(str(x), str(x)) for x in range(2020, 2024)], id="year_select"
                    ),
                    Select(
                        [(x, x) for x in ["FebMar", "OctNov", "MayJun"]],
                        id="series_select",
                    ),
                    Select(
                        [(str(x), x) for x in range(7)],
                        id="paper_select",
                    ),
                    id="top",
                ),
            ),
            Center(
                Horizontal(
                    Label("Progress: ", id="progress"),
                    self.bar,
                    self.completed,
                    id="midhoriz",
                ),
                id="middle",
            ),
            DataTable(),
        )

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        if any(event.control.id in x for x in self.filters):
            self.filters = list(
                map(
                    lambda x: (event.value, event.control.id)
                    if event.control.id in x
                    else x,
                    self.filters,
                )
            )
        else:
            self.filters.append((event.value, event.control.id))
        self.filters = [(x, y) for x, y in self.filters if x != Select.BLANK]
        table = self.query_one(DataTable)
        table.clear()
        easy_filters = [(x, y) for x, y in self.filters if y != "paper_select"]
        potential_paper = list(filter(lambda x: x[1] == "paper_select", self.filters))
        self.filtered = self.data
        if len(potential_paper) > 0:
            paper = int(potential_paper[0][0])
            print(paper)
            self.filtered = [x for x in self.data if x[3].isnumeric() and int(x[3]) // 10 == paper]
        filter_values = list(map(lambda x: x[0], easy_filters))
        self.filtered = [x for x in self.filtered if all(y in x for y in filter_values)]
        self.update_progress()
        table.add_rows(self.filtered)

    def update_progress(self) -> None:
        total = len(self.filtered)
        progress = len([x for x in self.filtered if x[-1] == "✅"])
        self.completed.total = total
        self.completed.num = progress
        self.bar.total = total
        self.bar.progress = progress

    @on(DataTable.CellSelected)
    def cell_selected(self, event: DataTable.CellSelected) -> None:
        table = self.query_one(DataTable)
        row_key, _ = event.cell_key
        if type(event.value) is str:
            data_index = self.data.index(table.get_row(row_key))
            row_idx = table.get_row_index(row_key)
            new_tick = bool_to_emoji(self.data[data_index][-1] != "✅")
            self.data[data_index] = [*self.data[data_index][:-1], new_tick]
            table.update_cell_at(Coordinate(row_idx, 7), new_tick)
            save_status(list(map(lambda x: [*x[:4], x[-1] == "✅"], self.data)))
            delta = 1 if new_tick == "✅" else -1
            self.bar.progress += delta
            self.completed.num += delta
            return
        value = event.value.plain
        if not (value == "ms" or value == "qp" or value == "in" or value == "sf"):
            return
        row = table.get_row(row_key)
        path = data_to_path([*row[:4], value])
        subprocess.Popen(
            ["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def on_mount(self) -> None:
        loaded_status = load_status()
        find = lambda fun, lst: next((i for i, x in enumerate(lst) if fun(x)), None)
        self.data = [
            [
                *x[:-1],
                loaded_status[find(lambda y: y[:4] == x[:4], loaded_status) or 0][-1],
            ]
            for x in self.data
        ]
        self.bar.update(progress=len([x for x in self.data if x[-1]]))
        self.completed.total = len(self.data)
        self.completed.num = len([x for x in self.data if x[-1]])
        self.data = [
            [
                *x[:-4],
                *[Text(y, style="underline blue") for y in x[-4:-1]],
                bool_to_emoji(x[-1]),
            ]
            for x in self.data
        ]
        table = self.query_one(DataTable)
        table.add_columns(
            "subject", "year", "series", "code", "qp", "ms", "other files", "completed"
        )
        table.add_rows(self.data)


if __name__ == "__main__":
    app = PaperManagerApp()
    app.run()
