import os
from tempfile import NamedTemporaryFile

import pytest  # type: ignore

from subwinder.exceptions import SubHashError
from subwinder.utils import extract, special_hash
from tests.utils import RandomTempFile


def test_extract():
    COMPRESSED = (
        "H4sIAIXHxV0C/yXLwQ0CMQxE0VbmxoVCoAyzHiBS4lnFXtB2TyRuT/r6N/Yu1JuTV9wvY9EKL8mhTm"
        "wa+2QmHRYOxiZfzuNRrVZv8dQcVk3xP08dSMFps5/4WhRKSPvwBzf2OXZqAAAA"
    )
    IDEAL = (
        b"Hello there, I'm that good ole compressed and encoded subtitle information"
        b" that you so dearly want to save"
    )

    assert extract(COMPRESSED) == IDEAL


def test_special_hash():
    CHUNK_SIZE = 64 * 1024  # 64KiB
    HASHED_SIZE = CHUNK_SIZE * 2

    # Make sure fails on too small of size
    with RandomTempFile(HASHED_SIZE - 1) as rand_file:
        with pytest.raises(SubHashError):
            special_hash(rand_file)

    # Ensure hash doesn't just run over the whole file
    temp_file = NamedTemporaryFile(delete=False)
    temp_file.write(bytes(CHUNK_SIZE))
    temp_file.write((1).to_bytes(1, byteorder="big"))
    temp_file.write(bytes(CHUNK_SIZE))
    temp_file.close()

    # Hash should be 0x0 (sum) + 0x2001 (file size), if the middle byte was included
    # then it would be 0x1 (sum) instead
    assert "0000000000020001" == special_hash(temp_file.name)

    # Cleanup our mess since we needed `delete=False` for `NamedTemporaryFile`
    os.remove(temp_file.name)

    # Test for matching hashes
    HASHES = [
        "a7abc175960dcada",
        "25182dd38c3b3793",
        "51cbe0f797fcf0b2",
        "3a947b73b070ea20",
        "2503835efd3d3c59",
    ]
    for i, hash in zip(range(5), HASHES):
        with RandomTempFile(HASHED_SIZE, seed=i) as rand_file:
            assert hash == special_hash(rand_file)
