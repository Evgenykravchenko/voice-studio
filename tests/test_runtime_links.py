import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from voice_cloner import cli


class RuntimeLinkTests(unittest.TestCase):
    def test_old_or_dangling_ffmpeg_links_are_repaired_without_touching_the_old_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);binary=root/'.venv/lib/bundled-ffmpeg';binary.parent.mkdir(parents=True);binary.write_bytes(b'new binary')
            link=root/'.runtime/bin/ffmpeg';link.parent.mkdir(parents=True)
            old=root/'old binary';old.write_bytes(b'old binary')
            with patch.object(cli,'PROJECT_DIR',root),patch.object(cli,'PROFILES_DIR',root/'data/profiles'),patch.object(cli,'OUTPUTS_DIR',root/'outputs'),patch.dict(os.environ,{'PATH':'/usr/bin'},clear=True),patch('imageio_ffmpeg.get_ffmpeg_exe',return_value=str(binary)):
                for target in [old,root/'missing old binary']:
                    link.symlink_to(target)
                    cli._ensure_local_environment()
                    self.assertFalse(Path(os.readlink(link)).is_absolute())
                    self.assertEqual(binary.resolve(),link.resolve())
                    self.assertEqual(b'old binary',old.read_bytes())
                    cli._ensure_local_environment()  # Repeated setup is harmless.
                    link.unlink()

    def test_existing_regular_local_binary_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);link=root/'.runtime/bin/ffmpeg';link.parent.mkdir(parents=True);link.write_bytes(b'local binary')
            with patch.object(cli,'PROJECT_DIR',root),patch.object(cli,'PROFILES_DIR',root/'data/profiles'),patch.object(cli,'OUTPUTS_DIR',root/'outputs'),patch.dict(os.environ,{'PATH':'/usr/bin'},clear=True):
                cli._ensure_local_environment()
            self.assertFalse(link.is_symlink());self.assertEqual(b'local binary',link.read_bytes())
