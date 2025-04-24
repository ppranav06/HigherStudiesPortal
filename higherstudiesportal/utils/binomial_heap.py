from datetime import datetime
from typing import List

class Node:
    def __init__(self, key, data):
        self.key = key  # Priority value
        self.data = data  # Request data
        self.degree = 0
        self.parent = None
        self.child = None
        self.sibling = None

class BinomialHeap:
    def __init__(self):
        self.head = None

    def merge_nodes(self, h1, h2):
        if not h1:
            return h2
        if not h2:
            return h1
        
        if h1.degree <= h2.degree:
            result = h1
            result.sibling = self.merge_nodes(h1.sibling, h2)
        else:
            result = h2
            result.sibling = self.merge_nodes(h1, h2.sibling)
        
        return result

    def union(self, other):
        if not other.head:
            return
        if not self.head:
            self.head = other.head
            return
        
        self.head = self.merge_nodes(self.head, other.head)
        
        prev = None
        current = self.head
        next_node = current.sibling
        
        while next_node:
            if current.degree != next_node.degree or \
               (next_node.sibling and next_node.sibling.degree == current.degree):
                prev = current
                current = next_node
            elif current.key <= next_node.key:
                current.sibling = next_node.sibling
                self._link_nodes(next_node, current)
            else:
                if not prev:
                    self.head = next_node
                else:
                    prev.sibling = next_node
                self._link_nodes(current, next_node)
                current = next_node
            next_node = current.sibling

    def _link_nodes(self, node1, node2):
        node1.parent = node2
        node1.sibling = node2.child
        node2.child = node1
        node2.degree += 1

    def insert(self, key, data):
        new_heap = BinomialHeap()
        new_heap.head = Node(key, data)
        self.union(new_heap)

    def get_min(self):
        if not self.head:
            return None
        
        min_node = self.head
        current = self.head.sibling
        
        while current:
            if current.key < min_node.key:
                min_node = current
            current = current.sibling
        
        return min_node.data

    def extract_min(self):
        if not self.head:
            return None
        
        min_node = self.head
        prev_min = None
        current = self.head.sibling
        prev = self.head
        
        # Find minimum node
        while current:
            if current.key < min_node.key:
                min_node = current
                prev_min = prev
            prev = current
            current = current.sibling
        
        # Remove minimum node
        if not prev_min:
            self.head = min_node.sibling
        else:
            prev_min.sibling = min_node.sibling
        
        # Create heap from children
        if min_node.child:
            child_heap = BinomialHeap()
            current = min_node.child
            while current:
                next_sibling = current.sibling
                current.sibling = child_heap.head
                current.parent = None
                child_heap.head = current
                current = next_sibling
            
            self.union(child_heap)
        
        return min_node.data

    def is_empty(self):
        return self.head is None

    def get_sorted_requests(self) -> List[dict]:
        results = []
        while not self.is_empty():
            results.append(self.extract_min())
        return results
