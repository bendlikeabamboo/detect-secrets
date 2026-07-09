# detect-secrets-plus: added in this fork. See NOTICE.
import os

import pytest

from detect_secrets.util.path import CustomPath
from detect_secrets.util.path import convert_local_os_path
from detect_secrets.util.path import parse_path


class TestParsePath:
    @staticmethod
    @pytest.mark.parametrize(
        'input_path, expected',
        (
            # --- Windows paths with function ---
            (
                r'C:\Users\me\f.py::fn',
                CustomPath(kind='file', file_path=r'C:\Users\me\f.py', function_name='fn'),
            ),
            (
                r'file://C:\Users\me\f.py::fn',
                CustomPath(kind='file', file_path=r'C:\Users\me\f.py', function_name='fn'),
            ),
            (
                'file:///C:/Users/me/f.py::fn',
                CustomPath(kind='file', file_path='C:/Users/me/f.py', function_name='fn'),
            ),

            # --- UNC paths ---
            (
                r'\\server\share\f.py::fn',
                CustomPath(kind='file', file_path=r'\\server\share\f.py', function_name='fn'),
            ),

            # --- macOS/Linux absolute paths ---
            (
                '/Users/me/f.py::fn',
                CustomPath(kind='file', file_path='/Users/me/f.py', function_name='fn'),
            ),

            # --- file:// with triple slash (absolute POSIX path) ---
            (
                'file:///home/user/f.py::fn',
                CustomPath(kind='file', file_path='/home/user/f.py', function_name='fn'),
            ),

            # --- Relative paths (both separators) ---
            (
                r'relative\f.py::fn',
                CustomPath(kind='file', file_path=r'relative\f.py', function_name='fn'),
            ),
            (
                'relative/f.py::fn',
                CustomPath(kind='file', file_path='relative/f.py', function_name='fn'),
            ),

            # --- file:// scheme with real fixture ---
            (
                'file://testing/custom_filters.py::is_invalid_secret',
                CustomPath(
                    kind='file',
                    file_path='testing/custom_filters.py',
                    function_name='is_invalid_secret',
                ),
            ),

            # --- Module paths ---
            (
                'detect_secrets.filters.common.is_invalid_file',
                CustomPath(kind='module', module_path='detect_secrets.filters.common.is_invalid_file'),
            ),

            # --- Plugin (file://, no function) ---
            (
                'file://testing/plugin.py',
                CustomPath(kind='file', file_path='testing/plugin.py', function_name=None),
            ),

            # --- Invalid cases ---
            ('http://x.py::fn', CustomPath()),
            ('f.py::', CustomPath()),
            ('f.py::123', CustomPath()),
            ('f.py', CustomPath(kind='module', module_path='f.py')),
        ),
    )
    def test_parse_path(input_path, expected):
        result = parse_path(input_path)
        assert result == expected

    @staticmethod
    def test_bare_file_with_scheme_is_file_not_module():
        result = parse_path('file://some_file.py')
        assert result.kind == 'file'
        assert result.file_path == 'some_file.py'
        assert result.function_name is None


class TestConvertLocalOsPath:
    @staticmethod
    def test_scheme_preserved_on_linux(monkeypatch):
        monkeypatch.setattr(os, 'sep', '/')
        result = convert_local_os_path('file://C:\\Users\\f.py')
        assert result == 'file://C:/Users/f.py'

    @staticmethod
    def test_scheme_preserved_on_windows(monkeypatch):
        monkeypatch.setattr(os, 'sep', '\\')
        result = convert_local_os_path('file://usr/local/f.py')
        assert result == 'file://usr\\local\\f.py'

    @staticmethod
    def test_no_scheme_on_linux(monkeypatch):
        monkeypatch.setattr(os, 'sep', '/')
        result = convert_local_os_path('path\\to\\file')
        assert result == 'path/to/file'
