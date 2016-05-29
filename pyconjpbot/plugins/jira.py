import json
from urllib.parse import quote

from jira import JIRA, JIRAError
from slackbot import settings
from slackbot.bot import respond_to, listen_to

# Clean JIRA Url to not have trailing / if exists
CLEAN_JIRA_URL = settings.JIRA_URL if not settings.JIRA_URL[-1:] == '/' else settings.JIRA_URL[:-1]

# Login to jira
jira_auth = (settings.JIRA_USER, settings.JIRA_PASS)
jira = JIRA(CLEAN_JIRA_URL, basic_auth=jira_auth)

@listen_to(r'(^|[^/])\b([A-Za-z]+)-([0-9]+)\b')
def jira_listener(message, pre, project, number):
    """
    JIRAのissue idっぽいものを取得したら、そのissueの情報を返す
    """
    # Only attempt to find tickets in projects defined in slackbot_settings
    if project not in settings.JIRA_PROJECTS:
        return

    # Parse ticket and search JIRA
    issue_id = '{}-{}'.format(project, number)
    try:
        issue = jira.issue(issue_id)
    except JIRAError:
        message.send('%s は存在しません' % issue_id)
        return

    # Create variables to display to user
    summary = issue.fields.summary
    assignee = '未割り当て'
    if issue.fields.assignee:
        assignee = issue.fields.assignee.displayName 
    status = issue.fields.status.name
    issue_url = issue.permalink()

    attachments = [{
        'fallback': '{} {}'.format(issue_id, summary),
        'pretext': '<{}|{}> {}'.format(issue_url, issue_id, summary),
        'fields': [
            {
                'title': '担当者',
                'value': assignee,
                'short': True,
            },
            {
                'title': 'ステータス',
                'value': status,
                'short': True,
            },
        ],
    }]
    message.send_webapi('', json.dumps(attachments))

@respond_to('jira search (.*)')
def jira_search(message, keyword):
    """
    JIRAをキーワード検索した結果を返す
    """
    jql = 'status in (Open, "In Progress", Reopened) AND text ~ "{}"'
    title = '「{}」の検索結果'.format(keyword)
    _send_jira_search_responce(message, jql.format(keyword), title)

@respond_to('jira assignee (.*)')
def jira_assignee(message, user):
    """
    指定されたユーザーにアサインされた課題の一覧を返す
    """
    jql = 'status in (Open, "In Progress", Reopened) AND assignee in ({})'
    title = '「{}」の担当課題'.format(user)
    _send_jira_search_responce(message, jql.format(user), title)

def _send_jira_search_responce(message, query, title):
    """
    JIRAをqueryで検索した結果を返すメソッド
    """
    pretext = title
    pretext += '(<{}/issues/?jql={}|JIRAで見る>)\n'.format(CLEAN_JIRA_URL, quote(query))
    issues = jira.search_issues(query)
    
    if issues:
        for issue in issues:
            summary = issue.fields.summary
            key = issue.key
            url = issue.permalink()
            pretext += '- <{}|{}> {}\n'.format(url, key, summary)
    else:
        pretext += '該当するJIRA issueは見つかりませんでした'

    attachments = [{
        'fallback': title,
        'pretext': pretext,
    }]
    message.send_webapi('', json.dumps(attachments))

@respond_to('jira help$')
def jira_search(message):
    """
    jiraコマンドのヘルプを返す
    """
    message.send('''- `SAR-123`: 指定されたチケットの詳細情報を返す
- `$jira search keywords`: 指定されたキーワードで検索する
- `$jira assignee user`: 指定されたユーザーが担当しているissueを返す''')
