import os
import tempfile


_tmp = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}/test.db"