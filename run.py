import sys
import os

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)
os.environ["PYTHONPATH"] = _root + os.pathsep + os.environ.get("PYTHONPATH", "")

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[_root],
    )
