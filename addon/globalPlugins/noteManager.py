# NVDA Add-on: noteManager
# Copyright (C) 2022 - 2023 David CM
# This add-on is free software, licensed under the terms of the GNU General Public License (version 2).
# See the file LICENSE for more details.

import api, bz2, config, globalPluginHandler, globalVars, gui, addonHandler, os, pickle, tones, weakref, wx, ui

from gui import guiHelper, nvdaControls
from gui.dpiScalingHelper import DpiScalingHelperMixin, DpiScalingHelperMixinWithoutInit
from scriptHandler import script

addonHandler.initTranslation()


def loadFile(path):
	b = bz2.BZ2File(path, "rb")
	return pickle.load(b	)


def saveFile(d, path):
	f= bz2.BZ2File(path, "wb")
	pickle.dump(d, f, 4)
	f.close()


NOTE_FILE = "notes.dat"
pathFile = os.path.abspath(os.path.join(globalVars.appArgs.configPath, NOTE_FILE))

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	# Translators: script category for add-on gestures
	scriptCategory = _("Note manager")

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.modified = False
		try:
			self.notes = loadFile(pathFile)
			self.curNote = 0
		except:
			self.notes = []
			self.curNote = -1

	def save(self):
		if self.modified:
			saveFile(self.notes, pathFile)
			self.modified = False	

	def newNote(self, text, index=None, update=False):
		if index == None:
			self.notes.append(text)
			index = len(self.notes) -1
			self.curNote = index
		else:
			if update:
				self.notes[index] = text
			else:
				self.notes.insert(index, text)
		self.modified = True
		return index

	def removeNote(self, index):
		del self.notes[index]
		self.modified = True

	def isNotes(self):
		if len(self.notes) == 0:
			ui.message(_("no notes available"))
			return False
		else:
			return True

	@script(
		# Translators: Documentation string for copy currently selected item script
		_("Copy the currently selected note to the clipboard, which by default will be the most recently added note."),
		gesture="kb:nvda+alt+m"
	)
	def script_copyCurNote(self, gesture):
		if not self.isNotes() or self.curNote == -1:
			return
		text = self.notes[self.curNote]
		if api.copyToClip(text):
			tones.beep(1500, 120)

	@script(
		# Translators: Documentation string for previous note item script
		_("Review the previous item in NVDA's note manager."),
		gesture="kb:nvda+alt+b"
	)
	def script_prevNote(self, gesture):
		if not self.isNotes():
			return
		self.curNote += 1
		if self.curNote >= len(self.notes):
			tones.beep(220, 100, 100)
			self.curNote -= 1
		ui.message(self.notes[self.curNote])

	@script(
		# Translators: Documentation string for next note item script
		_("Review the next item in NVDA's note manager."),
		gesture="kb:nvda+alt+n"
	)
	def script_nextNote(self, gesture):
		if not self.isNotes():
			return
		self.curNote -= 1
		if self.curNote < 0:
			tones.beep(220, 100, 0, 50)
			self.curNote += 1
		ui.message(self.notes[self.curNote])

	@script(
		# Translators: Documentation string for show in a dialog all notes saved in the note manager.
		_("Opens a dialog showing all notes saved in note manager"),
		gesture="kb:nvda+windows+s"
	)
	def script_showNotesDialog(self, gesture):
		gui.mainFrame.prePopup()
		NotesDialog(gui.mainFrame, self).Show()
		gui.mainFrame.postPopup()

	def terminate(self, *args, **kwargs):
		super().terminate(*args, **kwargs)

	"""
	TODO
	"kb:nvda+alt+r": "recordNote",
	"kb:nvda+alt+v": "writeNote",
	"""


class NotesDialog(
		DpiScalingHelperMixinWithoutInit,
		gui.contextHelp.ContextHelpMixin,
		wx.Dialog  # wxPython does not seem to call base class initializer, put last in MRO
):
	@classmethod
	def _instance(cls):
		""" type: () -> NotesDialog
		return None until this is replaced with a weakref.ref object. Then the instance is retrieved
		with by treating that object as a callable.
		"""
		return None

	helpId = "NoteManagerList"

	def __new__(cls, *args, **kwargs):
		instance = NotesDialog._instance()
		if instance is None:
			return super(NotesDialog, cls).__new__(cls, *args, **kwargs)
		return instance

	def __init__(self, parent, addon):
		if NotesDialog._instance() is not None:
			return
		NotesDialog._instance = weakref.ref(self)
		# Translators: The title of the Notes manager Dialog
		title = _("Notes manager")
		super().__init__(
			parent,
			title=title,
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
		)
		# hte add-on instance
		self.addon = addon

		# the results of a search, it's a pair of note / index. initially equals to notes.
		self.searchNotes = None
		# indexes of search, to save the selected item in a specific search.
		self.searches = {"": 0}
		# the current search, initially "".
		self.curSearch = ""
		# the indexes of items selected.
		self.selection = set()

		szMain = guiHelper.BoxSizerHelper(self, sizer=wx.BoxSizer(wx.VERTICAL))
		szCurrent = guiHelper.BoxSizerHelper(self, sizer=wx.BoxSizer(wx.HORIZONTAL))
		szBottom = guiHelper.BoxSizerHelper(self, sizer=wx.BoxSizer(wx.HORIZONTAL))

		# Translators: the label for the search text field in the notes manager add-on.
		self.searchTextFiel = szMain.addLabeledControl(_("&Search"),
			wx.TextCtrl,
			style =wx.TE_PROCESS_ENTER
		)
		self.searchTextFiel.Bind(wx.EVT_TEXT_ENTER, self.onSearch)
		self.searchTextFiel.Bind(wx.EVT_KILL_FOCUS, self.onSearch)

		# Translators: the label for the history elements list in the notes manager add-on.
		entriesLabel = _("Notes")
		self.noteList = nvdaControls.AutoWidthColumnListCtrl(
			parent=self,
			autoSizeColumn=1,
			style=wx.LC_REPORT|wx.LC_NO_HEADER
			)
		
		szMain.addItem(
			self.noteList,
			flag=wx.EXPAND,
			proportion=4
		)

		# This list consists of only one column.
		# The provided column header is just a placeholder, as it is hidden due to the wx.LC_NO_HEADER style flag.
		self.noteList.InsertColumn(0, entriesLabel)
		self.noteList.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelect)
		self.noteList.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onDeselect)

		# a multiline text field containing the text from the current selected element.
		self.currentNoteField= szCurrent.addItem(
			wx.TextCtrl(self, style =wx.TE_MULTILINE),
			flag=wx.EXPAND,
			proportion=1
		)
		self.currentNoteField.Bind(wx.EVT_KILL_FOCUS, self.onNoteUpdate)

		# Translators: the label for the copy button in the notes Manager add-on.
		self.copyButton = szCurrent.addItem(wx.Button(self, label=_("&Copy item")), proportion=0)
		self.copyButton.Bind(wx.EVT_BUTTON, self.onCopy)

		# Translators: the label for the delete button in the notes Manager add-on.
		self.deleteButton = szCurrent.addItem(wx.Button(self, label=_("&Delete note")), proportion=0)
		self.deleteButton.Bind(wx.EVT_BUTTON, self.onDelete)

		szMain.addItem(
			szCurrent.sizer,
			border=guiHelper.BORDER_FOR_DIALOGS,
			flag = wx.EXPAND,
			proportion=1,
		)

		szMain.addItem(
			wx.StaticLine(self),
			border=guiHelper.BORDER_FOR_DIALOGS,
			flag=wx.ALL | wx.EXPAND
		)

		# Translators: the label for the copy all button in the notes Manager add-on. This is based on the current search.
		self.copyAllButton = szBottom.addItem(wx.Button(self, label=_("Copy &all")))
		self.copyAllButton.Bind(wx.EVT_BUTTON, self.onCopyAll)

		# Translators: the label for the new note button in the notes Manager add-on. This is based on the current search.
		self.newNoteButton = szBottom.addItem(wx.Button(self, label=_("&New note")))
		self.newNoteButton.Bind(wx.EVT_BUTTON, self.onNewNote)

		''' to do"""
		# Translators: the label for the clear notes button in the notes Manager add-on.
		self.clearNotesButton = szBottom.addItem(wx.Button(self, label=_("Clean notes")))
		self.clearNotesButton .Bind(wx.EVT_BUTTON, self.onClear) '''

		# Translators: The label of a button to close the notes Manager dialog.
		closeButton = wx.Button(self, label=_("C&lose"), id=wx.ID_CLOSE)
		closeButton.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
		szBottom.addItem(closeButton)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.EscapeId = wx.ID_CLOSE

		szMain.addItem(
			szBottom.sizer,
			border=guiHelper.BORDER_FOR_DIALOGS,
			flag=wx.ALL | wx.EXPAND,
			proportion=1,
		)
		szMain = szMain.sizer
		szMain.Fit(self)
		self.SetSizer(szMain)
		self.doSearch()

		self.SetMinSize(szMain.GetMinSize())
		# Historical initial size, result of L{self.noteList} being (550, 350)
		# Setting an initial size on L{self.noteList} by passing a L{size} argument when
		# creating the control would also set its minimum size and thus block the dialog from being shrunk.
		self.SetSize(self.scaleSize((763, 509)))
		self.CentreOnScreen()
		self.searchTextFiel.SetFocus()

	def doSearch(self, text=""):
		self.selection = set()
		if not text:
			self.searchNotes = list(enumerate(self.addon.notes))
		else:
			self.searchNotes = [k for k in enumerate(self.addon.notes) if text in k[1].lower()]
		self.noteList.DeleteAllItems()
		self.currentNoteField.SetValue("")
		self.currentNoteField.SetEditable(False)
		for k in self.searchNotes: self.noteList.Append((k[1][0:100],))
		if len(self.searchNotes) > 0:
			index = self.searches.get(text, 0)
			self.setFocusItem(index)

	def setFocusItem(self, index):
		if len(self.searchNotes) == 0:
			self.currentNoteField.SetValue("")
			self.noteList.ClearAll()
			return
		if index == -1 or index >= len(self.searchNotes):
			index = len(self.searchNotes) -1
		note = self.searchNotes[index]
		self.selection = {index}
		self.currentNoteField.SetValue(note[1])
		self.currentNoteField.SetEditable(True)
		self.noteList.Select(index, on=1)
		self.noteList.SetItemState(index,wx.LIST_STATE_FOCUSED,wx.LIST_STATE_FOCUSED)

	def updateSelection(self):
		self.currentNoteField.SetValue(self.itemsToString(sorted(self.selection)))
		if len(self.selection) > 1:
			self.currentNoteField.SetEditable(False)
		else:
			self.currentNoteField.SetEditable(True)

	def itemsToString(self, items):
		s = ""
		for k in items:
			s += self.searchNotes[k][1] +"\n"
		if s: s= s[0:-1]
		return s

	def onSearch(self, evt=None, t=""):
		if evt: t = self.searchTextFiel.GetValue().lower()
		index = self.noteList.GetFocusedItem()
		self.searches[self.curSearch] = index
		self.curSearch = t
		self.doSearch(t)

	def onClose(self,evt):
		self.onNoteUpdate()
		self.DestroyChildren()
		self.Destroy()

	def onCopy(self,evt):
		t = self.currentNoteField.GetValue()
		if t:
			if api.copyToClip(t):
				tones.beep(1500, 120)

	def onCopyAll(self, evt):
		t = self.itemsToString(range(0, len(self.searchNotes)))
		if t and api.copyToClip(t):
			tones.beep(1500, 120)

	def onSelect(self, evt):
		index=evt.GetIndex()
		self.selection.add(index)
		self.updateSelection()

	def onDeselect(self, evt):
		index=evt.GetIndex()
		if index in self.selection:
			self.selection.remove(index)
		self.updateSelection()

	def onNewNote(self, evt):
		newIndex = len(self.addon.notes)
		self.searches[""] = newIndex
		self.addon.notes.append("")
		self.searchNotes.append((newIndex, ""))
		self.noteList.Append(("",))
		newIndex = len(self.searchNotes)-1
		self.setFocusItem(newIndex)
		self.currentNoteField.SetFocus()

	def onDelete(self, evt):
		if len(self.selection) > 1 or len(self.searchNotes) == 0:
			return
		curIndex = self.noteList.GetFocusedItem()
		nIndex = self.searchNotes[curIndex][0]
		self.addon.removeNote(nIndex)
		self.addon.save()
		self.onSearch(None, self.curSearch)

	def onNoteUpdate(self, evt=None):
		if len(self.selection) > 1 or len(self.searchNotes) == 0:
			return
		text = self.currentNoteField.GetValue()
		index = self.noteList.GetFocusedItem()
		origIndex, oldText = self.searchNotes[index]
		if text != oldText:
			self.addon.newNote(text, origIndex, True)
			self.addon.save()
			tones.beep(1500, 120)
			if evt:
				e = self.noteList.SetItemText(index, text[0:100])
				self.searchNotes[index] = (origIndex, text)
