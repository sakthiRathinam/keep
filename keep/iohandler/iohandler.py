import ast
import copy
import json
import logging
import re

import astunparse
import chevron
import requests

import keep.functions as keep_functions
from keep.contextmanager.contextmanager import ContextManager


class IOHandler:
    def __init__(self):
        self.context_manager = ContextManager.get_instance()
        self.logger = logging.getLogger(self.__class__.__name__)
        # whether Keep should shorten urls in the message or not
        # todo: have a specific parameter for this?
        self.shorten_urls = False
        self.context_manager = ContextManager.get_instance()
        if (
            self.context_manager.click_context
            and self.context_manager.click_context.params.get("api_key")
            and self.context_manager.click_context.params.get("api_url")
        ):
            self.shorten_urls = True

    def render(self, template):
        # rendering is only support for strings
        if not isinstance(template, str):
            return template
        # check if inside the mustache is object in the context
        if template.count("}}") != template.count("{{"):
            raise Exception(
                f"Invalid template - number of }} and {{ does not match {template}"
            )
        # TODO - better validate functions
        if template.count("(") != template.count(")"):
            raise Exception(
                f"Invalid template - number of ( and ) does not match {template}"
            )
        val = self.parse(template)
        return val

    def parse(self, string):
        """Use AST module to parse 'call stack'-like string and return the result

        Example -
            string = "first(split('1 2 3', ' '))" ==> 1

        Args:
            tree (_type_): _description_

        Returns:
            _type_: _description_
        """
        # break the string to tokens
        # this will break the following string to 4 tokens:
        #
        # string - "Number of errors: {{ steps.grep.condition.threshold.compare_to }}
        #               [threshold was set to len({{ steps.grep.condition.threshold.value }})]
        #               Error: split({{ foreach.value }},'a', 'b')
        #               and first(split({{ foreach.value }},'a', 'b'))"
        # tokens -
        #           {{ steps.grep.condition.threshold.compare_to }}
        #           len({{ steps.grep.condition.threshold.value }})
        #           split({{ foreach.value }},'a', 'b')
        #           first(split({{ foreach.value }},'a', 'b'))

        pattern = re.compile(
            r"(\w+\(\s*\{\{.*?\}\}\s*.*?\))|(\w+\(\s*.*?\)\))|(\{\{.*?\}\})"
        )
        parsed_string = copy.copy(string)
        tokens = pattern.findall(parsed_string)
        if len(tokens) == 0:
            return parsed_string
        elif len(tokens) == 1:
            token = "".join(tokens[0])
            val = self._parse_token(token)
            # if the token is the same as the string, return the value because {{ value }} can be any type
            if parsed_string.strip() == token:
                return val
            # however, if the token is part of a string, return the string with the token replaced with the value
            else:
                parsed_string = parsed_string.replace(token, str(val))
                return parsed_string

        for token in tokens:
            token = "".join(token)
            val = self._parse_token(token)
            parsed_string = parsed_string.replace(token, str(val))
        return parsed_string

    def _parse_token(self, token):
        # if its just a {{ value }} - get the key and return the value
        if token.startswith("{{") and token.endswith("}}"):
            return self._get(key=token)

        # else, it contains a function e.g. len({{ value }}) or split({{ value }}, 'a', 'b')
        def _parse(tree):
            if isinstance(tree, ast.Module):
                return _parse(tree.body[0].value)

            if isinstance(tree, ast.Call):
                func = tree.func
                args = tree.args
                # if its another function
                _args = []
                for arg in args:
                    _arg = None
                    if isinstance(arg, ast.Call):
                        _arg = _parse(arg)
                    elif isinstance(arg, ast.Str):
                        _arg = arg.s
                    # set is basically {{ value }}
                    elif isinstance(arg, ast.Set):
                        _arg = astunparse.unparse(arg).strip()
                        _arg = self._get(_arg)
                    else:
                        arg = arg.value
                    if _arg:
                        _args.append(_arg)
                val = getattr(keep_functions, func.id)(*_args)
                return val

        tree = ast.parse(token)
        return _parse(tree)

    def _get(self, key):
        # change [] to . for the key because thats what chevron uses
        _key = key.replace("[", ".").replace("]", "")

        context = self.context_manager.get_full_context()
        rendered = chevron.render(_key, context)
        # Try to convert it to python object if possible
        if (rendered.startswith("[") and rendered.endswith("]")) or (
            rendered.startswith("{") and rendered.endswith("}")
        ):
            try:
                rendered = ast.literal_eval(rendered)
            except ValueError:
                pass

        return rendered

    def render_context(self, context_to_render: dict):
        """
        Iterates the provider context and renders it using the alert context.
        """
        # Don't modify the original context
        context_to_render = copy.deepcopy(context_to_render)
        for key, value in context_to_render.items():
            if isinstance(value, str):
                context_to_render[key] = self._render_template_with_context(value)
            elif isinstance(value, list):
                context_to_render[key] = self._render_list_context(value)
            elif isinstance(value, dict):
                context_to_render[key] = self.render_context(value)
        return context_to_render

    def _render_list_context(self, context_to_render: list):
        """
        Iterates the provider context and renders it using the alert context.
        """
        for i in range(0, len(context_to_render)):
            value = context_to_render[i]
            if isinstance(value, str):
                context_to_render[i] = self._render_template_with_context(value)
            if isinstance(value, list):
                context_to_render[i] = self._render_list_context(value)
            if isinstance(value, dict):
                context_to_render[i] = self.render_context(value)
        return context_to_render

    def _render_template_with_context(self, template: str) -> str:
        """
        Renders a template with the given context.

        Args:
            template (str): template (string) to render
            alert_context (dict): alert run context

        Returns:
            str: rendered template
        """
        rendered_template = self.render(template)

        # shorten urls if enabled
        if self.shorten_urls:
            rendered_template = self.__patch_urls(rendered_template)

        return rendered_template

    def __patch_urls(self, rendered_template: str) -> str:
        """
        shorten URLs found in the message.

        Args:
            rendered_template (str): The rendered template that might contain URLs
        """
        urls = re.findall(
            "https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+/?.*", rendered_template
        )
        # didn't find any url
        if not urls:
            return rendered_template

        shortened_urls = self.__get_short_urls(urls)
        for url, shortened_url in shortened_urls.items():
            rendered_template = rendered_template.replace(url, shortened_url)
        return rendered_template

    def __get_short_urls(self, urls: list) -> dict:
        """
        Shorten URLs using Keep API.

        Args:
            urls (list): list of urls to shorten

        Returns:
            dict: a dictionary containing the original url as key and the shortened url as value
        """
        try:
            api_url = self.context_manager.click_context.params.get("api_url")
            api_key = self.context_manager.click_context.params.get("api_key")
            response = requests.post(
                f"{api_url}/s", json=urls, headers={"x-api-key": api_key}
            )
            if response.ok:
                return response.json()
            else:
                self.logger.error(
                    "Failed to request short URLs from API",
                    extra={
                        "response": response.text,
                        "status_code": response.status_code,
                    },
                )
        except Exception:
            self.logger.exception("Failed to request short URLs from API")
