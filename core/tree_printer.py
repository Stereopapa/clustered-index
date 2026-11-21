from typing import List, Literal, Tuple, Callable

from core.bplus_tree import BplusTree
from core.structures.page import Page


class TreePrinter:

    def __init__(self, tree: BplusTree):
        self._tree = tree
        self._loader = tree.page_manager

    def print_structure(self, collapse_rec: bool = True):
        page = self._loader.get_root()
        while not page.is_leaf: page = self._loader.page_read(page.pointers[0])

        debug_info: Callable[[Page], str] = (
            (lambda pag: f"P{pag.header.parent}R{pag.header.prev}L{pag.header.next}")
            if self._tree.get_conf_attribute("debug")
            else (lambda pag: "")
        )
        page_print: Callable[[Page],None] = (
            (lambda pag: print(f"{pag.view_no_rec}{debug_info(pag)}",end=""))
            if collapse_rec
            else (lambda pag: print(f"{pag}{debug_info(pag)}",end=""))
        )
        page_len: Callable[[Page],int] = (
            (lambda pag: len(str(pag.view_no_rec)) + len(debug_info(pag)))
            if collapse_rec
            else (lambda pag: len(str(pag)) + len(debug_info(pag)))
        )

        leafs_separator = " " * 2
        children_separator = " " * 6
        level_separator = "\n" * 1

        active_parent: int = page.header.parent
        children_str_len: int = 0
        parents_ident: List[Tuple[int, int]] = []
        next_parents_ident: List[Tuple[int, int]] = []

        #till the root
        while True:
            #to end of the tree level
            while True:
                if page.header.parent != active_parent:
                    print(children_separator,end="")
                    next_parents_ident.append((active_parent, children_str_len + len(children_separator)//2))
                    active_parent, children_str_len = page.header.parent, len(children_separator)//2

                children_str_len += page_len(page)

                if page.is_leaf:
                    page_print(page)
                    print(leafs_separator, end="")
                    children_str_len += len(leafs_separator)
                    if page.header.next > 0:
                        page = self._loader.page_read(page.header.next)
                    else:
                        next_parents_ident.append((active_parent, children_str_len))
                        break
                else:
                    print_parent, print_children_len = parents_ident.pop()
                    page = self._loader.page_read(print_parent)
                    space_amount = ((print_children_len // 2) - (page_len(page) // 2))
                    separator = " " * space_amount
                    children_str_len += space_amount * 2
                    print(separator, end="")
                    page_print(page)
                    print(separator, end="")

                    if len(parents_ident) == 0:
                        next_parents_ident.append((active_parent, children_str_len))
                        break


            if page.is_root: break
            else:
                print(level_separator,end="")
                parents_ident = next_parents_ident.copy()
                parents_ident.reverse()
                next_parents_ident.clear()

                parent_id, ident = parents_ident[-1]
                page = self._loader.page_read(parent_id)

                active_parent, children_str_len = page.header.parent, 0

    def display(self, mode: Literal["structure", "structure_collapse_rec",  "leafs", "sequential"], tittle: str = ""):
        print(f"\n{tittle}")
        match mode:
            case "structure":
                self.print_structure(collapse_rec=False)
            case "structure_collapse_rec":
                 self.print_structure(collapse_rec=True)
            case "leafs":
                page = self._loader.get_root()
                while not page.is_leaf:
                    page = self._loader.page_read(page.pointers[0])
                while page.header.next > 0:
                    print(page)
                    page = self._loader.page_read(page.header.next)
                print(page)
            case "sequential":
                for i in range(1, self._loader._page_count):
                    print(self._loader.page_read(i))
        print("\n")
        self._loader.buff_clear()
