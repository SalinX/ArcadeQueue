from re import Match

from nonebot import NoneBot, on_startup

from hoshino import Service, priv
from hoshino.typing import CQEvent, MessageSegment

from .lib.image import image_to_base64, text_to_image
from .lib.arcade import *
from . import log


sv_help= """
排卡指令帮助
j 查看所有机厅的排卡人数
jt 查看所有机厅的详细信息
<机厅简称>几/几人/几卡 查看目标机厅的排卡人数
<机厅简称>=/+/-<人数> 修改目标机厅的人数

群管理可用选项
添加机厅 <店名> <地址> <舞萌DX机台数量> <中二节奏机台数量> <简称> 添加机厅信息
删除机厅 <店名> 删除机厅信息
修改机厅 <店名> mai数量 <舞萌DX数量> chu数量 <中二节奏数量> 修改机厅店名和数量信息
添加/删除机厅别名 <店名> <简称> 为目标机厅添加/删除简称
查找机厅 <关键词> 来查找已添加的机厅
在添加机厅后，请使用 订阅机厅 <店名> 订阅目标机厅，否则将无法进行排卡操作
取消订阅机厅 <店名> 取消目标机厅在本群组的订阅"""

SV_HELP = '请使用 help 排卡/q/queue 来查看帮助'
sv_queue = Service('ArcadeQueue', manage_priv=priv.ADMIN, enable_on_default=True, help_=SV_HELP)

@on_startup
async def _():
    log.info('正在获取机厅信息')
    await arcade.getArcade()
    log.info('机厅信息获取完成')


@sv_queue.on_fullmatch(['帮助排卡', '排卡帮助', 'help 排卡', 'help q', 'help queue'])
async def arcadequeue_help(bot: NoneBot, ev: CQEvent):
    await bot.send(ev, sv_help, at_sender=True)
#   await bot.send(ev, MessageSegment.image(image_to_base64(Image.open((Root / 'help.png')))), at_sender=True)

@sv_queue.on_prefix(['添加机厅', '新增机厅'])
async def add_arcade(bot: NoneBot, ev: CQEvent):
    args: List[str] = ev.message.extract_plain_text().strip().split()
    if not priv.check_priv(ev, priv.ADMIN):
        msg = '只有群管理可以管理机厅'
    elif len(args) == 1 and args[0] in ['帮助', 'help']:
        msg = '添加机厅的指令格式：添加机厅 <店名> <地址> <舞萌DX机台数量> <中二节奏机台数量> <简称>\nTip: 可以同时添加多个简称'
    elif len(args) >= 3:
        if not args[2].isdigit():
            msg = '指令错误，请再次确认指令格式\n添加机厅 <店名> <地址> <舞萌DX机台数量> <中二节奏机台数量> <简称1> [简称2] ...'
        else:
            if not arcade.total.search_fullname(args[0]):
                aid = sorted(arcade.idList, reverse=True)
                if (sid := aid[0]) >= 10000:
                    sid += 1
                else:
                    sid = 10000
                arcade_dict = {
                    'name': args[0],
                    'address': args[1],
                    'mall': '',
                    'mainum': int(args[2]) if len(args) > 2 else 1,
                    'chuninum': int(args[3]) if len(args) > 3 else 2,
                    'id': str(sid),
                    'alias': args[4:] if len(args) > 4 else [],
                    'group': [],
                    'person': 0,
                    'by': '',
                    'time': ''
                }
                arcade.total.add_arcade(arcade_dict)
                await arcade.total.save_arcade()
                msg = f'{args[0]} 添加成功'
            else:
                msg = f'{args[0]} 已存在'
    else:
        msg = '指令错误，请再次确认指令格式\n添加机厅 <店名> <地址> <舞萌DX机台数量> <中二节奏机台数量> <简称1> [简称2] ...'

    await bot.send(ev, msg, at_sender=True)


@sv_queue.on_prefix(['删除机厅', '移除机厅'])
async def delele_arcade(bot: NoneBot, ev: CQEvent):
    name = ev.message.extract_plain_text().strip()
    if not priv.check_priv(ev, priv.ADMIN):
        msg = '只有群管理可以管理机厅'
    elif not name:
        msg = '指令错误，请再次确认指令格式\n删除机厅 <店名>，店名需要输入全称而不是简称哦！'
    else:
        if not arcade.total.search_fullname(name):
            msg = f'未找到{name}'
        else:
            arcade.total.del_arcade(name)
            await arcade.total.save_arcade()
            msg = f'已删除{name}'
    await bot.send(ev, msg, at_sender=True)


@sv_queue.on_prefix(['添加机厅别名', '删除机厅别名'])
async def _(bot: NoneBot, ev: CQEvent):
    args: List[str] = ev.message.extract_plain_text().strip().split()
    a = True if ev.prefix == '添加机厅别名' else False
    if len(args) != 2:
        msg = '指令错误，请再次确认指令格式\n添加/删除机厅别名 <店名> <别名>'
    elif not args[0].isdigit() and len(_arc := arcade.total.search_fullname(args[0])) > 1:
        msg = '发现多个重复条目，请直接使用店铺ID更改机厅别名\n' + '\n'.join([ f'{_.id}：{_.name}' for _ in _arc ])
    else:
        msg = await update_alias(args[0], args[1], a)
    await bot.send(ev, msg, at_sender=True)


@sv_queue.on_prefix(['修改机厅', '编辑机厅'])
async def modify_arcade(bot: NoneBot, ev: CQEvent):
    args: List[str] = ev.message.extract_plain_text().strip().split()
    if not priv.check_priv(ev, priv.ADMIN):
        msg = '只有群管理可以管理机厅'
    elif not args[0].isdigit() and len(_arc := arcade.total.search_fullname(args[0])) > 1:
        msg = '发现多个重复条目，请直接使用店铺ID更改机厅别名\n' + '\n'.join([ f'{_.id}：{_.name}' for _ in _arc ])
    elif args[1] == 'mai数量' and args[2].isdigit() and args[3] == 'chu数量' and args[4].isdigit() and len(args) == 5:
        msg = await update_arcade(args[0], args[2], args[4])
    else:
        msg = '指令错误，请再次确认指令格式\n修改机厅 <店名> mai数量 <舞萌DX数量> chu数量 <中二节奏数量>'
    
    await bot.send(ev, msg, at_sender=True)


@sv_queue.on_rex(r'^(订阅机厅|取消订阅机厅|取消订阅)\s(.+)', normalize=False)
async def _(bot: NoneBot, ev: CQEvent):
    match: Match[str] = ev['match']
    gid = ev.group_id
    sub = True if match.group(1) == '订阅机厅' else False
    name = match.group(2)
    if not priv.check_priv(ev, priv.ADMIN):
        msg = '只有群管理可以管理机厅'
    elif not name.isdigit() and len(_arc := arcade.total.search_fullname(name)) > 1:
        msg = f'发现多个重复条目，请直接使用店铺ID更改机厅别名\n' + '\n'.join([ f'{_.id}：{_.name}' for _ in _arc ])
    else:
        msg = await subscribe(gid, name, sub)
    
    await bot.send(ev, msg, at_sender=True)


@sv_queue.on_fullmatch(['查看订阅', '查看订阅机厅', 'jt'])
async def check_subscribe(bot: NoneBot, ev: CQEvent):
    gid = int(ev.group_id)
    arcadeList = arcade.total.group_subscribe_arcade(group_id=gid)
    if arcadeList:
        result = [f'以下是订阅机厅总览\n']
        for a in arcadeList:
            if a.mainum and a.chuninum !=0:
                alias = "\n  ".join(a.alias)
                result.append(f'''[{alias.strip()}] {a.name}
地址：{a.address}
舞萌DX机台数量：{a.mainum}
中二节奏机台数量：{a.chuninum}
''')
            elif a.mainum == 0:
                alias = "\n  ".join(a.alias)
                result.append(f'''[{alias.strip()}] {a.name}
地址：{a.address}
中二节奏机台数量：{a.chuninum}
''')
            else:
                alias = "\n  ".join(a.alias)
                result.append(f'''[{alias.strip()}] {a.name}
地址：{a.address}
舞萌DX机台数量：{a.mainum}
''')
        msg = '\n'.join(result)
    else:
        msg = '没有已订阅的机厅'
    await bot.send(ev, msg, at_sender=True)


@sv_queue.on_prefix(['查找机厅', '查询机厅', '机厅查找', '机厅查询'])
async def search_arcade(bot: NoneBot, ev: CQEvent):
    name: str = ev.message.extract_plain_text().strip()
    if not name:
        await bot.finish(ev, '指令错误，请再次确认指令格式\n查找机厅 <关键词>', at_sender=True)
    elif arcade_list := arcade.total.search_name(name):
        result = ['查找到以下结果\n']
        for a in arcade_list:
            if a.mainum and a.chuninum !=0:
                result.append(f'''店名：{a.name}
地址：{a.address}
店铺ID：{a.id}
舞萌DX机台数量：{a.mainum}
中二节奏机台数量：{a.chuninum}''')
            elif a.mainum == 0:
                result.append(f'''店名：{a.name}
地址：{a.address}
店铺ID：{a.id}
中二节奏机台数量：{a.chuninum}''')
            else:
                result.append(f'''店名：{a.name}
地址：{a.address}
店铺ID：{a.id}
舞萌DX机台数量：{a.mainum}''')
        if len(arcade_list) < 5:
            await bot.send(ev, '\n==========\n'.join(result), at_sender=True)
        else:
            await bot.send(ev, MessageSegment.image(image_to_base64(text_to_image('\n'.join(result)))), at_sender=True)
    else:
        await bot.send(ev, '未查找到结果，可以使用 添加机厅 <店名> <地址> <舞萌DX机台数量> <中二节奏机台数量> <简称> 来添加机厅信息', at_sender=True)


@sv_queue.on_rex(r'^(.+)?\s?(设置|设定|＝|=|增加|添加|加|＋|\+|减少|降低|减|－|-)\s?([0-9]+|＋|\+|－|-)(人|卡)?$')
async def arcade_person(bot: NoneBot, ev: CQEvent):
    try:
        match: Match[str] = ev['match']
        gid = ev.group_id
        nickname = ev.sender['nickname']
        if not match.group(3).isdigit() and match.group(3) not in ['＋', '+', '－', '-']:
            await bot.finish(ev, '键入值无效', at_sender=True) 
        arcade_list = arcade.total.group_subscribe_arcade(group_id=gid)
        if not arcade_list:
            log.info('无效查询：机厅未被订阅或输入错误')
        value = match.group(2)
        if value is None:
            value = "="
        if match.group(3) in ['＋', '+', '－', '-']:
            person = 1
        else:
            person = int(match.group(3))
        if match.group(1):
            if '人数' in match.group(1) or '卡' in match.group(1):
                arcadeName = match.group(1)[:-2] if '人数' in match.group(1) else match.group(1)[:-1]
            else:
                arcadeName = match.group(1)
            _arcade = []
            for _a in arcade_list:
                if arcadeName == _a.name:
                    _arcade.append(_a)
                    break
                if arcadeName in _a.alias:
                    _arcade.append(_a)
                    break
            if not _arcade:
                log.info('无效查询：机厅输入错误')
            else:
                msg = await update_person(_arcade, nickname, value, person)

            await bot.send(ev, msg, at_sender=True)
    except:
        pass


@sv_queue.on_fullmatch(['机厅几人', 'j', 'J', '/j', '/J', 'jtj', 'JTJ'])
async def arcade_query_multiple(bot: NoneBot, ev: CQEvent):
    gid = ev.group_id
    arcade_list = arcade.total.group_subscribe_arcade(gid)
    if arcade_list:
        result = ['机厅人数如下']
        result += arcade.total.arcade_to_msg(arcade_list)
        await bot.send(ev, '\n'.join(result), at_sender=True)
    else:
        await bot.finish(ev, '没有已订阅的机厅，请使用 订阅机厅 <店名> 来订阅目标机厅', at_sender=True)


@sv_queue.on_suffix(['有多少人', '有几人', '有几卡', '多少人', '多少卡', '几人', '几卡', '几'])
async def arcade_query_person(bot: NoneBot, ev: CQEvent):
    arg = ev.message.extract_plain_text().strip().lower()
    result = None
    arcades: List[Dict] = json.load(open(arcades_json, 'r', encoding='utf-8'))
    if arg:
        for a in arcades:
            if arg == a['name']:
                result = a
                break
            if arg in a['alias']:
                result = a
                break
        if not result:
            return log.info('无效查询：机厅输入错误')
    if result:
        msg = f'{arg}有{result["person"]}人 '
        totalnum = result['mainum'] + result['chuninum']
        if totalnum > 1:
            msg += f'机均{result["person"] // totalnum }人'
        if result['by']:
            msg += f'\n由 {result["by"]} 更新于\n{result["time"]}'
        await bot.send(ev, msg.strip(), at_sender=True)
    else:
        return log.info('无效查询：未订阅机厅')


@sv_queue.scheduled_job('cron', hour='1')
async def _():
    try:
        await download_arcade_info()
        for _ in arcade.total:
            _.person = 0
            _.by = '自动归零'
            _.time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        await arcade.total.save_arcade()
    except:
        return
    log.info('机厅人数已归零')