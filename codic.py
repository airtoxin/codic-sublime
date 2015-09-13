#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sublime
import sublime_plugin

import os
import sys

BASE_URL = "https://api.codic.jp/v1/engine/translate.json?text={text}"
PLUGIN_DIR = os.path.dirname(os.path.realpath(__file__))
SETTING_FILE = "codic-sublime.sublime-settings"
SETTINGS = None

sys.path.insert(0, os.path.join(PLUGIN_DIR, 'libs'))
import requests

class CodicEngineCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        def on_done(text):
            if (text):
                self.search(str(text))
        window = sublime.active_window()
        if window:
            window.show_input_panel("[codic] Enter words:", "", on_done, None, None)

    def search(self, text):
        global SETTINGS
        url = BASE_URL.format(text=text)
        api_token = SETTINGS.get("api_token")
        headers = {"Authorization": "Bearer {api_token}".format(api_token=api_token)}
        response = requests.get(url, headers=headers).json()
        if isinstance(response, dict):
            error = response["errors"][0]["message"]
            error_code = response["errors"][0]["code"]
            self.set_error_status(error_code, error)
        else:
            response = response[0]
            candidates = [c["text"] for c in response["words"][0]["candidates"]]
            window = sublime.active_window()
            if window:
                def on_done(selected_index):
                    window.run_command("codic_insert_result", {"text": candidates[selected_index]})
                window.show_quick_panel(candidates, on_done)

    def set_error_status(self, error_code, error):
        status_message = "[codic] {error} ({error_code})".format(error=error, error_code=error_code)
        sublime.set_status("codic", status_message)
        sublime.set_timeout(lambda: sublime.erase_status("codic"), 2000)


class CodicInsertResultCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        for r in self.view.sel():
            if r.empty():
                self.view.insert(edit, r.a, str(args["text"]))
            else:
                self.view.replace(edit, r, str(args["text"]))


def prompt_api_token():
    global SETTINGS
    if SETTINGS.get("api_token"): return True
    def on_done(token):
        if token:
            SETTINGS.set("api_token", str(token))
            sublime.save_settings(SETTING_FILE)
    window = sublime.active_window()
    if window:
        window.show_input_panel("[codic] Enter your api token:", "", on_done, None, None)
        return True
    return False

def plugin_loaded():
    global SETTINGS
    SETTINGS = sublime.load_settings(SETTING_FILE)
    if not prompt_api_token():
        sublime.set_timeout(plugin_loaded, 1000)

if int(sublime.version()) < 3000:
    plugin_loaded()
