from __future__ import annotations
import dataclasses
import typing
import types

from pawpaw import Errors, PredicatedValue, type_magic

I = typing.TypeVar('I')  # Input to predicate
R = typing.TypeVar('R')  # Return value type; should be "anything but None", but Python lacks this ability


class Furcation(list[PredicatedValue], typing.Generic[I, R]):
    P_I = typing.Callable[[I], bool]
    C_ITEM = PredicatedValue | tuple[P_I, R | None] | P_I | R

    @classmethod
    def tautology(cls, item: I) -> bool:
        return True

    def __call__(self, item: I) -> R | None:
        i_typ, r_typ = self.generic_types()

        if not type_magic.isinstance_ex(item, i_typ):
            raise Errors.parameter_invalid_type('item', item, i_typ)

        for pv in self:
            if pv.predicate(item):
                return pv.value

        return None

    def generic_types(self) -> tuple[I, R]:
        return typing.get_args(self.__orig_class__)

    def _transform_insertion(self, item: C_ITEM) -> PredicatedValue:
        i_typ, r_typ = self.generic_types()

        if type_magic.isinstance_ex(item, r_typ):
            return PredicatedValue(self.tautology, item)

        if type_magic.isinstance_ex(item, tuple) and \
            len(item) == 2 and \
            type_magic.functoid_isinstance(item[0], typing.Callable[[i_typ], bool]) and \
            type_magic.isinstance_ex(item[1], r_typ | None):
            return PredicatedValue(item[0], item[1])

        if type_magic.isinstance_ex(item, PredicatedValue):
            return item

        if type_magic.functoid_isinstance(item, typing.Callable[[i_typ], bool]):
            return PredicatedValue(item, None)

        raise Errors.parameter_invalid_type('item', item, PredicatedValue, tuple[typing.Callable[[i_typ], bool], r_typ | None], typing.Callable[[i_typ], bool], r_typ)

    def append(self, item: C_ITEM) -> None:
        super().append(self._transform_insertion(item))

    def insert(self, index: int, item: C_ITEM) -> None:
        super().insert(index, self._transform_insertion(item))

    def extend(self, items: typing.Iterable[C_ITEM]) -> None:
        super().extend(self._transform_insertion(i) for i in items)
