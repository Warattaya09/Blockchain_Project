import json
import os
import time
import hashlib


class Blockchain:
    def __init__(self, filename="blockchain.json"):
        self.filename = filename

        if os.path.exists(self.filename) and os.path.getsize(self.filename) > 0:
            with open(self.filename, "r") as f:
                self.chain = json.load(f)
        else:
            self.chain = []
            self.create_genesis_block()
            self.save_chain()

    def create_genesis_block(self):
        block = {
            "index": 0,
            "timestamp": time.time(),
            "data": "Genesis Block",
            "previous_hash": "0",
        }
        block["hash"] = self.calculate_hash(block)
        self.chain.append(block)

    def calculate_hash(self, block):
        # block_copy = block.copy()
        # block_copy.pop("hash", None)
        # block_string = json.dumps(block_copy, sort_keys=True).encode()
        # return hashlib.sha256(block_string).hexdigest()
        block_copy = block.copy()
        block_copy.pop("hash", None)  # ห้ามเอา hash ตัวเองมาคิด
        encoded = json.dumps(block_copy, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()


    def get_last_block(self):
        return self.chain[-1]

    def create_block(self, data):
        prev_block = self.chain[-1]

        # block = {
        #     "index": last_block["index"] + 1,
        #     "timestamp": time.time(),
        #     "data": data,
        #     "previous_hash": last_block["hash"],
        # }
        block = {
        "index": len(self.chain),
        "timestamp": time.time(),
        "data": data,
        "previous_hash": self.calculate_hash(prev_block)
        }

        block["hash"] = self.calculate_hash(block)
        self.chain.append(block)
        self.save_chain()
        return block

    def save_chain(self):
        with open(self.filename, "w") as f:
            json.dump(self.chain, f, indent=2)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]

            if curr["previous_hash"] != self.calculate_hash(prev):
                return False

            if curr["hash"] != self.calculate_hash(curr):
                return False

        return True






