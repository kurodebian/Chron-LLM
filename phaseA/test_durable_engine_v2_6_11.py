import os
import json
import unittest
import shutil
import tempfile
import hashlib
from pathlib import Path
from durable_engine_v2_6_11 import (
    DurableRepositoryEngine,
    FramedJournalWriter,
    is_canonical_sha256,
)


class TestDurableEngineV2611Failures(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.test_dir)
        self.engine = DurableRepositoryEngine(self.repo_path)
        self.engine.acquire_lock()

    def tearDown(self):
        self.engine.release_lock()
        shutil.rmtree(self.test_dir)

    def _create_dummy_tx(
        self,
        tx_id: str,
        commit_seq: int = 1,
        content: str = "test content",
        terminal_hash: str = None,
    ) -> Path:
        tx_dir = self.engine.tx_dir / tx_id
        tx_dir.mkdir(parents=True, exist_ok=True)

        pub_base = (
            getattr(self.engine, "published_dir", None)
            or getattr(self.engine, "pub_dir", None)
            or (self.repo_path / "published")
        )
        pub_tx_dir = pub_base / tx_id
        pub_tx_dir.mkdir(parents=True, exist_ok=True)

        # 修正箇所: content.dat -> content.txt
        pub_file = pub_tx_dir / "content.txt"
        content_bytes = content.encode("utf-8") if isinstance(content, str) else content
        with open(pub_file, "wb") as f:
            f.write(content_bytes)

        content_hash = hashlib.sha256(content_bytes).hexdigest()

        # TARGET_INSTALLED の検証用に絶対パスを指定
        abs_dst = str(pub_file.resolve())

        journal_path = tx_dir / "commit.journal"
        journal = FramedJournalWriter(journal_path)
        journal.append_record(
            {"op": "STAGE_CREATED", "tx_id": tx_id, "hash": content_hash}
        )
        journal.append_record({"op": "TARGET_INSTALLED", "dst": abs_dst})
        journal.append_record({"op": "MOVE_VERIFIED", "actual_hash": content_hash})
        journal.append_record(
            {"op": "COMMIT_SEALED", "commit_seq": commit_seq, "hash": content_hash}
        )

        records, calculated_term_hash, _ = journal.read_valid_prefix()
        term_hash = terminal_hash if terminal_hash is not None else calculated_term_hash

        commit_seal = {
            "tx_id": tx_id,
            "commit_seq": commit_seq,
            "content_hash": content_hash,
            "chain_height": len(records),
            "terminal_hash": term_hash,
            "status": "COMMITTED",
            "verified_at_post_state": True,
        }
        seal_bytes = json.dumps(commit_seal, sort_keys=True).encode("utf-8")
        seal_hash = hashlib.sha256(seal_bytes).hexdigest()
        commit_seal["seal_hash"] = seal_hash

        with open(tx_dir / "COMMIT_SEAL", "w", encoding="utf-8") as f:
            json.dump(commit_seal, f, indent=2)

        pub_seal = {
            "tx_id": tx_id,
            "commit_seq": commit_seq,
            "content_hash": content_hash,
            "seal_hash": seal_hash,
        }
        with open(tx_dir / "PUBLISH_SEAL", "w", encoding="utf-8") as f:
            json.dump(pub_seal, f, indent=2)

        return tx_dir

    def test_authority_guard_blocks_invalid_pointer_update(self):
        with self.assertRaises(Exception):
            self.engine._set_current_pointer("invalid_tx_999")
        self.assertFalse(self.engine.current_ptr_file.exists())

    def test_canonical_sha256_predicate(self):
        self.assertTrue(is_canonical_sha256("a" * 64))
        self.assertTrue(is_canonical_sha256("0123456789abcdef" * 4))
        self.assertFalse(is_canonical_sha256("A" * 64))

    def test_crash_mid_transaction_move_done_seal_missing(self):
        tx_path = self.engine.tx_dir / "tx_crash_before_seal"
        tx_path.mkdir(parents=True, exist_ok=True)
        journal_path = tx_path / "commit.journal"

        with open(journal_path, "wb") as f:
            f.write(b"partial commit data...")

        valid, reason = self.engine.verify_transaction("tx_crash_before_seal")
        self.assertFalse(valid)

    def test_failure_commit_seal_non_canonical_terminal_hash(self):
        tx_id = "tx_001"
        tx_path = self._create_dummy_tx(tx_id, commit_seq=1)

        seal_path = tx_path / "COMMIT_SEAL"
        with open(seal_path, "r", encoding="utf-8") as f:
            commit_seal = json.load(f)

        commit_seal["terminal_hash"] = commit_seal["terminal_hash"].upper()
        with open(seal_path, "w", encoding="utf-8") as f:
            json.dump(commit_seal, f, indent=2)

        valid, reason = self.engine.verify_transaction(tx_id)
        self.assertFalse(valid)
        self.assertIn("non-canonical", reason.lower())

    def test_failure_publish_seal_commit_seq_mismatch(self):
        tx_path = self._create_dummy_tx("tx_002", commit_seq=10)
        with open(tx_path / "PUBLISH_SEAL", "r", encoding="utf-8") as f:
            pub_seal = json.load(f)

        pub_seal["commit_seq"] = 999
        with open(tx_path / "PUBLISH_SEAL", "w", encoding="utf-8") as f:
            json.dump(pub_seal, f, indent=2)

        valid, reason = self.engine.verify_transaction("tx_002")
        self.assertFalse(valid)
        self.assertIn("mismatch", reason.lower())

    def test_failure_publish_seal_content_hash_binding_mismatch(self):
        tx_id = "tx_003"
        tx_path = self._create_dummy_tx(tx_id, commit_seq=1)

        pub_base = (
            getattr(self.engine, "published_dir", None)
            or getattr(self.engine, "pub_dir", None)
            or (self.repo_path / "published")
        )
        pub_file = pub_base / tx_id / "content.txt"
        with open(pub_file, "wb") as f:
            f.write(b"tampered content")

        valid, reason = self.engine.verify_transaction(tx_id)
        self.assertFalse(valid)
        self.assertIn("mismatch", reason.lower())

    def test_recovery_rollback_and_causal_total_ordering(self):
        self._create_dummy_tx("tx_001", commit_seq=1)

        tx2_path = self.engine.tx_dir / "tx_002"
        tx2_path.mkdir(parents=True, exist_ok=True)
        with open(tx2_path / "commit.journal", "wb") as f:
            f.write(b"broken journal data")

        recovered_tx = self.engine.scan_and_recover()
        self.assertEqual(recovered_tx, "tx_001")

    def test_wal_hash_chain_corruption(self):
        tx_id = "tx_corrupt"
        tx_path = self.engine.tx_dir / tx_id
        tx_path.mkdir(parents=True, exist_ok=True)

        journal_path = tx_path / "commit.journal"
        corrupted_data = (
            b'{"seq": 1, "prev_hash": "' + b"0" * 64 + b'", "op": "INIT"}\n'
        )
        corrupted_data += (
            b'{"seq": 2, "prev_hash": "'
            + b"a" * 64
            + b'", "data": "'
            + (b"\xc9" * 50)
            + b'"}'
        )

        with open(journal_path, "wb") as f:
            f.write(corrupted_data)

        commit_seal = {
            "tx_id": tx_id,
            "commit_seq": 1,
            "content_hash": "a" * 64,
            "chain_height": 2,
            "terminal_hash": "a" * 64,
            "status": "COMMITTED",
            "verified_at_post_state": True,
            "seal_hash": "a" * 64,
        }
        with open(tx_path / "COMMIT_SEAL", "w", encoding="utf-8") as f:
            json.dump(commit_seal, f, indent=2)

        valid, reason = self.engine.verify_transaction(tx_id)
        self.assertFalse(valid)


if __name__ == "__main__":
    unittest.main()
