import urwid

from mitmproxy.tools.console import common
from mitmproxy.tools.console import signals
from mitmproxy.addons import view
from mitmproxy import export
import mitmproxy.tools.console.master # noqa


def _mkhelp():
    text = []
    keys = [
        ("A", "accept all intercepted flows"),
        ("a", "accept this intercepted flow"),
        ("b", "save request/response body"),
        ("C", "export flow to clipboard"),
        ("d", "delete flow"),
        ("D", "duplicate flow"),
        ("e", "toggle eventlog"),
        ("E", "export flow to file"),
        ("f", "filter view"),
        ("F", "toggle follow flow list"),
        ("L", "load saved flows"),
        ("m", "toggle flow mark"),
        ("M", "toggle marked flow view"),
        ("n", "create a new request"),
        ("o", "set flow order"),
        ("r", "replay request"),
        ("S", "server replay request/s"),
        ("U", "unmark all marked flows"),
        ("v", "reverse flow order"),
        ("V", "revert changes to request"),
        ("w", "save flows "),
        ("W", "stream flows to file"),
        ("X", "kill and delete flow, even if it's mid-intercept"),
        ("z", "clear flow list or eventlog"),
        ("Z", "clear unmarked flows"),
        ("tab", "tab between eventlog and flow list"),
        ("enter", "view flow"),
        ("|", "run script on this flow"),
    ]
    text.extend(common.format_keyvals(keys, key="key", val="text", indent=4))
    return text


help_context = _mkhelp()

footer = [
    ('heading_key', "?"), ":help ",
]


class LogBufferBox(urwid.ListBox):

    def __init__(self, master):
        self.master = master
        urwid.ListBox.__init__(self, master.logbuffer)

    def set_focus(self, index):
        if 0 <= index < len(self.master.logbuffer):
            super().set_focus(index)

    def keypress(self, size, key):
        key = common.shortcuts(key)
        if key == "z":
            self.master.clear_events()
            key = None
        elif key == "G":
            self.set_focus(len(self.master.logbuffer) - 1)
        elif key == "g":
            self.set_focus(0)
        return urwid.ListBox.keypress(self, size, key)


class BodyPile(urwid.Pile):

    def __init__(self, master):
        h = urwid.Text("Event log")
        h = urwid.Padding(h, align="left", width=("relative", 100))

        self.inactive_header = urwid.AttrWrap(h, "heading_inactive")
        self.active_header = urwid.AttrWrap(h, "heading")

        urwid.Pile.__init__(
            self,
            [
                FlowListBox(master),
                urwid.Frame(
                    LogBufferBox(master),
                    header = self.inactive_header
                )
            ]
        )
        self.master = master

    def keypress(self, size, key):
        if key == "tab":
            self.focus_position = (
                self.focus_position + 1) % len(self.widget_list)
            if self.focus_position == 1:
                self.widget_list[1].header = self.active_header
            else:
                self.widget_list[1].header = self.inactive_header
            key = None

        # This is essentially a copypasta from urwid.Pile's keypress handler.
        # So much for "closed for modification, but open for extension".
        item_rows = None
        if len(size) == 2:
            item_rows = self.get_item_rows(size, focus = True)
        i = self.widget_list.index(self.focus_item)
        tsize = self.get_item_size(size, i, True, item_rows)
        return self.focus_item.keypress(tsize, key)


class FlowItem(urwid.WidgetWrap):

    def __init__(self, master, flow):
        self.master, self.flow = master, flow
        w = self.get_text()
        urwid.WidgetWrap.__init__(self, w)

    def get_text(self):
        cols, _ = self.master.ui.get_cols_rows()
        return common.format_flow(
            self.flow,
            self.flow is self.master.view.focus.flow,
            hostheader=self.master.options.showhost,
            max_url_len=cols,
        )

    def selectable(self):
        return True

    def mouse_event(self, size, event, button, col, row, focus):
        if event == "mouse press" and button == 1:
            if self.flow.request:
                self.master.view_flow(self.flow)
                return True

    def keypress(self, xxx_todo_changeme, key):
        (maxcol,) = xxx_todo_changeme
        key = common.shortcuts(key)
        if key == "E":
            signals.status_prompt_onekey.send(
                self,
                prompt = "Export to file",
                keys = [(e[0], e[1]) for e in export.EXPORTERS],
                callback = common.export_to_clip_or_file,
                args = (None, self.flow, common.ask_save_path)
            )
        # elif key == "C":
        #     signals.status_prompt_onekey.send(
        #         self,
        #         prompt = "Export to clipboard",
        #         keys = [(e[0], e[1]) for e in export.EXPORTERS],
        #         callback = common.export_to_clip_or_file,
        #         args = (None, self.flow, common.copy_to_clipboard_or_prompt)
        #     )
        elif key == "b":
            common.ask_save_body(None, self.flow)
        else:
            return key


class FlowListWalker(urwid.ListWalker):

    def __init__(self, master):
        self.master = master
        self.master.view.sig_view_refresh.connect(self.sig_mod)
        self.master.view.sig_view_add.connect(self.sig_mod)
        self.master.view.sig_view_remove.connect(self.sig_mod)
        self.master.view.sig_view_update.connect(self.sig_mod)
        self.master.view.focus.sig_change.connect(self.sig_mod)
        signals.flowlist_change.connect(self.sig_mod)

    def sig_mod(self, *args, **kwargs):
        self._modified()

    def get_focus(self):
        if not self.master.view.focus.flow:
            return None, 0
        f = FlowItem(self.master, self.master.view.focus.flow)
        return f, self.master.view.focus.index

    def set_focus(self, index):
        if self.master.view.inbounds(index):
            self.master.view.focus.index = index
            signals.flowlist_change.send(self)

    def get_next(self, pos):
        pos = pos + 1
        if not self.master.view.inbounds(pos):
            return None, None
        f = FlowItem(self.master, self.master.view[pos])
        return f, pos

    def get_prev(self, pos):
        pos = pos - 1
        if not self.master.view.inbounds(pos):
            return None, None
        f = FlowItem(self.master, self.master.view[pos])
        return f, pos


class FlowListBox(urwid.ListBox):

    def __init__(
        self, master: "mitmproxy.tools.console.master.ConsoleMaster"
    ) -> None:
        self.master = master  # type: "mitmproxy.tools.console.master.ConsoleMaster"
        super().__init__(FlowListWalker(master))

    def get_method_raw(self, k):
        if k:
            self.get_url(k)

    def get_method(self, k):
        if k == "e":
            signals.status_prompt.send(
                self,
                prompt = "Method",
                text = "",
                callback = self.get_method_raw
            )
        else:
            method = ""
            for i in common.METHOD_OPTIONS:
                if i[1] == k:
                    method = i[0].upper()
            self.get_url(method)

    def get_url(self, method):
        signals.status_prompt.send(
            prompt = "URL",
            text = "http://www.example.com/",
            callback = self.new_request,
            args = (method,)
        )

    def new_request(self, url, method):
        try:
            f = self.master.create_request(method, url)
        except ValueError as e:
            signals.status_message.send(message = "Invalid URL: " + str(e))
            return
        self.master.view.focus.flow = f

    def keypress(self, size, key):
        key = common.shortcuts(key)
        if key == "L":
            signals.status_prompt_path.send(
                self,
                prompt = "Load flows",
                callback = self.master.load_flows_callback
            )
        elif key == "M":
            self.master.view.toggle_marked()
        elif key == "n":
            signals.status_prompt_onekey.send(
                prompt = "Method",
                keys = common.METHOD_OPTIONS,
                callback = self.get_method
            )
        elif key == "o":
            orders = [(i[1], i[0]) for i in view.orders]
            lookup = dict([(i[0], i[1]) for i in view.orders])

            def change_order(k):
                self.master.options.console_order = lookup[k]

            signals.status_prompt_onekey.send(
                prompt = "Order",
                keys = orders,
                callback = change_order
            )
        else:
            return urwid.ListBox.keypress(self, size, key)
