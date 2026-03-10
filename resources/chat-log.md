On this screenshot there is a visualization of modules that demonstrates the courses in mediainformatics in Lübeck. Can you generate an App that allows dragging and dropping these modules between semesters?

This is the screenshot of the website. 


Drag & Drop — Module lassen sich frei zwischen allen 6 Semestern verschieben. Der Ziel-Slot leuchtet beim Darüberziehen lila auf, und ein gestrichelter Rahmen zeigt an, wo das Modul abgelegt werden kann.
KP-Tracking — Jedes Semester zeigt oben rechts das aktuelle KP-Gesamt in Echtzeit. Das Badge wird grün (= 30 KP), rot (zu viele) oder orange (zu wenige).
Farbkodierung — exakt wie im Original: Lila für MCI/Medieninformatik, Dunkelrot für Design, Grün für Psychologie, Teal für Informatik, Blau für Mathematik, Orange für Wahlpflicht.
Legende & Reset — über die Buttons oben rechts erreichbar.

Two new interactions have been added:
Modul entfernen — Hover über ein Modul, um das ✕-Symbol oben rechts einzublenden. Ein Klick öffnet einen Bestätigungsdialog, bevor das Modul wirklich gelöscht wird.
Modul hinzufügen — Jedes Semester hat jetzt einen gestrichelten „+ Modul hinzufügen"-Button. Das Modal erlaubt die Eingabe von Modulcode, Name, KP, Format (z.B. 2V+1Ü) und Kategorie — mit Farbvorschau direkt neben dem Dropdown.

Now add the edit button to each module card and the edit modal. First the card:Add edit button to module cardAdd edit button to module cardNow add the paddingRight on the module name to make room for two buttons:Adjust paddingRight on module name for two buttonsAdjust paddingRight on module name for two buttonsNow add the Edit Modal JSX right before the Delete Confirm modal:Edited a file, read a fileEdited a file, read a fileDone! Hover over any module card and you'll now see two icon buttons appear in the top-right corner — ✎ bearbeiten (left) and ✕ entfernen (right). Clicking the pencil opens a pre-filled edit modal with all fields — Modulcode, Name, KP, Format und Kategorie — that you can change and save.

I'll rewrite the file cleanly — replacing the tiny icon-only buttons with a proper hover action bar, and adding per-module drop targets for in-column reordering.Ran a command, created a file, read a fileRan a command, created a file, read a fileTwo things are now fixed and improved:
Better action buttons — Hovering a module slides in a full-width action bar at the bottom of the card with two clearly labeled, easily clickable buttons: ✎ Bearbeiten and ✕ Entfernen. No more tiny 18px circles to aim at.
In-column reordering — Dragging a module now shows a purple insertion line between cards (above or below, depending on where your cursor is in the card). This works both for reordering within the same semester and for inserting at a specific position when moving between semesters.

Deliberated JSON format and sketched export-import functionality
Deliberated JSON format and sketched export-import functionality
Now add state for import error and a hidden file input ref, plus the import handler:


Edited 2 files
Edited 2 files
Now update the header buttons and add the hidden file input + error toast:


Replace header buttons with export/import buttons and add file input
Replace header buttons with export/import buttons and add file input
Now add the import error toast and a format hint right before the closing </div> of the page:


Add error toast and format hint before closing div
Add error toast and format hint before closing div
Now add the new style entries at the end of the S object:


Edited a file, read a file
Edited a file, read a file
Export and import are now live. Here's how they work:

↓ Exportieren — Downloads a nicely formatted .json file named studienplan_mi_luebeck_YYYY-MM-DD.json. The file is fully human-readable


Can you allow an additional area "Wahlpflicht-Module" where I can add additional modules that can then be used to replace the Placehodlers in the 5th and 6th column?



I'll do a full clean rewrite — the pool needs its own drag source/destination logic woven throughout the whole drag system.Ran a command, created a file, read a fileRan a command, created a file, read a fileThe new Wahlpflicht-Module pool area lives below the semester grid. Here's how everything works:
Pool → Semester — Drag any pool card into a semester column. If you drop it directly onto a striped Platzhalter card, it replaces it in-place (keeping the same position). If you drop it between other cards, the purple insertion line shows where it'll land. The module moves out of the pool.
Semester → Pool — Drag any semester module down into the orange-bordered pool area to move it back. Useful for swapping out a Wahlpflicht module you've already placed.
Reordering in the pool — Pool cards can also be reordered among themselves with a horizontal orange insertion line.
Pool management — The pool has its own "+ Hinzufügen" button with a form defaulting to the Wahlpflicht category. Individual cards show ✎ / ✕ on hover. The pool shows the total available KP.
6 example electives are pre-loaded (Mensch-Roboter-Interaktion, Mobile Computing, etc.) to get you started. The existing Wahlpflicht placeholders in semesters 5 and 6 are now visually marked with a striped pattern and a small "Platzhalter" badge. Export/import now also saves and restores the pool.