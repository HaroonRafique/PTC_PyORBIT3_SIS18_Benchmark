from pathlib import Path

from common.reference_artifacts import sha256_file


ROOT = Path(__file__).resolve().parents[1]
COMMON_INPUTS = {
    "SIS18.seq": "33b1ef751e12fe4bba7ecb42869b197e0441b5f5a3983b693dcb468193a813b1",
    "time.ptc": "37f07edca1793b48fce32c7c98fba488e5f89d68c86b8e384f74f706c13854af",
    "resplit.ptc": "484311f518f7cd570039e3e4ab144d2495653b4a8ca550abe5528cd822220ee4",
    "print_flat_file.ptc": "06d261a0ae3858fdfb95711ff4265f4f67d2d25cfc4295d527221898ec78d276",
}
MADX_HASHES = {
    1: "aa677181292e4f5fe734d34beb3a3073e8d2edb0b51e471ef93994270ae7ef6f",
    2: "ad65dba6e978aba77b8bf256f69805fc48f3b6142acb3baea48d6666f474b46e",
    3: "03341c0a6cc076d6989cbeb52392ec1bb1da5e08e1bf8c71a6145f8934b02f11",
    4: "b3cd6a0961e28d177c256c6b015fcfd8779691dd3c5acdee7b0500ef1a09236d",
    5: "15dd3ffd73c5b105301f3ba7701a371223320e9f32049bc4cdc799b4b39ef25d",
    6: "56f69f54b2ca8a1f9b3a635f552378a69c4fd266590a33e829dd11905f0b8860",
    7: "f8dbb1730e5e73ce1974ccc0aac6ce70ec7dce92960c335e15e363398f0eb105",
    8: "41e98bf69e14f0f1afb7841453998faea18c92ec6979ee0e436ae5745f8d99df",
    9: "dbe77f54ddc83bde3614308123234783a23d12af6168f40ba2fc45377d6ee370",
}


def test_packaged_inputs_match_the_historical_step_inputs():
    for step, madx_hash in MADX_HASHES.items():
        # The glob resolves each benchmark's descriptive directory name.
        input_dirs = list(ROOT.glob(f"step_{step:02d}_*/legacy_input"))
        assert len(input_dirs) == 1
        input_dir = input_dirs[0]
        expected = {**COMMON_INPUTS, "SIS18.madx": madx_hash}
        if step == 2:
            expected["chrom.ptc"] = "fd5ceab7a1bf95d62cde99d00163d9c8d32489539f7b1f3be0074083d68bed61"
        assert {path.name for path in input_dir.iterdir() if path.is_file()} == set(expected)
        assert {name: sha256_file(input_dir / name) for name in expected} == expected
