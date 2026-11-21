import copy
from typing import List, Literal, Unpack, Tuple

from core.page_manager import PageManager
from experiment.metrics import Metrics
from core.structures.record import Record
from core.structures.page import Page, PageType
from core.config import BplusTreeConfig



class BplusTree:
    _metrics: Metrics
    _loader: PageManager
    _conf: BplusTreeConfig

    def set_conf_attribute(self, **kwargs: Unpack[BplusTreeConfig.SeterDict]):
        for key, value in kwargs.items():
            if hasattr(self._conf, key):
                    setattr(self._conf, key, value)
            else: raise AttributeError(f"Configuration doesn't have attribute {key}")

    def get_conf_attribute(self, name: BplusTreeConfig.GetterLiteral):
        if hasattr(self._conf, name):
                return getattr(self._conf, name)
        raise AttributeError(f"Configuration doesn't have attribute {name}")

    def set_conf_by_instance(self, conf: BplusTreeConfig = BplusTreeConfig()):
        self._conf = conf
        if getattr(self, "_loader", None) is not None:
            self._loader._conf = self._conf
            self.reload_file(True)

    def set_conf_by_template(self, conf_template: Literal["default", "presentation"] = "default") -> BplusTreeConfig:
        template: BplusTreeConfig = getattr(BplusTreeConfig, conf_template.upper())

        self._conf = copy.deepcopy(template)
        if getattr(self, "_loader", None) is not None:
            self._loader._conf = self._conf
            self.reload_file(True)
        return self._conf

    def get_conf_copy(self) -> BplusTreeConfig:
        return copy.copy(self._conf)


    def __init__(self, conf: BplusTreeConfig = BplusTreeConfig()):
        self._conf = conf
        self._loader = PageManager(self._conf)
        self.set_metrics(None)

    def set_metrics(self, metrics: Metrics = None):
        self._metrics = metrics
        self._loader.set_metrics(metrics)

    def reload_file(self, override: bool = False):
        original = self._conf.override_file
        self._conf.override_file = override

        self._loader.file_load()

        self._conf.override_file = original

    def safe_operation(func):
        def wrapper(self, *args, **kwargs):
            try:
                res = func(self, *args, **kwargs)
                if kwargs.get("flush", True):
                    self._loader.buff_flush()
                    self._loader.buff_clear()
            except:
                self._loader.revert_to_prev_flush()
                raise

            return res
        return wrapper

    @property
    def page_manager(self) -> PageManager:
        return self._loader

    @property
    def height(self):
        h = 1

        metrics = self._metrics
        self.set_metrics(None)

        page = self._loader.get_root()
        while not page.is_leaf:
            page = self._loader.page_read(page.pointers[0])
            h += 1

        self.set_metrics(metrics)
        return h


    def search(self, key: int) -> Record:
        page = self._loader.get_root()
        while not page.is_leaf:
            page = self._loader.page_read(page.search(key))
        rec = page.search(key)
        self._loader.buff_clear()
        return rec


    def _compensate_leaf(self, left: Page, right: Page, parent: Page, in_parent_idx: int):
        keys = left.keys + right.keys
        records = left.records + right.records

        m = (len(keys) + 1) // 2

        left.keys = keys[:m]
        right.keys = keys[m:]
        left.records = records[:m]
        right.records = records[m:]

        parent.keys[in_parent_idx] = left.keys[-1]

    def _compensate_node(self, left: Page, right: Page, parent: Page, in_parent_idx: int):

        parent_key = parent.keys[in_parent_idx]

        keys = left.keys + [parent_key] + right.keys
        m = len(keys) // 2

        parent.keys[in_parent_idx] = keys.pop(m)

        left.keys = keys[:m]
        right.keys = keys[m:]

        pointers = left.pointers + right.pointers
        m = len(left.keys) + 1

        left.pointers = pointers[:m]
        right.pointers = pointers[m:]



        #pointers rearrangement
        for i, child_id in enumerate(left.pointers):
            child = self._loader.page_read(child_id)
            # if i < len(left.keys) and child.is_leaf:
            #     left.keys[i] = child.keys[-1]
            child.header.parent = left.header.id
            child.dirty = True

        for i, child_id in enumerate(right.pointers):
            child = self._loader.page_read(child_id)
            # if i < len(right.keys) and child.is_leaf:
            #     right.keys[i] = child.keys[-1]
            child.header.parent = right.header.id
            child.dirty = True

    def compensate(self, left: Page, right: Page, parent: Page, in_parent_pos: int):
        right.dirty = parent.dirty = left.dirty = True

        if left.is_leaf and right.is_leaf: self._compensate_leaf(left, right, parent, in_parent_pos)
        else: self._compensate_node(left,right,parent, in_parent_pos)


    def _split_leaf(self, page: Page, parent: Page, in_parent_pos: int):
        left: Page = self._loader.page_alloc(is_leaf=True)
        right = page
        m = (len(page.keys) + 1) // 2

        left.keys = right.keys[:m]
        right.keys = right.keys[m:]

        left.records = right.records[:m]
        right.records = right.records[m:]

        parent.insert(in_parent_pos, left.keys[-1], left.header.id)

        # pointers arrangement
        left.header.parent = parent.header.id

        left.header.prev = right.header.prev
        if left.header.prev > 0:
            temp = self._loader.page_read(left.header.prev)
            temp.header.next = left.header.id
            temp.dirty = True

        left.header.next = right.header.id
        right.header.prev = left.header.id

    def _split_node(self, page: Page, parent: Page, in_parent_pos: int):
        left: Page = self._loader.page_alloc(is_leaf=False)
        right = page
        m = len(page.keys) // 2
        separator = page.keys[m]

        left.keys = right.keys[:m]
        right.keys = right.keys[m + 1:]

        m = len(left.keys) + 1
        left.pointers = right.pointers[:m]
        right.pointers = right.pointers[m:]

        parent.insert(in_parent_pos, separator, left.header.id)

        # pointers arrangement
        left.header.parent = parent.header.id
        for child_id in left.pointers:
            child: Page = self._loader.page_read(child_id)
            child.header.parent = left.header.id
            child.dirty = True

    def _split_root(self, root: Page):
        to_split: Page = self._loader.page_alloc(is_leaf=root.is_leaf)
        to_split.keys = root.keys.copy()

        root.keys.clear()

        if to_split.is_leaf:
            to_split.records = root.records.copy()
            # pointers arrangement
            to_split.header.parent = root.header.id


            root.records.clear()
            self._loader.change_page_type(root, PageType.INTERNAL)

            self._split_leaf(to_split, root, 0)

        else:
            to_split.pointers = root.pointers.copy()

            #pointers arrangement
            to_split.header.parent = root.header.id
            for page_id in to_split.pointers:
                child = self._loader.page_read(page_id)
                child.header.parent = to_split.header.id
                child.dirty = True

            root.pointers.clear()
            self._split_node(to_split, root, 0)

        root.pointers.append(to_split.header.id)

    def split(self, page: Page, parent: Page | None, in_parent_pos: int | None):
        page.dirty = True
        if isinstance(parent, Page): parent.dirty = True

        if page.is_root: self._split_root(page)
        elif page.is_leaf: self._split_leaf(page, parent, in_parent_pos)
        else: self._split_node(page, parent, in_parent_pos)

    def _descent_tree(self, key: int) -> Tuple[Page, List[int]]:
        children_positions: List[int] = []
        page = self._loader.get_root()

        while not page.is_leaf:
            idx = page.find_index(key)
            children_positions.append(idx)
            page = self._loader.page_read(page.pointers[idx])

        return page, children_positions


    @safe_operation #type: ignore
    def insert(self, key: int, rec: Record, flush: bool = True):

        #find
        page, children_positions = self._descent_tree(key)

        #insert leaf
        idx = page.find_index(key)
        page.insert(idx, key, rec)

        parent: Page | None = None
        in_parent_pos: int | None = None

        while page.overflow:
            if page.is_root:
                self.split(page=page, parent=None, in_parent_pos=None)
                break

            parent = self._loader.page_read(page.header.parent)
            in_parent_pos = children_positions.pop()
            left_id = parent.pointers[in_parent_pos - 1] if in_parent_pos > 0 else None
            right_id = parent.pointers[in_parent_pos + 1] if in_parent_pos < len(parent.pointers) - 1 else None

            # compenasate
            if left_id is not None:
                sibling: Page = self._loader.page_read(left_id)
                if not sibling.full:
                    self.compensate(left=sibling, right=page, parent=parent, in_parent_pos=in_parent_pos - 1)
                    break

            if right_id is not None:
                sibling: Page = self._loader.page_read(right_id)
                if not sibling.full:
                    self.compensate(left=page, right=sibling, parent=parent, in_parent_pos=in_parent_pos)
                    break

            # split
            self.split(page, parent, in_parent_pos)
            page = parent

    def _merge_leafs(self, left: Page, right: Page, parent: Page, in_parent_pos: int):
        parent.delete(in_parent_pos, left.keys[-1])

        right.keys = left.keys + right.keys
        right.records = left.records + right.records

        # pointers rearrangement
        right.header.prev = left.header.prev
        if right.header.prev > 0:
            sibling = self._loader.page_read(right.header.prev)
            sibling.header.next = right.header.id
            sibling.dirty = True

        self._loader.page_dealloc(left)

    def _merge_nodes(self, left: Page, right: Page, parent: Page, in_parent_pos: int):
        m_key = parent.keys.pop(in_parent_pos)
        parent.pointers.pop(in_parent_pos)

        right_most_left_child = self._loader.page_read(left.pointers[-1])
        # if right_most_left_child.is_leaf:
        #     m_key = right_most_left_child.keys[-1]


        right.keys = left.keys + [m_key] + right.keys
        right.pointers = left.pointers + right.pointers

        # pointers rearrangement
        for child_id in left.pointers:
            child = self._loader.page_read(child_id)
            child.header.parent = right.header.id
            child.dirty = True

        self._loader.page_dealloc(left)

    def _merge_root(self, left: Page, right: Page, root: Page):

        if left.is_leaf and right.is_leaf:
            self._merge_leafs(left, right, root, 0)
            root.pointers.clear()
            root.keys.clear() #sanity check keys already empty

            self._loader.change_page_type(root, PageType.LEAF)
            root.records = right.records.copy()
            root.keys = right.keys.copy()

        else:
            self._merge_nodes(left, right, root, 0)
            root.pointers.clear()
            root.keys.clear() #sanity check keys already empty

            for child_id in right.pointers:
                child = self._loader.page_read(child_id)
                child.header.parent = root.header.id
                child.dirty = True

            root.keys = right.keys.copy()
            root.pointers = right.pointers.copy()
        self._loader.page_dealloc(right)

    def merge(self, left: Page, right: Page, parent: Page, in_parent_pos: int):
        left.dirty = right.dirty = parent.dirty = True

        if parent.is_root and len(parent.keys) == 1: self._merge_root(left, right, parent)
        elif left.is_leaf and right.is_leaf: self._merge_leafs(left, right, parent, in_parent_pos)
        else: self._merge_nodes(left, right, parent, in_parent_pos)

    def _check_rightmost_leafs_key_deletion(self, page: Page, key: int ,pos: int, in_parent_pos: int):
        if pos == len(page.keys) and pos > 0:
            parent = self._loader.page_read(page.header.parent)
            if in_parent_pos < (len(parent.pointers) - 1):
                parent.keys[in_parent_pos] = page.keys[pos-1]
                parent.dirty = True

    @safe_operation #type: ignore
    def delete(self, key: int, flush: bool = True) -> Record:
        return_rec: Record

        #find
        page, children_positions = self._descent_tree(key)

        pos = page.find_index(key)
        return_rec = page.delete(pos, key)
        # if not page.is_root:
        #     self._check_rightmost_leafs_key_deletion(page, key, pos, children_positions[-1])

        while page.underflow:
            # only situation when root.underflow in b+ tree is when the tree is empty
            if page.is_root: return return_rec

            parent = self._loader.page_read(page.header.parent)
            in_parent_pos = children_positions.pop()

            left_id = parent.pointers[in_parent_pos - 1] if in_parent_pos > 0 else None
            right_id = parent.pointers[in_parent_pos + 1] if in_parent_pos < len(parent.pointers) - 1 else None

            # compensate
            if left_id is not None:
                left_sibling = self._loader.page_read(left_id)
                if left_sibling.has_spare_keys:
                    self.compensate(left=left_sibling, right=page, parent=parent, in_parent_pos=in_parent_pos - 1)
                    break

            if right_id is not None:
                right_sibling = self._loader.page_read(right_id)
                if right_sibling.has_spare_keys:
                    self.compensate(left=page, right=right_sibling, parent=parent, in_parent_pos=in_parent_pos)
                    break

            # merge
            if left_id is not None and right_id is not None:
                left_sibling = self._loader.page_read(left_id)
                right_sibling = self._loader.page_read(right_id)
                if len(left_sibling.keys) <= len(right_sibling.keys):
                    self.merge(left=left_sibling, right=page, parent=parent, in_parent_pos=in_parent_pos - 1)
                else:
                    self.merge(left=page, right=right_sibling, parent=parent, in_parent_pos=in_parent_pos)
            elif left_id is not None:
                left_sibling = self._loader.page_read(left_id)
                self.merge(left=left_sibling, right=page, parent=parent, in_parent_pos=in_parent_pos - 1)
            else:
                right_sibling = self._loader.page_read(right_id)
                self.merge(left=page, right=right_sibling, parent=parent, in_parent_pos=in_parent_pos)

            page = parent

        return return_rec

    @safe_operation  # type: ignore
    def update(self, key: int, new_key: int,  rec: Record, flush: bool = True):
        if key == new_key:
            page, _ = self._descent_tree(key)
            page.update_rec(key, rec)

        else:
            self.delete(key, flush=False)
            self.insert(new_key, rec, flush=False)
