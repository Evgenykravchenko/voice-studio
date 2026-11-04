"""A foreign ready health page must never be reused as this studio."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('studio_check',Path(__file__).resolve().parents[1]/'scripts/check-studio.py')
launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)


class LauncherIdentityTests(unittest.TestCase):
    def test_missing_relative_or_wrong_project_identity_is_not_a_running_studio(self):
        with tempfile.TemporaryDirectory(prefix='studio identity ') as directory:
            root=Path(directory)
            for value in [None,[],{'status':'ready'},{'status':'ready','projectRoot':''},{'status':'ready','projectRoot':'.'},
                          {'status':'ready','projectRoot':None},{'status':'ready','projectRoot':str(root/'another-project')},
                          {'status':'starting','projectRoot':str(root)}]:
                with self.subTest(value=value):self.assertFalse(launcher.matches_project(value,root))
            self.assertTrue(launcher.matches_project({'status':'ready','projectRoot':str(root)},root))

    def test_project_symlinks_are_compared_by_their_real_location(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);real=root/'real';real.mkdir();link=root/'linked';link.symlink_to(real,target_is_directory=True)
            self.assertTrue(launcher.matches_project({'status':'ready','projectRoot':str(link)},real))


if __name__=='__main__':unittest.main()
