import sublime, sublime_plugin, subprocess, thread, re

class CancelledException(Exception):
    pass

class ProcessFailedException(Exception):
    def __init__(self, stderr, exit_status):
        super(ProcessFailedException, self).__init__()
        self.stderr = stderr
        self.exit_status = exit_status

class PipeResult(object):
    def __init__(self, stdout, stderr, returncode):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    def fixup(self, string):
        return re.sub(r'\r\n|\r', '\n', string.decode('utf-8'))

    def output(self):
        return self.fixup(self.stdout)

    def error_message(self):
        if len(self.stderr) == 0:
            return "Shell returned %d" % self.returncode
        else:
            return "Shell returned %d:\n%s" % (self.returncode, self.fixup(self.stderr))

class ExternalCommandTask(object):
    def __init__(self, view, sublime_cmd_name, cmdline, on_done):
        self.view = view
        self.sublime_cmd_name = sublime_cmd_name
        self.cmdline = cmdline
        self.cancelled = False
        self.done = False
        self.on_done = on_done
        self.proc = None

    def run_filter(self, region_text):
        if self.cancelled:
            raise CancelledException()

        self.proc = subprocess.Popen(
            self.cmdline,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)

        stdout, stderr = self.proc.communicate(region_text)
        returncode = self.proc.returncode

        return PipeResult(stdout, stderr, returncode)

    def show_error_panel(self, failed_results):
        panel = self.view.window().get_output_panel("external_command_errors")
        panel.set_read_only(False)
        edit = panel.begin_edit()
        panel.erase(edit, sublime.Region(0, panel.size()))

        for result in failed_results:
            panel.insert(edit, panel.size(), result.error_message())

        panel.set_read_only(True)
        self.view.window().run_command("show_panel", {"panel": "output.external_command_errors"})
        panel.end_edit(edit)

    def handle_results(self, results, edit):
        raise NotImplementedError()

    def task_input(self):
        raise NotImplementedError()

    def start(self):
        input_strings = self.task_input()

        def run():
            try:
                filter_results = [self.run_filter(string) for string in input_strings]
                def process_results():
                    if not self.cancelled:
                        edit = self.view.begin_edit(self.sublime_cmd_name, None)
                        self.handle_results(filter_results, edit)
                        self.view.end_edit(edit)

                        # handle errors
                        failed_results = [result for result in filter_results if result.returncode]
                        if len(failed_results) > 0:
                            self.show_error_panel(failed_results)

                sublime.set_timeout(process_results, 0)
            finally:
                def done():
                    self.done = True
                    self.on_done(self)
                sublime.set_timeout(done, 0)

        def spin(size, i=0, addend=1):
            if self.done:
                self.view.erase_status('external_command')
                return

            before = i % size
            after = (size - 1) - before
            self.view.set_status('external_command', '%s [%s=%s]' % (self.cmdline, ' ' * before, ' ' * after))
            if not after:
                addend = -1
            if not before:
                addend = 1
            i += addend
            sublime.set_timeout(lambda: spin(size, i, addend), 100)

        thread.start_new_thread(run, ())
        spin(8)

    def cancel(self):
        self.cancelled = True
        proc = self.proc
        if proc and proc.returncode is None:
            try:
                proc.kill()
            except OSError:
                pass


class ReplaceTask(ExternalCommandTask):
    def __init__(self, *args, **kwargs):
        super(ReplaceTask, self).__init__(*args, **kwargs)

    def task_input(self):
        selections = [region for region in self.view.sel() if not region.empty()]
        if len(selections) == 0:
            self.regions = [sublime.Region(0, self.view.size())]
        else:
            self.regions = selections

        return [self.view.substr(region).encode('utf-8') for region in self.regions]

    def handle_results(self, results, edit):
        delta = 0
        for region, result in zip(self.regions, results):
            replacement_text = result.output()
            new_region = sublime.Region(region.begin() + delta, region.end() + delta)
            self.view.erase(edit, new_region)
            delta += self.view.insert(edit, new_region.begin(), replacement_text) - new_region.size()


class InsertTask(ExternalCommandTask):
    def __init__(self, *args, **kwargs):
        super(InsertTask, self).__init__(*args, **kwargs)

    def task_input(self):
        self.regions = self.view.sel()
        return ["" for _ in self.regions]

    def handle_results(self, results, edit):
        delta = 0
        for region, result in zip(self.regions, results):
            replacement_text = result.output()
            new_region = sublime.Region(region.begin() + delta, region.end() + delta)
            delta += self.view.insert(edit, new_region.begin(), replacement_text)


class ExternalCommandManager(sublime_plugin.EventListener):
    tasks = {}

    def on_modified(self, view):
        task = self.tasks.get(view.buffer_id())
        if task:
            task.cancel()

    def on_selection_modified(self, view):
        task = self.tasks.get(view.buffer_id())
        if task and task.view.id() == view.id():
            task.cancel()

    def on_close(self, view):
        task = self.tasks.get(view.buffer_id())
        if task and task.view.id() == view.id():
            task.cancel()

    def task_for_view(self, view):
        return self.tasks.get(view.buffer_id())

    def start_task(self, sublime_command, cmdline):
        view = sublime_command.view
        def on_done(task):
            if self.tasks.get(view.buffer_id()) == task:
                del self.tasks[view.buffer_id()]
        task = sublime_command.task_type(view, sublime_command.name(), cmdline, on_done)
        self.tasks[view.buffer_id()] = task
        task.start()

    def __del__(self):
        for task in self.tasks.values():
            task.cancel()


class ExternalCommandBase(object):
    command_manager = ExternalCommandManager()

    def get_task(self):
        return self.command_manager.task_for_view(self.view)

    def is_enabled(self):
        if self.view.is_read_only():
            return False
        else:
            task = self.get_task()
            return task is None or type(task) == self.task_type

    def description(self):
        task = self.get_task()
        if task and type(task) == self.task_type:
            return "Cancel External Command"
        else:
            return super(ExternalCommandBase, self).description()

    def run(self, _):
        task = self.get_task()
        if task and type(task) == self.task_type:
            task.cancel()
        else:
            def start(cmdline):
                self.command_manager.start_task(self, cmdline)
            self.view.window().show_input_panel("Command:", "", start, None, None)


class FilterThroughCommandCommand(ExternalCommandBase, sublime_plugin.TextCommand):
    task_type = ReplaceTask


class InsertCommandOutputCommand(ExternalCommandBase, sublime_plugin.TextCommand):
    task_type = InsertTask
