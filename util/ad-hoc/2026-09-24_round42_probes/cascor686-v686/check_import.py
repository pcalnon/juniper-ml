"""Which tree do api.* imports resolve to? (scratch)"""

import os
import sys

sys.path.insert(0, os.path.join(sys.argv[1], "src"))
import api.app as a  # noqa: E402
import api.lifecycle.manager as m  # noqa: E402

print(m.__file__)
print(a.__file__)
print(m._OPT_IN_SKIPPED_CALLER_DEFERRED, m._FETCH_PATH_AUTO_START)
