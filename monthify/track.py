# Track dataclass

from dataclasses import dataclass, field, fields

from monthify.utils import extract_month_and_year


@dataclass()
class Track:
    """
    Parses and stores data such as title and artist about tracks retrieved from the spotify api
    """

    title: str
    artist: str
    added_at: str
    uri: str
    track_month: tuple[str] = field(init=False, repr=False)

    def __post_init__(self):
        self.track_month = extract_month_and_year(self.added_at)

    def __repr__(self):
        cls = self.__class__
        cls_name = cls.__name__
        res = [f"{cls_name}("]
        for f in fields(cls):
            val = getattr(self, f.name)
            res.append(f" {f.name} = {val!r}")

        res.append(")")
        return "".join(res)
