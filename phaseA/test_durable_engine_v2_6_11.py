import unittest
import tempfile
import shutil
import os
import json
import hashlib
from durable_engine_v2_6_11 import (
    DurableEngineV2611,
    QuarantineEngine,
    is_canonical_sha256,
)

class TestDurableEngineV2611Failures(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="engine_test_")
        self.repo_dir = os.path.join(self.test_dir, "repo")
        self.engine = DurableEngineV2611(self.repo_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_dummy_tx(self, tx_id: str, commit_seq: int, terminal_hash: str = None, valid_journal: bool = True):
        tx_path = os.path.join(self.engine.tx_dir, tx_id)
        os.makedirs(tx_path, exist_ok=True)

        if terminal_hash is None:
            terminal_hash = "a" * 64

        journal_path = os.path.join(tx_path, "commit.journal")
        if valid_journal:
            line1 = json.dumps({"seq": 1, "prev_hash": "0" * 64, "op": "INIT"}).encode("utf-8")
            h1 = hashlib.sha256(line1).hexdigest()
            line2 = json.dumps({"seq": 2, "prev_hash": h1, "op": "COMMIT"}).encode("utf-8")
            with open(journal_path, "wb") as f:
                f.write(line1 + b"\n" + line2 + b"\n")
        
        commit_seal = {
            "commit_seq": commit_seq,
            "terminal_hash": terminal_hash
        }
        with open(os.path.join(tx_path, "COMMIT_SEAL"), "w", encoding="utf-8") as f:
            json.dump(commit_seal, f)

        return tx_path

    def test_authority_guard_blocks_invalid_pointer_update(self):
        """I-20 ガード: 無効な TX ID に対して _set_current_pointer を呼ぶと Exception が発生し、CURRENT が不変であること"""
        with self.assertRaises(Exception):
            self.engine._set_current_pointer("invalid_tx_999")
        self.assertFalse(os.path.exists(self.engine.current_ptr_file))

    def test_canonical_sha256_predicate(self):
        """I-21.1: 構文チェック関数 is_canonical_sha256 の境界値テスト"""
        self.assertTrue(is_canonical_sha256("a" * 64))
        self.assertTrue(is_canonical_sha256("0123456789abcdef" * 4))
        self.assertFalse(is_canonical_sha256("A" * 64))  # 大文字不可
        self.assertFalse(is_canonical_sha256("a" * 63))  # 桁不足
        self.assertFalse(is_canonical_sha256("a" * 65))  # 桁超過
        self.assertFalse(is_canonical_sha256(12345))

    def test_crash_mid_transaction_move_done_seal_missing(self):
        """クラッシュ擬似: Move 完了後、COMMIT_SEAL 発行前にクラッシュした場合"""
        tx_path = os.path.join(self.engine.tx_dir, "tx_crash_before_seal")
        os.makedirs(tx_path, exist_ok=True)
        journal_path = os.path.join(tx_path, "commit.journal")
        
        # with 文で確実にクローズして ResourceWarning を防止
        with open(journal_path, "wb") as f:
            f.write(b"partial commit data...")
        
        valid, reason = self.engine.verify_transaction("tx_crash_before_seal")
        self.assertFalse(valid)
        self.assertIn("COMMIT_SEAL missing", reason)

    def test_failure_commit_seal_non_canonical_terminal_hash(self):
        """I-21.1 違反: COMMIT_SEAL の terminal_hash が大文字の場合に Authority 拒否されるか"""
        upper_hash = "A" * 64
        self._create_dummy_tx("tx_001", commit_seq=1, terminal_hash=upper_hash)
        
        valid, reason = self.engine.verify_transaction("tx_001")
        self.assertFalse(valid)
        self.assertIn("COMMIT_SEAL terminal_hash is non-canonical", reason)

    def test_failure_publish_seal_commit_seq_mismatch(self):
        """I-11 違反: PUBLISH_SEAL の commit_seq が COMMIT_SEAL と食い違っている場合"""
        tx_path = self._create_dummy_tx("tx_002", commit_seq=10)
        pub_seal = {
            "commit_seq": 999,  # ミスマッチ
            "content_hash": "b" * 64
        }
        with open(os.path.join(tx_path, "PUBLISH_SEAL"), "w", encoding="utf-8") as f:
            json.dump(pub_seal, f)

        valid, reason = self.engine.verify_transaction("tx_002")
        self.assertFalse(valid)
        self.assertIn("PUBLISH_SEAL commit_seq mismatch", reason)

    def test_failure_publish_seal_content_hash_binding_mismatch(self):
        """I-11 違反: PUBLISH_SEAL 内の content_hash と実際のファイル内容が不一致"""
        tx_id = "tx_003"
        tx_path = self._create_dummy_tx(tx_id, commit_seq=1)
        
        pub_dir = os.path.join(self.engine.published_dir, tx_id)
        os.makedirs(pub_dir, exist_ok=True)
        content_file = os.path.join(pub_dir, "content.dat")
        with open(content_file, "wb") as f:
            f.write(b"hello world")

        pub_seal = {
            "commit_seq": 1,
            "content_hash": "0" * 64  # ミスマッチハッシュ
        }
        with open(os.path.join(tx_path, "PUBLISH_SEAL"), "w", encoding="utf-8") as f:
            json.dump(pub_seal, f)

        valid, reason = self.engine.verify_transaction(tx_id)
        self.assertFalse(valid)
        self.assertIn("PUBLISH_SEAL content_hash binding mismatch", reason)

    def test_recovery_rollback_and_causal_total_ordering(self):
        """I-21 復旧: 正常な複数 TX の最新版が破壊された際、全順序に従い直近の正当な Authority に戻るか"""
        # tx_001 (正常)
        self._create_dummy_tx("tx_001", commit_seq=1)
        
        # tx_002 (最新だが破壊されている: COMMIT_SEALなし)
        tx2_path = os.path.join(self.engine.tx_dir, "tx_002")
        os.makedirs(tx2_path, exist_ok=True)
        with open(os.path.join(tx2_path, "commit.journal"), "wb") as f:
            f.write(b"broken journal data")

        # 破損した tx_002 を無視して正常な tx_001 に復旧されるか確認
        recovered_tx = self.engine.scan_and_recover()
        self.assertEqual(recovered_tx, "tx_001")
        
        # CURRENT ポインタが tx_001 に正しくセットされているか検証
        with open(self.engine.current_ptr_file, "r", encoding="utf-8") as f:
            curr = f.read().strip()
        self.assertEqual(curr, "tx_001")

    def test_wal_hash_chain_corruption(self):
        """WAL 損壊: ファイルの途中のバイトが化けて Hash Chain が破綻した場合"""
        tx_id = "tx_corrupt"
        tx_path = os.path.join(self.engine.tx_dir, tx_id)
        os.makedirs(tx_path, exist_ok=True)
        
        # 不正なバイナリデータ（UTF-8デコード不可）を書き込んで WAL 損壊を再現
        journal_path = os.path.join(tx_path, "commit.journal")
        corrupted_data = b'{"seq": 1, "prev_hash": "' + b"0"*64 + b'", "op": "INIT"}\n'
        corrupted_data += b'{"seq": 2, "prev_hash": "' + b"a"*64 + b'", "data": "' + (b"\xc9" * 50) + b'"}'
        
        with open(journal_path, "wb") as f:
            f.write(corrupted_data)
            
        with open(os.path.join(tx_path, "COMMIT_SEAL"), "w", encoding="utf-8") as f:
            json.dump({"commit_seq": 1, "terminal_hash": "a" * 64}, f)

        valid, reason = self.engine.verify_transaction(tx_id)
        self.assertFalse(valid)
        self.assertIn("Hash Chain broken or corrupt", reason)

if __name__ == "__main__":
    unittest.main()