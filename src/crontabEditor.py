# crontabEditor.py - UI code for adding a crontab record
# Copyright (C) 2004, 2005  Philip Van Hoof <me at pvanhoof dot be>
# Copyright (C) 2004 - 2009 Gaute Hope <eg at gaute dot eu dot com>
# Copyright (C) 2004, 2005  Kristof Vansant <de_lupus at pandora dot be>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

#pygtk modules
import gtk
import gobject

#python modules
import re
import os

#custom modules
import config
import crontabEditorHelper


class CrontabEditor:
    def __init__(self, parent, backend, scheduler, template):

        self.ParentClass = parent
        self.backend = backend
        self.scheduler = scheduler
        self.template = template

        self.xml = self.ParentClass.xml
        self.widget = self.xml.get_widget("crontab_editor")
        self.widget.connect("delete-event", self.widget.hide_on_delete)


        # TODO: move to crontab?
        self.fieldRegex = re.compile('^(\*)$|^([0-9]+)$|^\*\/([0-9]+)$|^([0-9]+)-([0-9]+)$|(^([0-9]+[,])+([0-9]+)$)')
        self.nooutputRegex = re.compile('([^#\n$]*)>(\s|)/dev/null\s2>&1')


        self.title_box = self.xml.get_widget ("crontab_title_box")

        self.image_icon = gtk.Image ()
        self.image_icon.set_from_pixbuf (self.ParentClass.bigiconcrontab)
        self.title_box.pack_start (self.image_icon, False, False, 0)
        self.title_box.reorder_child (self.image_icon, 0)
        self.image_icon.show ()

        self.noevents = False


        ##simple tab
        self.entry_title = self.xml.get_widget ("entry_title")
        self.entry_task = self.xml.get_widget ("entry_task")

        self.frequency_combobox = self.xml.get_widget ("frequency_combobox")
        self.frequency_combobox_model = gtk.ListStore (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
        self.frequency_combobox_model.append([_("Every minute"), ["*", "*", "*", "*", "*", ""]])
        self.frequency_combobox_model.append([_("Every hour"), ["0", "*", "*", "*", "*", ""]])
        self.frequency_combobox_model.append([_("Every day"), ["0", "0", "*", "*", "*", ""]])
        self.frequency_combobox_model.append([_("Every month"), ["0", "0", "1", "*", "*", ""]])
        self.frequency_combobox_model.append([_("Every week"), ["0", "0", "*", "*", "1", ""]])
        self.frequency_combobox_model.append([_("At reboot"), ["", "", "", "", "", "@reboot"]])
        self.frequency_combobox.set_model (self.frequency_combobox_model)

        self.cb_output = self.xml.get_widget ("combo_output")
        self.cb_o_model = gtk.ListStore (gobject.TYPE_STRING, gobject.TYPE_INT)
        self.cb_o_model.append ([self.ParentClass.output_strings[0], 0])
        self.cb_o_model.append ([self.ParentClass.output_strings[1], 1])
        self.cb_o_model.append ([self.ParentClass.output_strings[2], 2])
        self.cb_o_model.append ([self.ParentClass.output_strings[3], 3])
        self.cb_output.set_model (self.cb_o_model)
        cell = gtk.CellRendererText ()
        self.cb_output.pack_start (cell, True)
        self.cb_output.add_attribute (cell, "text", 0)

        self.button_cancel = self.xml.get_widget ("button_cancel")
        self.button_apply = self.xml.get_widget ("button_apply")
        self.button_template = self.xml.get_widget ("button_template")
        self.rb_advanced = self.xml.get_widget ("rb_advanced")
        self.rb_basic = self.xml.get_widget ("rb_basic")

        self.label_preview = self.xml.get_widget ("label_preview")

        self.xml.signal_connect("on_button_cancel_clicked", self.on_button_cancel_clicked)
        self.xml.signal_connect("on_button_apply_clicked", self.on_button_apply_clicked)
        self.xml.signal_connect("on_anyadvanced_entry_changed", self.on_anyadvanced_entry_changed)
        self.xml.signal_connect("on_anybasic_entry_changed", self.on_anybasic_entry_changed)
        self.xml.signal_connect("on_frequency_combobox_changed", self.on_frequency_combobox_changed)
        self.xml.signal_connect ("on_combo_output_changed", self.on_anybasic_entry_changed)

        self.xml.signal_connect("on_help_clicked", self.on_fieldHelp_clicked)

        self.xml.signal_connect("on_rb_advanced_toggled", self.on_editmode_toggled)
        self.xml.signal_connect("on_rb_basic_toggled", self.on_editmode_toggled)

        self.xml.signal_connect ("on_button_template_clicked", self.on_template_clicked)

        ##advanced
        self.minute_entry = self.xml.get_widget ("minute_entry")
        self.hour_entry = self.xml.get_widget ("hour_entry")
        self.day_entry = self.xml.get_widget ("day_entry")
        self.month_entry = self.xml.get_widget ("month_entry")
        self.weekday_entry = self.xml.get_widget ("weekday_entry")

        self.help_minute = self.xml.get_widget ("help_minute")
        self.help_hour = self.xml.get_widget ("help_hour")
        self.help_day = self.xml.get_widget ("help_day")
        self.help_month = self.xml.get_widget ("help_month")
        self.help_weekday = self.xml.get_widget ("help_weekday")

        self.editorhelper = crontabEditorHelper.CrontabEditorHelper(self)



    def showadd (self, transient):
        self.button_apply.set_label (gtk.STOCK_ADD)
        self.__reset__ ()
        self.mode = 0
        self.widget.set_title(_("Create a New Scheduled Task"))
        self.widget.set_transient_for(transient)
        self.widget.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.button_template.show ()
        self.widget.show ()
        self.cb_output.set_active (0)

    def showadd_template (self, transient, title, command, output,timeexpression):
        self.button_apply.set_label (gtk.STOCK_ADD)
        self.__reset__ ()
        self.mode = 0
        self.widget.set_title(_("Create a New Scheduled Task"))
        self.widget.set_transient_for(transient)
        self.widget.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.button_template.show ()
        self.widget.show ()

        self.output = output
        # hehe again, why make it less complicated..
        timeexpression = timeexpression + " echo hehe"
        self.minute, self.hour, self.day, self.month, self.weekday, hehe = self.scheduler.parse (timeexpression, True)
        self.special = ""
        if self.minute == "@reboot":
            self.special = "@reboot"
            self.minute = ""
            self.day = ""
            self.hour = ""
            self.month = ""
            self.weekday = ""
        self.command = command
        self.title = title

        self.__update_textboxes__ ()

        i = self.__getfrequency__ (self.minute, self.hour, self.day, self.month, self.weekday, self.special)
        if i == -1:
            # advanced
            self.rb_advanced.set_active (True)
        else:
            self.rb_basic.set_active (True)
            self.frequency_combobox.set_active (i)

        self.cb_output.set_active (self.output)


    def showedit_template (self, transient, id, title, command, output, timeexpression):
        self.button_apply.set_label (gtk.STOCK_SAVE)

        self.mode = 2
        self.tid = id
        self.__reset__ ()

        self.command = command
        self.title = title
        self.output = output

        timeexpression = timeexpression + " echo hehe"
        self.minute, self.hour, self.day, self.month, self.weekday, hehe = self.scheduler.parse (timeexpression, True)
        self.special = ""
        if self.minute == "@reboot":
            self.special = "@reboot"
            self.minute = ""
            self.day = ""
            self.hour = ""
            self.month = ""
            self.weekday = ""

        self.widget.set_title(_("Edit template"))
        self.__update_textboxes__ ()

        self.widget.set_transient_for(transient)
        self.widget.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.widget.show ()
        self.button_template.hide ()
        i = self.__getfrequency__ (self.minute, self.hour, self.day, self.month, self.weekday, self.special)
        if i == -1:
            # advanced
            self.rb_advanced.set_active (True)
        else:
            self.rb_basic.set_active (True)
            self.frequency_combobox.set_active (i)

        self.cb_output.set_active (self.output)

    def shownew_template (self, transient):
        self.button_apply.set_label (gtk.STOCK_ADD)

        self.mode = 2
        self.tid = 0
        self.__reset__ ()


        self.widget.set_title(_("New template"))
        self.__update_textboxes__ ()

        self.widget.set_transient_for(transient)
        self.widget.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.widget.show ()
        self.button_template.hide ()


    def showedit (self, transient, record, job_id, linenumber, iter):
        self.button_apply.set_label (gtk.STOCK_APPLY)
        self.mode = 1
        self.linenumber = linenumber
        self.record = record
        self.job_id = job_id
        self.__reset__ ()
        (self.minute, self.hour, self.day, self.month, self.weekday, self.command, self.comment, self.job_id, self.title, self.desc, self.output, display) = self.scheduler.parse (record)[1]
        self.special = ""
        if self.minute == "@reboot":
            self.special = "@reboot"
            self.minute = ""
            self.day = ""
            self.hour = ""
            self.month = ""
            self.weekday = ""

        self.widget.set_title(_("Edit a Scheduled Task"))
        self.__update_textboxes__ ()
        self.parentiter = iter
        self.widget.set_transient_for(transient)
        self.widget.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.button_template.show ()
        self.widget.show ()
        i = self.__getfrequency__ (self.minute, self.hour, self.day, self.month, self.weekday, self.special)
        if i == -1:
            # advanced
            self.rb_advanced.set_active (True)
        else:
            self.rb_basic.set_active (True)
            self.frequency_combobox.set_active (i)

        self.cb_output.set_active (self.output)

    def __reset__ (self):
        self.noevents = True
        self.minute = "0"
        self.hour = "*"
        self.day = "*"
        self.month = "*"
        self.weekday = "*"
        self.special = ""
        self.command = "ls"
        self.title = _("Untitled")
        self.output = 0
        self.frequency_combobox.set_active (1)
        self.rb_basic.set_active (True)
        self.minute_entry.set_editable (False)
        self.minute_entry.set_sensitive (False)
        self.hour_entry.set_editable (False)
        self.hour_entry.set_sensitive (False)
        self.day_entry.set_editable (False)
        self.day_entry.set_sensitive (False)
        self.month_entry.set_editable (False)
        self.month_entry.set_sensitive (False)
        self.weekday_entry.set_editable (False)
        self.weekday_entry.set_sensitive (False)
        self.help_minute.set_sensitive (False)
        self.help_hour.set_sensitive (False)
        self.help_day.set_sensitive (False)
        self.help_month.set_sensitive (False)
        self.help_weekday.set_sensitive (False)
        self.cb_output.set_active (0)
        self.frequency_combobox.set_sensitive (True)
        self.__update_textboxes__ ()
        self.noevents = False


    #error dialog box
    def __WrongRecordDialog__ (self, x, y, z):
        self.wrongdialog = gtk.MessageDialog(self.widget, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, (_("This is an invalid record! The problem could be in the %(field)s field. Reason: %(reason)s") % (y, z)))
        self.wrongdialog.run()
        self.wrongdialog.destroy()

    def __dialog_command_failed__ (self):
        self.wrongdialog2 = gtk.MessageDialog(self.widget, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, (_("Your command contains one or more of the character %, this is special for cron and cannot be used with Gnome-schedule because of the format it uses to store extra information on the crontab line. Please use the | redirector character to achieve the same functionality. Refer to the crontab manual for more information about the % character. If you don not want to use it for redirection it must be properly escaped with the \ letter.")))
        self.wrongdialog2.run()
        self.wrongdialog2.destroy()

    def __check_field_format__ (self, field, type):
        try:
            # Type should not be translatable!
            self.scheduler.checkfield (field, type)
        except ValueError, ex:
            raise ex

    def on_editmode_toggled (self, widget, *args):
        if widget.get_active() == True:
            if self.noevents == False:
                self.noevents = True
                if widget.get_name () == self.rb_advanced.get_name ():
                    self.rb_basic.set_active (False)
                    if (self.frequency_combobox.get_active () == 5):
                        # reboot, standard every hour
                        self.special = ""
                        self.minute_entry.set_text ("0")
                        self.hour_entry.set_text ("*")
                        self.day_entry.set_text ("*")
                        self.month_entry.set_text ("*")
                        self.weekday_entry.set_text ("*")
                        self.minute = "0"
                        self.hour = "*"
                        self.day = "*"
                        self.month = "*"
                        self.weekday = "*"

                        self.update_preview ()

                    self.rb_advanced.set_active (True)
                    self.minute_entry.set_editable (True)
                    self.minute_entry.set_sensitive (True)
                    self.hour_entry.set_editable (True)
                    self.hour_entry.set_sensitive (True)
                    self.day_entry.set_editable (True)
                    self.day_entry.set_sensitive (True)
                    self.month_entry.set_editable (True)
                    self.month_entry.set_sensitive (True)
                    self.weekday_entry.set_editable (True)
                    self.weekday_entry.set_sensitive (True)
                    self.help_minute.set_sensitive (True)
                    self.help_hour.set_sensitive (True)
                    self.help_day.set_sensitive (True)
                    self.help_month.set_sensitive (True)
                    self.help_weekday.set_sensitive (True)
                    self.frequency_combobox.set_sensitive (False)
                else:
                    self.rb_basic.set_active (True)
                    self.rb_advanced.set_active (False)
                    self.minute_entry.set_editable (False)
                    self.minute_entry.set_sensitive (False)
                    self.hour_entry.set_editable (False)
                    self.hour_entry.set_sensitive (False)
                    self.day_entry.set_editable (False)
                    self.day_entry.set_sensitive (False)
                    self.month_entry.set_editable (False)
                    self.month_entry.set_sensitive (False)
                    self.weekday_entry.set_editable (False)
                    self.weekday_entry.set_sensitive (False)
                    self.help_minute.set_sensitive (False)
                    self.help_hour.set_sensitive (False)
                    self.help_day.set_sensitive (False)
                    self.help_month.set_sensitive (False)
                    self.help_weekday.set_sensitive (False)
                    self.frequency_combobox.set_sensitive (True)
                    self.on_frequency_combobox_changed (self.frequency_combobox)
                self.noevents = False


    def on_button_cancel_clicked (self, *args):
        self.widget.hide()

    def on_template_clicked (self, *args):
        if self.special != "":
            try:
                self.__check_field_format__ (self.special, "special")
                record = self.special + " " + self.command
                self.minute = "@reboot"
                self.hour = "@reboot"
                self.day = "@reboot"
                self.month = "@reboot"
                self.weekday = "@reboot"
            except ValueError, ex:
                x, y, z = ex
                self.__WrongRecordDialog__ (x, y, z)
                return
        else:
            try:
                # Type should not be translatable!
                self.__check_field_format__ (self.minute, "minute")
                self.__check_field_format__ (self.hour, "hour")
                self.__check_field_format__ (self.day, "day")
                self.__check_field_format__ (self.month, "month")
                self.__check_field_format__ (self.weekday, "weekday")
                record = self.minute + " " + self.hour + " " + self.day + " " + self.month + " " + self.weekday + " " + self.command
            except ValueError, ex:
                x, y, z = ex
                self.__WrongRecordDialog__ (x, y, z)
                return

        if self.scheduler.check_command (self.command) == False:
            self.__dialog_command_failed__ ()
            return  False

        if self.special != "":
            self.template.savetemplate_crontab (0, self.title, self.command, self.output, self.special)
        else:
            self.template.savetemplate_crontab (0, self.title, self.command, self.output, self.minute + " " + self.hour + " " + self.day + " " + self.month + " " + self.weekday)

        self.widget.hide ()

    def on_button_apply_clicked (self, *args):
        if self.special != "":
            try:
                self.__check_field_format__ (self.special, "special")
                record = self.special + " " + self.command
                self.minute = "@reboot"
                self.hour = "@reboot"
                self.day = "@reboot"
                self.month = "@reboot"
                self.weekday = "@reboot"
            except ValueError, ex:
                x, y, z = ex
                self.__WrongRecordDialog__ (x, y, z)
                return
        else:
            try:
                # Type should not be translatable!
                self.__check_field_format__ (self.minute, "minute")
                self.__check_field_format__ (self.hour, "hour")
                self.__check_field_format__ (self.day, "day")
                self.__check_field_format__ (self.month, "month")
                self.__check_field_format__ (self.weekday, "weekday")
                record = self.minute + " " + self.hour + " " + self.day + " " + self.month + " " + self.weekday + " " + self.command
            except ValueError, ex:
                x, y, z = ex
                self.__WrongRecordDialog__ (x, y, z)
                return

        if self.scheduler.check_command (self.command) == False:
            self.__dialog_command_failed__ ()
            return  False


        if (self.backend.get_not_inform_working_dir_crontab() != True):
            dia2 = gtk.MessageDialog (self.widget, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE, _("Note about working directory of executed tasks:\n\nRecurrent tasks will be run from the home directory."))
            dia2.add_buttons (_("_Don't show again"), gtk.RESPONSE_CLOSE, gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            dia2.set_title (_("Warning: Working directory of executed tasks"))
            response = dia2.run ()
            if response == gtk.RESPONSE_CANCEL:
                dia2.destroy ()
                del dia2
                return
            elif response == gtk.RESPONSE_CLOSE:
                self.backend.set_not_inform_working_dir_crontab (True)
            else:
                pass
            dia2.destroy ()
            del dia2

        if self.mode == 1:
            self.scheduler.update (self.minute, self.hour, self.day, self.month, self.weekday, self.command, self.linenumber, self.parentiter, self.output, self.job_id, self.comment, self.title, self.desc)

        elif self.mode == 0:
            self.scheduler.append (self.minute, self.hour, self.day, self.month, self.weekday, self.command, self.output, self.title)

        elif self.mode == 2:
            if self.special != "":
                try:
                    self.__check_field_format__ (self.special, "special")
                    record = self.special + " " + self.command
                    self.minute = "@reboot"
                    self.hour = "@reboot"
                    self.day = "@reboot"
                    self.month = "@reboot"
                    self.weekday = "@reboot"
                except ValueError, ex:
                    x, y, z = ex
                    self.__WrongRecordDialog__ (x, y, z)
                    return
            else:
                try:
                    # Type should not be translatable!
                    self.__check_field_format__ (self.minute, "minute")
                    self.__check_field_format__ (self.hour, "hour")
                    self.__check_field_format__ (self.day, "day")
                    self.__check_field_format__ (self.month, "month")
                    self.__check_field_format__ (self.weekday, "weekday")
                    record = self.minute + " " + self.hour + " " + self.day + " " + self.month + " " + self.weekday + " " + self.command
                except ValueError, ex:
                    x, y, z = ex
                    self.__WrongRecordDialog__ (x, y, z)
                    return

            if self.scheduler.check_command (self.command) == False:
                self.__dialog_command_failed__ ()
                return  False

            if self.special != "":
                self.template.savetemplate_crontab (self.tid, self.title, self.command, self.output, self.special)
            else:
                self.template.savetemplate_crontab (self.tid, self.title, self.command, self.output, self.minute + " " + self.hour + " " + self.day + " " + self.month + " " + self.weekday)

            self.widget.hide ()
            return

        self.ParentClass.schedule_reload ()
        self.widget.hide ()


    def __set_frequency_combo__ (self):
        if self.noevents == False:
            index = self.__getfrequency__ (self.minute, self.hour, self.day, self.month, self.weekday, self.special)
            if index != -1:
                self.frequency_combobox.set_active (index)
            else:
                self.rb_advanced.set_active (True)


    def __getfrequency__ (self, minute, hour, day, month, weekday, special):
        index = -1

        if minute == "*" and hour == "*" and month == "*" and day == "*" and weekday == "*":
            index = 0
        if minute == "0" and hour == "*" and month == "*" and day == "*" and weekday == "*":
            index = 1
        if minute == "0" and hour == "0" and month == "*" and day == "*" and weekday == "*":
            index = 2
        if minute == "0" and hour == "0" and month == "*" and day == "1" and weekday == "*":
            index = 3
        if minute == "0" and hour == "0" and month == "*" and day == "*" and weekday == "1":
            index = 4
        if special != "":
            index = 5


        return index


    def __update_textboxes__ (self):
        self.noevents = True
        self.cb_output.set_active (self.output)
        self.entry_task.set_text (self.command)
        self.entry_title.set_text (self.title)
        self.minute_entry.set_text (self.minute)
        self.hour_entry.set_text (self.hour)
        self.day_entry.set_text (self.day)
        self.month_entry.set_text (self.month)
        self.weekday_entry.set_text (self.weekday)
        self.update_preview ()
        #self.__set_frequency_combo__()
        self.noevents = False

    def update_preview (self):
        if self.special != "":
            try:
                self.__check_field_format__ (self.special, "special")
                record = self.special + " " + self.command
                minute = "@reboot"
                hour = "@reboot"
                day = "@reboot"
                month = "@reboot"
                weekday = "@reboot"
                self.label_preview.set_text ("<b>" + self.scheduler.__easy__ (minute, hour, day, month, weekday) + "</b>")

            except ValueError, ex:
                x, y, z = ex
                self.label_preview.set_text (_("This is an invalid record! The problem could be in the %(field)s field. Reason: %(reason)s") % ({'field' : y, 'reason' : z}))


        else:
            try:
                # Type should not be translatable!
                self.__check_field_format__ (self.minute, "minute")
                self.__check_field_format__ (self.hour, "hour")
                self.__check_field_format__ (self.day, "day")
                self.__check_field_format__ (self.month, "month")
                self.__check_field_format__ (self.weekday, "weekday")

                # Day of Month
                # Crontab bug? Let's not support
                # dom behaves like minute
                """
                dom = self.day
                if dom.isdigit() == False:
                    dom = dom.lower ()
                    for day in self.scheduler.downumbers:
                        dom = dom.replace (day, self.scheduler.downumbers[day])
                """

                # Month of Year
                moy = self.month
                if moy.isdigit () == False:
                    moy = moy.lower ()
                    for m in self.scheduler.monthnumbers:
                        moy = moy.replace (m, self.scheduler.monthnumbers[m])


                # Day of Week
                dow = self.weekday
                if dow.isdigit() == False:
                    dow = dow.lower ()
                    for day in self.scheduler.downumbers:
                        dow = dow.replace (day, self.scheduler.downumbers[day])
                self.label_preview.set_text ("<b>" + self.scheduler.__easy__ (self.minute, self.hour, self.day, moy, dow) + "</b>")
            except ValueError, ex:
                x, y, z = ex
                self.label_preview.set_text (_("This is an invalid record! The problem could be in the %(field)s field. Reason: %(reason)s") % ({'field' : y, 'reason' : z}))

        self.label_preview.set_use_markup (True)


    def on_anyadvanced_entry_changed (self, *args):
        if self.noevents == False:
            self.minute = self.minute_entry.get_text ()
            self.hour = self.hour_entry.get_text ()
            self.day = self.day_entry.get_text ()
            self.month = self.month_entry.get_text ()
            self.weekday = self.weekday_entry.get_text ()
            self.output = self.cb_output.get_active()

            self.__update_textboxes__ ()


    def on_anybasic_entry_changed (self, *args):
        if self.noevents == False:
            self.command = self.entry_task.get_text ()
            self.title = self.entry_title.get_text ()
            self.output = self.cb_output.get_active()
            self.__update_textboxes__ ()


    def on_frequency_combobox_changed (self, bin):
        iter = self.frequency_combobox.get_active_iter ()
        frequency = self.frequency_combobox_model.get_value(iter, 1)
        if frequency != None:
            self.minute, self.hour, self.day, self.month, self.weekday, self.special = frequency
            self.__update_textboxes__()


    def on_fieldHelp_clicked(self, widget, *args):
        name = widget.get_name()
        field = "minute"
        if name == "help_minute" :
            field = "minute"
            expression = self.minute_entry.get_text()
        if name == "help_hour" :
            field = "hour"
            expression = self.hour_entry.get_text()
        if name == "help_day" :
            field = "day"
            expression = self.day_entry.get_text()
        if name == "help_month" :
            field = "month"
            expression = self.month_entry.get_text()
        if name == "help_weekday" :
            field = "weekday"
            expression = self.weekday_entry.get_text()

        self.editorhelper.show (field, expression)

