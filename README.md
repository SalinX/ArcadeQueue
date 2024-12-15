# ArcadeQueue
适用于 [HoshinoBot](https://github.com/Ice9Coffee/HoshinoBot) 的机厅排卡模块，基于 [Project maimaiDX](https://github.com/Yuri-YuzuChaN/maimaiDX) 中的 maimaiDXArcade 进行二次修改

## 使用方法
1. clone本项目至 HoshinoBot 模块目录 `modules` 下
    ``` git
    git clone https://github.com/SalinX/ArcadeQueue
    ```

2. 前往 HoshinoBot 目录中 `config/__bot__.py` 的 'MODULES_ON' 条目下添加 `ArcadeQueue`
3. 安装模块所需的 requirements：`pip install -r requirements.txt`
4. 在 https://phantomjs.org/download.html 下载对应操作系统的 PhantomJS，Windows下需要添加环境目录
5. 如果此时 HoshinoBot 仍在运行，重启 HoshinoBot 以使模块生效

## 修改内容
1. 在原模块的基础上增加对中二节奏机台数量的支持
2. 支持直接读取本地机厅信息，并可通过配置文件控制是否在线获取机厅信息

## 如果需要使用本地机厅信息
1. 修改模块根目录下的config.json，设置 `"use-online-database"` 的值为 `False`
2. 打开模块根目录内的 `static/arcades-local.json` 文件，按需修改内容后将该文件重命名为 `arcades.json` 即可

   *建议对修改后的文件进行备份，以免使用在线数据时文件内容被覆盖

## License

MIT

你可以自由使用本项目的代码用于商业或非商业的用途，但必须附带 MIT 授权协议。
