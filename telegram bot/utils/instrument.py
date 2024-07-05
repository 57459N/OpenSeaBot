from dataclasses import dataclass


@dataclass
class Instrument:
    name: str
    server_name: str

    def __hash__(self):
        return hash(self.name)


class Instruments:

    def __init__(self, *args: Instrument):
        self.instruments: dict[str, Instrument] = {i.name: i for i in args}

    def __getitem__(self, item: str):
        return self.instruments[item]

    def __iter__(self):
        return iter(self.instruments.values())

    def __next__(self):
        return next(self)
