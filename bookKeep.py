import sublime, sublime_plugin, re

class bookkeepCommand(sublime_plugin.TextCommand):
	def run(self, edit, targetregion=None):
		view = self.view

		def updateNextMatch(regionStart, regionEnd, acc):
			regionText = view.substr(sublime.Region(regionStart, regionEnd))
			found_at_pos = regionText.find("[" + acc + "=")
			if found_at_pos > -1:
				found_old_bal = re.search(r"=[ \t]*(?:\$-|-\$|\$|-)?[\d(,.) \t]+", regionText[found_at_pos:])
				if found_old_bal:
					old_bal_start = regionStart + found_at_pos + found_old_bal.start()
					old_bal_end = regionStart + found_at_pos + found_old_bal.end()
					view.replace(edit, sublime.Region(old_bal_start, old_bal_end), view.settings().get("arith_result"))	# update the bal b/d

					line_rest = view.substr(sublime.Region(old_bal_end, view.line(old_bal_end).end()))
					found_next_bal = re.search(r"=[ \t]*(?:\$-|-\$|\$|-)?[\d(,.) \t]+(?=])", line_rest)
					if found_next_bal:
						next_bal_start = old_bal_end + found_next_bal.start()
						next_bal_end = old_bal_end + found_next_bal.end()
						view.replace(edit, sublime.Region(next_bal_start, next_bal_end), "")	# ditch the old one

						nbs = str(next_bal_start); nbs_region = 'sublime.Region(' + nbs + ', ' + nbs + ')'
						view.run_command('bookkeep', {'targetregion': nbs_region})	# recalc for a new one
						return [True, regionStart + found_at_pos, next_bal_start + len(view.settings().get("arith_result")) + 1]
			return [False, -1, -1]

		thisRegion = eval(targetregion) if targetregion else view.sel()[0]
		expr = ""; thisPoint = -1
		if thisRegion.end() == thisRegion.begin():
			thisPoint = thisRegion.begin()
			if thisPoint > 1:
				pos = thisPoint; char = view.substr(sublime.Region(pos - 1, pos))
				while char in "0123456789(.,$) +-*/" and pos > 1:
					expr = char + expr; pos -= 1; char = view.substr(sublime.Region(pos - 1, pos))
		else:
			for char in view.substr(thisRegion):
				if char not in "0123456789(.,$) +-*/":
					errmsg = "Encountered invalid character in `" + view.substr(thisRegion) + "`, cannot proceed."
					print(errmsg); view.window().status_message(errmsg); view.show_popup("<b style='background-color:red;color:lime'>: Invalid Character > Ended :</b>"); return
			expr = view.substr(thisRegion)
			view.run_command('move', {'by': 'characters', 'forward': True})

		if view.window() is not None and view == view.window().active_view() and expr:
			if view.settings().get("arith_result"): view.settings().erase("arith_result")
			try:
				view.settings().set("arith_result", "=${:,.15g}".format(round(eval(expr.replace(",", "").replace("$", "")), 4)))
				view.replace(edit, thisRegion, view.settings().get("arith_result"))
			except Exception as e:
				errmsg = "An error occurred in the evaluation of `" + expr + "`"
				print(errmsg + ":", e); view.window().status_message(errmsg); view.show_popup("<b style='background-color:red;color:lime'>: Evaluation Error Occurred :</b>")

			# this "if" block handles the updating of the subsequent transactions (if any) that need recalc
			if view.settings().get("arith_result") and not targetregion and thisPoint > -1:
				line_portion_infront = view.substr(sublime.Region(view.line(thisPoint).begin(), thisPoint))
				found_acc = re.search(r"(?<==).+?(?=\[)", line_portion_infront[::-1])
				if found_acc:
					acc = found_acc.group()[::-1]
					if view.find(r"\[=Bottom Up Style=\]", 0):
						go_on = True
						while go_on:
							go_on, last_region_begin, last_region_end = updateNextMatch(thisPoint, view.line(thisPoint).end(), acc)
							if go_on: thisPoint = last_region_end
						while True:
							found_acc = view.substr(sublime.Region(0, view.line(thisPoint).begin())).rfind("[" + acc + "=")
							if found_acc > -1:
								thisPoint = view.line(found_acc).begin()
								go_on = True
								while go_on:
									go_on, last_region_begin, last_region_end = updateNextMatch(thisPoint, view.line(thisPoint).end(), acc)
									if go_on: thisPoint = last_region_end
							else: break
					else:
						go_on = True
						while go_on:
							go_on, last_region_begin, last_region_end = updateNextMatch(thisPoint, view.size(), acc)
							if go_on: thisPoint = last_region_end

class bookkeepListener(sublime_plugin.EventListener):
	def on_modified(self, view):
		sel0 = view.sel()[0]; acc_detected = False; arith_needed = False
		if len(view.substr(sel0)) == 0:
			point = sel0.begin(); char = view.substr(sublime.Region(point - 1, point))
			if char == "=" and str(view.command_history(0)[1])[-3:] == "='}" and not view.settings().get("redo_flag") and point > 1:
				line_portion_infront = view.substr(sublime.Region(view.line(sel0).begin(), point))
				pos_of_open_sqrbra = line_portion_infront.rfind("[")
				if pos_of_open_sqrbra > -1 and line_portion_infront[pos_of_open_sqrbra:].find("]") == -1:
					acc = ""; pos = point - 1; char = view.substr(sublime.Region(pos - 1, pos))
					while char not in "[=]\n" and pos > 1:
						acc = char + acc; pos -= 1; char = view.substr(sublime.Region(pos - 1, pos))
					if char == "[": acc_detected = True
					elif char == "=": arith_needed = True
		if view.window() is not None and view == view.window().active_view():
			if acc_detected:	# brought down the balance from the one (with the same acc) just earlier than the moment the current caret position (which could be anywhere in a list of the transactions arranged in chronological order, no matter it's top down or bottom up) all about.
				found_acc = view.substr(view.line(sel0)).rfind("[" + acc + "=", 0, pos - view.line(sel0).begin())
				if found_acc > -1:
					view.run_command('insert', {'characters': re.search(r"=[^=[\]]+\]", view.substr(view.line(sel0))[found_acc:]).group()[1:-1]})
					return
				found_acc = view.find(r"\[" + acc + "=", view.line(sel0).end()) if view.find(r"\[=Bottom Up Style=\]", 0) else view.substr(sublime.Region(0, view.line(sel0).begin())).rfind("[" + acc + "=")
				if view.find(r"\[=Bottom Up Style=\]", 0) and found_acc or found_acc > -1:
					line_text = view.substr(view.line(found_acc))
					view.run_command('insert', {'characters': re.search(r"=[^=[\]]+\]", line_text[line_text.rfind("[" + acc + "="):]).group()[1:-1]})
			elif arith_needed:	# do the calculation
				view.run_command("undo")
				if len(view.substr(view.sel()[0])) > 0 or view.sel()[0].begin() < point - 1:
					view.settings().set("redo_flag", True)
					view.run_command("redo")
					view.run_command("left_delete")
					view.settings().erase("redo_flag")
				view.run_command('bookkeep')
