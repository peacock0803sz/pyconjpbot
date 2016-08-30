import json
import random

from slackbot.bot import respond_to, listen_to
from slackbot import settings
import slacker
import git

@respond_to('^help$')
def help(message):
    """
    helpページのURLを返す
    """
    message.send('ヘルプはこちら→ https://github.com/pyconjp/pyconjpbot#commands')

@respond_to('^shuffle\s+(.*)')
def shuffle(message, words):
    """
    指定したキーワードをシャッフルして返す
    """
    words = words.split()
    if len(words) == 1:
        message.send('キーワードを複数指定してください\n`$shuffle word1 word2...`')
    else:
        random.shuffle(words)
        message.send(' '.join(words))

@respond_to('^choice\s+(.*)')
def choice(message, words):
    """
    指定したキーワードから一つを選んで返す
    """
    words = words.split()
    if len(words) == 1:
        message.send('キーワードを複数指定してください\n`$choice word1 word2...`')
    else:
        message.send(random.choice(words))
        
@respond_to('^ping$')
def ping(message):
    """
    pingに対してpongで応答する
    """
    message.reply('pong')

@respond_to('^version$')
def version(message):
    """
    バージョン情報を返す
    """
    obj = git.Repo('').head.object
    url = "https://github.com/pyconjp/pyconjpbot/commit/{}".format(obj.hexsha)
    text = "<{}|{}> {} - {}({})".format(url, obj.hexsha[:6], obj.summary,
                                       obj.committer.name, obj.committed_datetime)
    attachments = [{
        'pretext': text,
    }]
    message.send_webapi('', json.dumps(attachments))

@respond_to('^random$')
@respond_to('^random\s+(active|help)$')
def random_command(message, subcommand=None):
    """
    チャンネルにいるメンバーからランダムに一人を選んで返す

    - https://github.com/os/slacker
    - https://api.slack.com/methods/channels.info
    - https://api.slack.com/methods/users.getPresence
    - https://api.slack.com/methods/users.info
    """

    if subcommand == 'help':
        message.send('''- `$random`: チャンネルにいるメンバーからランダムに一人を選ぶ
- `$random active`: チャンネルにいるactiveなメンバーからランダムに一人を選ぶ
''')
        return

    # チャンネルのメンバー一覧を取得
    channel = message.body['channel']
    webapi = slacker.Slacker(settings.API_TOKEN)
    cinfo = webapi.channels.info(channel)
    members = cinfo.body['channel']['members']

    # bot の id は除く
    bot_id = message._client.login_data['self']['id']
    members.remove(bot_id)

    member_id = None
    while not member_id:
        # メンバー一覧からランダムに選んで返す
        member_id = random.choice(members)
        if subcommand == 'active':
            # active が指定されている場合は presence を確認する
            presence = webapi.users.get_presence(member_id)
            if presence.body['presence'] == 'away':
                members.remove(member_id)
                member_id = None

    user_info = webapi.users.info(member_id)
    name = user_info.body['user']['name']
    message.send('{} さん、君に決めた！'.format(name))
    
