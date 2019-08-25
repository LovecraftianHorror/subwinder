import os
import struct

from .exceptions import SubHashError


# As per API spec with some tweaks to make it a bit nicer
# https://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
def special_hash(filepath):
    FILE_MIN_SIZE = 65536 * 2
    LONGLONGFORMAT = "<q"  # little-endian long long
    try:
        bytesize = struct.calcsize(LONGLONGFORMAT)

        with open(filepath, "rb") as f:
            filesize = os.path.getsize(filepath)
            filehash = filesize

            if filesize < FILE_MIN_SIZE:
                raise SubHashError(
                    "Filesize is below minimum of {FILE_MIN_SIZE} bytes"
                )

            for i in range(2):
                # Seek on second pass
                if i == 1:
                    # TODO: Could `filesize - 65536` even be negative? Min
                    #       condition above should catch it, test it
                    f.seek(max(0, filesize - 65536), 0)

                # Perform black magic
                for _ in range(65536 / bytesize):
                    buffer = f.read(bytesize)
                    filehash += struct.unpack(LONGLONGFORMAT, buffer)[0]
                    # TODO: couldn't this be done once at the very end?
                    #       test on several files to verify
                    filehash &= 0xFFFFFFFFFFFFFFFF  # Keep as 64-bit int
    except IOError:
        raise SubHashError(f"Error on reading {filepath}")

    return "%016x" % filehash
