# encoding: utf-8

from wunderlist import icons
from wunderlist.util import workflow
from wunderlist.models.task import Task
from wunderlist.models.list import List
from wunderlist.models.preferences import Preferences
import re

_hashtag_prompt_pattern = r'#\S*$'

def filter(args):
    query = ' '.join(args[1:])
    wf = workflow()
    prefs = Preferences.current_prefs()
    matching_hashtags = []

    if not query:
        wf.add_item('Begin typing to search tasks', '', icon=icons.SEARCH)

    hashtag_match = re.search(_hashtag_prompt_pattern, query)
    if hashtag_match:
        from wunderlist.models.hashtag import Hashtag

        hashtag_prompt = hashtag_match.group()
        hashtags = Hashtag.select().where(Hashtag.id.contains(hashtag_prompt))

        for hashtag in hashtags:
            # If there is an exact match, do not show hashtags
            if hashtag.id.lower() == hashtag_prompt.lower():
                matching_hashtags = []
                break

            matching_hashtags.append(hashtag)

    # Show hashtag prompt if there is more than one matching hashtag or the
    # hashtag being typed does not exactly match the single matching hashtag
    if len(matching_hashtags) > 0:
        for hashtag in matching_hashtags:
            wf.add_item(hashtag.id[1:], '', autocomplete=u'-search %s %s ' % (query[:hashtag_match.start()], hashtag.id), icon=icons.HASHTAG)

    else:
        conditions = None

        for arg in args[1:]:
            if len(arg) > 1:
                conditions = conditions | Task.title.contains(arg)

        if conditions:
            if not prefs.show_completed_tasks:
                conditions = Task.completed_at.is_null() & conditions

            tasks = Task.select().where(Task.list.is_null(False) & conditions)

            # Default Wunderlist sort order
            tasks = tasks.join(List).order_by(Task.order.asc()).order_by(List.order.asc())

            for t in tasks:
                wf.add_item(u'%s – %s' % (t.list_title, t.title), t.subtitle(), autocomplete='-task %s  ' % t.id, icon=icons.TASK_COMPLETED if t.completed_at else icons.TASK)

        if prefs.show_completed_tasks:
            wf.add_item('Hide completed tasks', arg='-pref show_completed_tasks --alfred %s' % ' '.join(args), valid=True, icon=icons.HIDDEN)
        else:
            wf.add_item('Show completed tasks', arg='-pref show_completed_tasks --alfred %s' % ' '.join(args), valid=True, icon=icons.VISIBLE)

        wf.add_item('Let\'s discuss this screen', 'Do you need to search completed tasks, tasks by list, date, etc?', arg=' '.join(args + ['discuss']), valid=True, icon=icons.DISCUSS)

        wf.add_item('Main menu', autocomplete='', icon=icons.BACK)

def commit(args, modifier=None):
    action = args[1]

    if action == 'discuss':
        import webbrowser

        webbrowser.open('https://github.com/idpaterson/alfred-wunderlist-workflow/issues/95')
