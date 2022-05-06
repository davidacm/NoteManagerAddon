# Note manager add-on

This add-on allows you to create, save, select, and copy your own notes. E.G, a message that you use very often, a reminder or annotation, etc.
## features:

* save the notes in a file, so your notes will be available even after restart NVDA.
* A dialog to manage and review the notes.
* search notes in the note manager dialog.
* You can review, multi-select items and copy the current item or items selected in the note manager dialog.
* gestures to review the notes without open the note manager.

## Usage.
	
	* Open the note manager, with focus in the search field: NVDA + windows + s.



### Note manager dialog.

In this dialog, you will be focused in the search text field. You can see the list of notes by pressing tab key. You can navigate the items by using up and down arrow keys. Each element will show just 100 characters, but you can see the entire contend by pressing tab key in a multiline text edit field.
In the multiline text edit field you can edit the note, the note will be saved when this field loses the focus or the entire dialog is closed. No confirmation is needed, because this addon is intended to take quick notes without assle. If you select multiple items, then the edit field to see the notes, will be read only because you can't edit multiple notes at the same time.

You can search in the entire list of notes in the search edit field. Type some letters or words and then, press enter. The list of items will be updated according to your search. To clean the search, just clean the text in the search edit field, and press enter.

Also, a search will be made if you are in the search field, and the field loses the focus. E.G, by pressing tab or focus another control in some another way.

You can copy the current selected items, by using the copy button. This will copy all text shown in the field that contains all items selected.
Also, you can copy all current items with "Copy all" button. This will copy just the current items shown in the list, each one will be separated by a newline. If you searched something, then this button will only copy the items found.

If you want to select more than one item, use same keys as on windows. E.G, shift + up and down arrow keys to do contiguous selection, control + the same keys to do uncontiguous selection.
To close this dialog, press escape or close button.

## Things to do.

* Open a dialog to create a new note, without using the note manager.
* create note from the clipboard.
* create a note from selection.
