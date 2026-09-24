import hashlib, io, sys, zlib
import numpy as np
src = sys.argv[1]
with np.load(src) as z:
    arrays = {k: z[k] for k in z.files}
b1 = io.BytesIO(); np.savez_compressed(b1, **arrays)
b2 = io.BytesIO(); np.savez(b2, **{k: arrays[k] for k in sorted(arrays)})
print(f"python {sys.version.split()[0]} numpy {np.__version__} zlib {zlib.ZLIB_RUNTIME_VERSION}: "
      f"savez_compressed={hashlib.sha256(b1.getvalue()).hexdigest()[:16]} canonical(checksum form)={hashlib.sha256(b2.getvalue()).hexdigest()[:16]}")
