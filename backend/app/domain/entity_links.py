"""Quién es quién: agrupar referencias externas en entidades (plan D-4).

Dos referencias son la misma entidad (jugador o franquicia) solo si:
- una fuente declara el enlace (`same_as` o `predecessor`; RF-114, RF-131), o
- la curación las une (RF-131).

Una separación de la curación impide que dos referencias acaben juntas, directa o
indirectamente, aunque una fuente las enlace (RF-133). Nunca se une por coincidencia
de nombre o gamertag (RF-19, RF-132): esta función no recibe nombres.
"""

from collections.abc import Hashable, Iterable, Sequence

Ref = Hashable


class CurationConflictError(ValueError):
    """La curación une y separa a la vez referencias que no pueden estar juntas."""


class _Groups:
    """Unión de conjuntos con restricciones de separación."""

    def __init__(self, splits: Iterable[tuple[Ref, Ref]]):
        self.parent: dict[Ref, Ref] = {}
        self.splits = [tuple(pair) for pair in splits]

    def add(self, ref: Ref) -> None:
        self.parent.setdefault(ref, ref)

    def find(self, ref: Ref) -> Ref:
        self.add(ref)
        root = ref
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[ref] != root:  # compresión de caminos
            self.parent[ref], ref = root, self.parent[ref]
        return root

    def members(self, root: Ref) -> set[Ref]:
        return {ref for ref in self.parent if self.find(ref) == root}

    def would_violate_split(self, a: Ref, b: Ref) -> bool:
        group_a, group_b = self.members(self.find(a)), self.members(self.find(b))
        return any(
            (x in group_a and y in group_b) or (x in group_b and y in group_a) for x, y in self.splits
        )

    def union(self, a: Ref, b: Ref) -> bool:
        """Une los grupos de `a` y `b` si ninguna separación lo impide. Devuelve si se unieron."""
        root_a, root_b = self.find(a), self.find(b)
        if root_a == root_b:
            return True
        if self.would_violate_split(a, b):
            return False
        # Raíz determinista (la menor por texto) para que el resultado no dependa del orden.
        low, high = sorted((root_a, root_b), key=repr)
        self.parent[high] = low
        return True


def group_refs(
    refs: Iterable[Ref],
    source_links: Iterable[tuple[Ref, Ref]] = (),
    merges: Iterable[Sequence[Ref]] = (),
    splits: Iterable[tuple[Ref, Ref]] = (),
) -> list[frozenset]:
    """Agrupa las referencias en entidades.

    Args:
        refs: Referencias conocidas (p. ej. `("bp", "123")`).
        source_links: Parejas enlazadas por una fuente.
        merges: Grupos que la curación declara como la misma entidad.
        splits: Parejas que la curación declara como entidades distintas.

    Returns:
        Lista de grupos; cada grupo es una entidad.

    Raises:
        CurationConflictError: si una unión de la curación contradice una separación.
    """
    groups = _Groups(splits)
    for ref in sorted(refs, key=repr):
        groups.add(ref)

    # 1. Las uniones de la curación van primero: si contradicen una separación, es un error.
    for merge in merges:
        first, *rest = merge
        for other in rest:
            if not groups.union(first, other):
                raise CurationConflictError(
                    f"La curación une {first!r} y {other!r}, pero también los separa."
                )

    # 2. Los enlaces de las fuentes, en orden determinista; los que violan una separación se ignoran.
    for a, b in sorted((tuple(link) for link in source_links), key=repr):
        groups.union(a, b)

    by_root: dict[Ref, set[Ref]] = {}
    for ref in groups.parent:
        by_root.setdefault(groups.find(ref), set()).add(ref)
    return [frozenset(members) for members in by_root.values()]
