import json
import time
import traceback
from typing import Dict, List, Optional, Union

import aiohttp
from pydantic import BaseModel

from .. import arcades_json, config_json, log
from .tool import writefile, openfile


class Arcade(BaseModel):
    
    name: str
    address: str
    mall: str
    province: str
    mainum: int
    chuninum: int
    id: str
    alias: List[str]
    group: List[int]
    person: int
    by: str
    time: str


class ArcadeList(List[Arcade]):


    async def save_arcade(self):
        return await writefile(arcades_json, [_.model_dump() for _ in self])
    
    def search_name(self, name: str) -> List[Arcade]:
        """模糊查询机厅"""
        arcade_list = []
        for arcade in self:
            if name in arcade.name:
                arcade_list.append(arcade)
            elif name in arcade.address:
                arcade_list.append(arcade)
            elif name in arcade.alias:
                arcade_list.append(arcade)
                
        return arcade_list
    
    def search_fullname(self, name: str) -> List[Arcade]:
        """查询店铺全名机厅"""
        arcade_list = []
        for arcade in self:
            if name == arcade.name:
                arcade_list.append(arcade)

        return arcade_list
    
    def search_alias(self, alias: str) -> List[Arcade]:
        """查询别名机厅"""
        arcade_list = []
        for arcade in self:
            if alias in arcade.alias:
                arcade_list.append(arcade)
        
        return arcade_list
    
    def search_id(self, id: str) -> List[Arcade]:
        """指定ID查询机厅"""
        arcade_list = []
        for arcade in self:
            if id == arcade.id:
                arcade_list.append(arcade)

        return arcade_list

    def add_arcade(self, arcade: dict) -> bool:
        """添加机厅"""
        self.append(Arcade(**arcade))
        return True

    def del_arcade(self, arcadeName: str) -> bool:
        """删除机厅"""
        for arcade in self:
            if arcadeName == arcade.name:
                self.remove(arcade)
                return True
        return False
    
    def group_in_arcade(self, group_id: int, arcadeName: str) -> bool:
        """是否已订阅该机厅"""
        for arcade in self:
            if arcadeName == arcade.name:
                if group_id in arcade.group:
                    return True
        return False
    
    def group_subscribe_arcade(self, group_id: int) -> List[Arcade]:
        """已订阅机厅"""
        arcade_list = []
        for arcade in self:
            if group_id in arcade.group:
                arcade_list.append(arcade)
        return arcade_list

    @classmethod
    def arcade_to_msg(cls, arcade_list: List[Arcade]) -> List[str]:
        """机厅人数格式化"""
        result = []
        for arcade in arcade_list:
            arcadename = ''.join(arcade.alias)
            msg = f'''{arcadename} 当前 {arcade.person} 人'''
            totalnum = arcade.mainum + arcade.chuninum
            if totalnum > 1:
                msg += f''' 机均 {arcade.person // totalnum} 人'''
            if arcade.by:
                msg += f'\n[{arcade.time}]'
            result.append(msg.strip())
        return result


class ArcadeData:
    
    total: Optional[ArcadeList]
    
    def __init__(self) -> None: 
        self.arcades: List[Dict] = json.load(open(arcades_json, 'r', encoding='utf-8'))
        self.idList = []

    def get_by_id(self, id: int) -> Union[None, Dict]:
        id_list = [c_a['id'] for c_a in self.arcades]
        if id in id_list:
            return self.arcades[id_list.index(id)]
        else:
            return None
    
    async def getArcade(self):
        self.total = await download_arcade_info()
        self.idList = [int(c_a.id) for c_a in self.total]

arcade = ArcadeData()

async def load_config() -> bool:
    try:
        config = json.load(open(config_json, 'r', encoding='utf-8'))
        save = config.get('use-online-database', '').strip().lower()
        if save in ['true', '']:
            return True
        elif save == 'false':
            return False
        else:
            raise ValueError("'use-online-database'为无效值，已重置为 True")
    except Exception as e:
        log.error(f'读取配置文件时出现问题：{e}')
        return True


async def download_arcade_info() -> ArcadeList:
    save = await load_config()
    try:
        async with aiohttp.request('GET', 'http://wc.wahlap.net/maidx/rest/location', timeout=aiohttp.ClientTimeout(total=30)) as req:
            if req.status == 200:
                maidata = await req.json()
            else:
                maidata = None
                log.error('获取舞萌DX店铺分布失败')

        async with aiohttp.request('GET', 'https://wc.wahlap.net/chunithm/rest/location', timeout=aiohttp.ClientTimeout(total=30)) as req:
            if req.status == 200:
                chunidata = await req.json()
            else:
                chunidata = None
                log.error('获取中二节奏店铺分布失败')

        arcadelist = ArcadeList()

        maidata_dict = {arc['id']: arc for arc in maidata} if maidata else {}
        chunidata_dict = {arc['id']: arc for arc in chunidata} if chunidata else {}

        # 处理 maidata
        for _arc in maidata:
            arcade_dict = {
                'name': _arc['arcadeName'],
                'address': _arc['address'],
                'mall': _arc['mall'],
                'province': _arc['province'],
                'mainum': _arc['machineCount'],
                'chuninum': chunidata_dict.get(_arc['id'], {}).get('machineCount', 0),
                'id': _arc['id'],
                'alias': [],
                'group': [],
                'person': 0,
                'by': '',
                'time': ''
            }
            arcadelist.append(Arcade(**arcade_dict))

        # 处理 chunidata
        for _arc in chunidata:
            if _arc['id'] not in maidata_dict:
                arcade_dict = {
                    'name': _arc['arcadeName'],
                    'address': _arc['address'],
                    'mall': _arc['mall'],
                    'province': _arc['province'],
                    'mainum': 0,
                    'chuninum': _arc['machineCount'],
                    'id': _arc['id'],
                    'alias': [],
                    'group': [],
                    'person': 0,
                    'by': '',
                    'time': ''
                }
                arcadelist.append(Arcade(**arcade_dict))

        if save:
            await writefile(arcades_json, [])
            await writefile(arcades_json, [_.model_dump() for _ in arcadelist])
        else:
            arcadelist_data = await openfile(arcades_json)
            arcadelist = ArcadeList([Arcade(**arc) for arc in arcadelist_data])
            log.info('未使用在线机厅信息，正在使用本地机厅信息')

        return arcadelist
    except Exception:
        log.error(f'Error: {traceback.format_exc()}')
        log.error('获取机厅信息失败')


async def update_arcade(arcadeName: str, mainum: str, chuninum:str):
    if arcadeName.isdigit():
        arcade_list = arcade.total.search_id(arcadeName)
    else:
        arcade_list = arcade.total.search_fullname(arcadeName)
    if arcade_list:
        _arcade = arcade_list[0]
        _arcade.mainum = int(mainum)
        _arcade.chuninum = int(chuninum)
        msg = f'已修改 {arcadeName} 的详情信息\n舞萌DX机台数量为{mainum}台\n中二节奏机台数量为{chuninum}台'
        await arcade.total.save_arcade()
    else:
        msg = f'未查找到该机厅'
    return msg
    

async def update_alias(arcadeName: str, aliasName: str, add_del: bool):
    """变更机厅别名"""
    change = False
    if arcadeName.isdigit():
        arcade_list = arcade.total.search_id(arcadeName)
    else:
        arcade_list = arcade.total.search_fullname(arcadeName)
    if arcade_list:
        _arcade = arcade_list[0]
        if add_del:
            if aliasName not in _arcade.alias:
                _arcade.alias.append(aliasName)
                msg = f'别名已添加'
                change = True
            else:
                msg = f'已存在该别名'
        else:
            if aliasName in _arcade.alias:
                _arcade.alias.remove(aliasName)
                msg = f'别名已移除'
                change = True
            else:
                msg = f'没有该别名'
    else:
        msg = f'未查找到该机厅'
    if change:
        await arcade.total.save_arcade()
    return msg


async def subscribe(group_id: int, arcadeName: str, sub: bool):
    """订阅机厅，`sub` 等于 `True` 为订阅，`False` 为取消订阅"""
    change = False
    if arcadeName.isdigit():
        arcade_list = arcade.total.search_id(arcadeName)
    else:
        arcade_list = arcade.total.search_fullname(arcadeName)
    if arcade_list:
        _arcade = arcade_list[0]
        if sub:
            if arcade.total.group_in_arcade(group_id, _arcade.name):
                msg = f'该机厅已订阅'
            else:
                _arcade.group.append(group_id)
                msg = f'已添加订阅'
                change = True
        else:
            if not arcade.total.group_in_arcade(group_id, _arcade.name):
                msg = f'该机厅未订阅'
            else:
                _arcade.group.remove(group_id)
                msg = f'已取消订阅'
                change = True
    else:
        msg = f'未查找到该机厅'
    if change:
        await arcade.total.save_arcade() 
    return msg
        
        
async def update_person(arcadeList: List[Arcade], userName: str, value: str, person: int):
    """变更机厅人数"""
    if len(arcadeList) == 1:
        _arcade = arcadeList[0]
        original_person = _arcade.person
        arcadename = ''.join(_arcade.alias)
        if value in ['++', '＋＋']:
            _arcade.person + 1
        elif value in ['--', '－－']:
            _arcade.person - 1
        elif value.isdigit():
            person = value
            if person > 30 or person < 0:
                return '无效人数'
            _arcade.person = person 
        elif value in ['+', '＋', '增加', '添加', '加']:
            if person > 30:
                return '增加人数超出上限'
            _arcade.person += person
        elif value in ['-', '－', '减少', '降低', '减']:
            if person > 30 or person > _arcade.person:
                return '减少人数超出上限'
            _arcade.person -= person
        elif value in ['=', '＝', '设置', '设定']:
            if person > 30 or person < 0:
                return '无效人数'
            _arcade.person = person
        if _arcade.person == original_person:
            return f'人数没有变化，{arcadename}为{_arcade.person}人'
        else:
            _arcade.by = userName
            _arcade.time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            await arcade.total.save_arcade()
            return f'{arcadename}现在有{_arcade.person}人'
    elif len(arcadeList) > 1:
        return '发现多个重复条目，请直接使用店铺ID更改机厅别名\n' + '\n'.join([f'{_.id}：{_.name}' for _ in arcadeList])
    else:
        return '未查找到该机厅'
