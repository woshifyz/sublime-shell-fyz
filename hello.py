# -*- coding: utf-8 -*-

import sublime, sublime_plugin

import os,os.path

import shlex,subprocess

class GDBView(object):

    def __init__(self, name, s=True):

        self.name = name

        self.closed = True

        self.doScroll = s

        self.view = None

        self.value = None


    def is_open(self):

        return not self.closed



    def open(self):

        if self.view == None or self.view.window() == None:

            sublime.active_window().focus_group(1)

            self.create_view()


    def close(self):

        if self.view != None:

            sublime.active_window().focus_group(1)

            self.destroy_view()


    def add(self,msg):

        self.view.set_read_only(False)

        e = self.view.begin_edit()

        #self.view.erase(e, sublime.Region(0, self.view.size()))

        self.view.insert(e,self.view.size(),msg)

        self.view.end_edit(e)

        self.view.set_read_only(True)

    def scroll(self):
        self.view.show(self.view.size())

    def create_view(self):

        self.view = sublime.active_window().new_file()

        self.view.set_name(self.name)

        self.view.set_scratch(True)

        self.view.set_read_only(True)

        # Setting command_mode to false so that vintage

        # does not eat the "enter" keybinding

        self.view.settings().set('command_mode', False)

        self.closed = False


    def destroy_view(self):

        sublime.active_window().focus_view(self.view)

        sublime.active_window().run_command("close")

        self.view = None


    def is_closed(self):

        return self.closed


    def was_closed(self):

        self.closed = True


    def get_view(self):

        return self.view


    def do_clear(self, data):

        self.view.set_read_only(False)

        e = self.view.begin_edit()

        self.view.erase(e, sublime.Region(0, self.view.size()))

        self.view.end_edit(e)

        self.view.set_read_only(True)


    def do_scroll(self, data):

        self.view.run_command("goto_line", {"line": data + 1})


    def do_set_viewport_position(self, data):

        # Shouldn't have to call viewport_extent, but it

        # seems to flush whatever value is stale so that

        # the following set_viewport_position works.

        # Keeping it around as a WAR until it's fixed

        # in Sublime Text 2.

        self.view.viewport_extent()

        self.view.set_viewport_position(data, False)



c_view =  GDBView('shell')

cur_path = os.getcwd()

bullet = u'\u2022'

def is_ls_command(cmd):
    cmd = cmd.strip()
    if cmd == 'ls -l':
        return False
    if cmd.startswith('ls'):
        return True
    else:
        return False

def is_cd_command(cmd):
    cmd = cmd.strip()
    if cmd.startswith('cd'):
        return True
    else:
        return False
def exec_cd_command(cur,cmd):
    cmd = cmd.strip()
    cds = cmd.split(' ')
    cur_path = None
    if len(cds) == 1:
        cur_path = os.path.abspath(os.getenv('HOME'))
    else:
        if cds[1] == '~':
            cur_path = os.path.abspath(os.getenv('HOME'))
        elif cds[1] == '..':
            cur_path = os.path.abspath(os.path.join(cur,cds[1]))
        else:
            cur_path = os.path.join(cur,cds[1])
    return cur_path

def sort_files(filename):
    total_weight = 0
    if filename[0] == '.':
        total_weight += 2
    if filename[-1] == os.sep:
        total_weight += 1
    return total_weight

def short_path(path):
    if path.startswith(os.getenv('HOME')):
        return path.replace(os.getenv('HOME'),'~')
    return path

class ShellOpenCommand(sublime_plugin.WindowCommand):

    def run(self):

        a_window = sublime.active_window()

        a_window.set_layout(

                    {

                        "cols": [0.0, 0.5, 1.0],

                        "rows": [0.0, 0.5, 1.0],

                        "cells": [[0, 0, 2, 1], [0, 1, 2, 2]]

                    } 

        )

        global c_view

        #if c_view.is_closed():
        c_view.open()

        self.window.show_input_panel(short_path(cur_path),'',self.on_done,None,None)


    def on_done(self,msg):

        global c_view
        global cur_path

        cmd = shlex.split(msg)
        path = cur_path
        proc = subprocess.Popen(msg,cwd=path,stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.PIPE,shell=True)

        output, error = proc.communicate()
        if is_ls_command(msg):
            output = output.replace('\n','\t')
            c_view.add(output)
        elif is_cd_command(msg):
            #self.open_navigator()
            cur_path = exec_cd_command(cur_path,msg)
        elif msg == 'reset':
            cur_path = os.path.abspath(os.getenv('HOME'))
        else:
            if len(output):

                c_view.add(output)

            if len(error):

                c_view.add(error)

        c_view.add('\n'+short_path(cur_path)+">>>")

        #c_view.add('=======================================\n')
        c_view.scroll()

        self.window.show_input_panel(short_path(cur_path),'',self.on_done,None,None)

    def open_navigator(self):
        global bullet
        self.dir_files = ['[' + os.getcwd() +']', bullet + ' Directory actions', '..' + os.sep, '~' + os.sep]
        for element in os.listdir(os.getcwd()):
            fullpath = os.path.join(os.getcwd(), element)
            if os.path.isdir(fullpath):
                self.dir_files.append(element + os.sep)
            else:
                self.dir_files.append(element)
        self.dir_files = self.dir_files[:4] + sorted(self.dir_files[4:], key=sort_files)
        if self.window.active_view().file_name() is not None:
            self.dir_files.insert(2, bullet + ' To current view')
        #print self.dir_files
        self.window.show_quick_panel(self.dir_files, None)

class ShellCloseCommand(sublime_plugin.WindowCommand):

    def run(self):

        global c_view

        #if not c_view.is_closed():

        c_view.close() 

        a_window = sublime.active_window()

        a_window.set_layout(

                    {

                        "cols": [0.0, 1.0],

                        "rows": [0.0,1.0],

                        "cells": [[0, 0, 1, 1]]

                    } 

        )

