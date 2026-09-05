# detect-secrets-plus: modified from upstream Yelp/detect-secrets (Apache-2.0). See NOTICE.
import argparse
import inspect
import os
from importlib import import_module

from ... import filters
from ...constants import VerifiedResult
from ...core.log import log
from ...exceptions import InvalidFile
from ...settings import get_settings
from ...util.importlib import import_file_as_module
from ...util.path import parse_path
from .common import valid_path


def add_filter_options(parent: argparse.ArgumentParser) -> None:
    parser = parent.add_argument_group(
        title="filter options",
        description=(
            "Configure settings for filtering out secrets after they are flagged by the engine."
        ),
    )

    verify_group = parser.add_mutually_exclusive_group()
    verify_group.add_argument(
        "-n",
        "--no-verify",
        action="store_true",
        help="Disables additional verification of secrets via network call.",
    )
    verify_group.add_argument(
        "--only-verified",
        action="store_true",
        help="Only flags secrets that can be verified.",
    )

    parser.add_argument(
        "--exclude-lines",
        type=str,
        action="append",
        help="If lines match this regex, it will be ignored.",
    )
    parser.add_argument(
        "--exclude-files",
        type=str,
        action="append",
        help="If filenames match this regex, it will be ignored.",
    )
    parser.add_argument(
        "--exclude-secrets",
        type=str,
        action="append",
        help="If secrets match this regex, it will be ignored.",
    )

    if filters.wordlist.is_feature_enabled():
        parser.add_argument(
            "--word-list",
            type=valid_path,
            help=(
                "Text file with a list of words, "
                "if a secret contains a word in the list we ignore it."
            ),
            dest="word_list_file",
        )

    if filters.gibberish.is_feature_enabled():
        parser.add_argument(
            "--gibberish-model",
            type=valid_path,
            help="Path to model trained with gibberish-detector.",
            dest="gibberish_model_file",
        )
        parser.add_argument(
            "--gibberish-limit",
            type=float,
            help="Threshold to determine whether a string is gibberish.",
        )

    _add_custom_filters(parser)
    _add_disable_flag(parser)


def _add_custom_filters(parser: argparse._ArgumentGroup) -> None:
    def valid_looking_paths(path: str) -> str:
        parsed = parse_path(path)
        if parsed.kind == "invalid":
            raise argparse.ArgumentTypeError(f"{path} is not a valid filter path.")

        if parsed.kind == "file":
            if parsed.function_name is None:
                raise argparse.ArgumentTypeError(
                    "Did not specify function name for imported file.",
                )
            if not os.path.isfile(parsed.file_path):
                raise argparse.ArgumentTypeError(
                    f"{parsed.file_path} is not a valid file.",
                )

        return path

    parser.add_argument(
        "-f",
        "--filter",
        type=valid_looking_paths,
        nargs=1,
        action="append",  # so we can support multiple flags with same value
        help=(
            "Specify path to custom filter. "
            "May be a python module path (e.g. detect_secrets.filters.common.is_invalid_file) or "
            "a local file path (e.g. file://path/to/file.py::function_name)."
        ),
    )


def _add_disable_flag(parser: argparse._ArgumentGroup) -> None:
    parser.add_argument(
        "--disable-filter",
        type=str,
        nargs=1,
        action="append",  # so we can support multiple flags with same value
        help="Specify filter to disable. e.g. detect_secrets.filters.common.is_invalid_file",
    )


def parse_args(args: argparse.Namespace) -> None:
    if args.exclude_lines:
        get_settings().filters["detect_secrets.filters.regex.should_exclude_line"] = {
            "pattern": args.exclude_lines,
        }

    if args.exclude_files:
        get_settings().filters["detect_secrets.filters.regex.should_exclude_file"] = {
            "pattern": args.exclude_files,
        }

    if args.exclude_secrets:
        get_settings().filters["detect_secrets.filters.regex.should_exclude_secret"] = {
            "pattern": args.exclude_secrets,
        }

    if filters.wordlist.is_feature_enabled() and args.word_list_file:
        filters.wordlist.initialize(args.word_list_file)

    if filters.gibberish.is_feature_enabled():
        kwargs = {}
        if args.gibberish_model_file:
            kwargs["model_path"] = args.gibberish_model_file

        if args.gibberish_limit:
            kwargs["limit"] = args.gibberish_limit

        filters.gibberish.initialize(**kwargs)

    if not args.no_verify:
        get_settings().filters[
            "detect_secrets.filters.common.is_ignored_due_to_verification_policies"
        ] = {
            "min_level": (
                VerifiedResult.VERIFIED_TRUE if args.only_verified else VerifiedResult.UNVERIFIED
            ).value,
        }
    else:
        get_settings().disable_filters(
            "detect_secrets.filters.common.is_ignored_due_to_verification_policies",
        )

    if args.disable_filter:
        # Flatten entry for easier parsing.
        args.disable_filter = [entry for item in args.disable_filter for entry in item]

        redundant_disabled_filters = set(args.disable_filter) - set(get_settings().filters)
        for name in redundant_disabled_filters:
            log.warning(f'Redundant --disable-filter "{name}"')

        get_settings().disable_filters(*args.disable_filter)

    if args.filter:
        # Flatten entry for easier parsing.
        args.filter = [entry for item in args.filter for entry in item]

        # Post-processing validation
        for item in args.filter:
            _raise_if_custom_filter_path_is_invalid(item)
            get_settings().filters[item] = {}


def _raise_if_custom_filter_path_is_invalid(path: str) -> None:
    parsed = parse_path(path)
    if parsed.kind == "invalid":
        raise argparse.ArgumentTypeError(
            "Invalid Python module path for custom filter.",
        )

    if parsed.kind == "module":
        try:
            module_path, function_name = path.rsplit(".", 1)
        except ValueError:
            raise argparse.ArgumentTypeError(
                "Invalid Python module path for custom filter.",
            )

        try:
            module = import_module(module_path)
        except ModuleNotFoundError:
            raise argparse.ArgumentTypeError(f'Cannot import "{path}" as custom filter.')

        try:
            function = getattr(module, function_name)
        except AttributeError:
            raise argparse.ArgumentTypeError(
                f'No filter function named `{function_name}` found in "{module_path}".',
            )

        if not inspect.isfunction(function):
            raise argparse.ArgumentTypeError(f"{path} is not a filter function.")

    elif parsed.kind == "file":
        if parsed.function_name is None:
            raise argparse.ArgumentTypeError(
                "Did not specify function name for imported file.",
            )

        try:
            module = import_file_as_module(parsed.file_path)
        except (FileNotFoundError, InvalidFile):
            raise argparse.ArgumentTypeError(
                f"Cannot import {parsed.file_path} as custom filter.",
            )

        try:
            getattr(module, parsed.function_name)
        except AttributeError:
            raise argparse.ArgumentTypeError(
                f'No filter function named `{parsed.function_name}` found in "{parsed.file_path}".',
            )
