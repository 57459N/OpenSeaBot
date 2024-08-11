from dataclasses import dataclass


@dataclass
class Instrument:
    name: str
    server_name: str
    stopable: bool = True

    def __hash__(self):
        return hash(self.name)


class Instruments:

    def __init__(self, *args: Instrument):
        d = {i.name: i for i in args}
        d.update({i.server_name: i for i in args})
        self.instruments: dict[str, Instrument] = d

    def __getitem__(self, item: str):
        return self.instruments[item]

    def __iter__(self):
        return iter(set(self.instruments.values()))

    def __next__(self):
        return next(self)
