# 清华葡萄酒协会公众号排版工作流

这套工具把一次活动拆成三层：**用户提供内容与来源；配置决定版式；通用程序生成预览和图片。** 后续不再为每篇从头排版。

## 哪些部分高度复用

| 层级 | 固定内容 | 每篇需要决定的内容 |
|---|---|---|
| 排版系统 | 1080px宽、72px边距、字体字号、行距、标题层级、颜色 | 只在用户明确要求换风格时改 |
| 内容组件 | 封面、分节、图文、三项数据、酒款卡片、分享人、报名、提示、致谢、结语 | 文案、图片、条目数、显示顺序 |
| 素材处理 | 本地归档、裁切坐标、保持原图和logo、来源记录 | 哪张图片、焦点与裁切范围 |
| 审稿 | 可选中文字的网页、浏览器批注、相同URL迭代 | 本轮具体意见 |
| 导出 | 当前版本确认、自动按section切图、同宽连续拼接、编号 | 分段边界是否需要调整 |
| 内容核对 | 酒款计数、重复条目、缺图、越界、失效确认检查 | 名称、来源、时间地点、费用等事实 |

不能机械复用的是主张和事实：活动时间地点、报名入口、支付和退款规定、赞助关系、酒款参数、人物身份、酒庄统计数据，都要以本次素材和用户确认为准。

## 固定样式 v1

默认不加入协会logo，新建项目不自动插入标志。仅在用户明确要求某篇使用时，才添加合适的logo组件；共用assets中的矢量原稿与预览素材保留供按需使用。

所有数值均以1080px画布为基准。`theme.json` 是唯一配置源；以下仅说明当前约定。

| 用途 | 字体 | 字号 / 行距 | 默认颜色 |
|---|---|---|---|
| 封面主标题 | 宋体，加粗 | 112 / 140 | 深酒红 #6b343e |
| 一级分节 | 宋体 | 60 / 82 | 深酒红 |
| 小标题、提示和致谢标题 | 宋体 | 48 / 78 | 普通标题酒红；提示、致谢黑色 |
| 酒款名称 | 宋体 | 44 / 65 | 深酒红 |
| 正文 | 等线 Light | 39 / 73 | 深灰 #3e3b3b |
| 酒款正文 | 等线 Light | 36 / 68 | 深灰 |
| 辅助正文 | 等线 Light | 34 / 65 | 深灰 |
| 元信息 | 等线 Light | 32 / 60 | 暖灰 |
| 酒款品牌 | 等线 Light | 29 / 53 | 暖灰 |
| 文末结语 | 宋体 | 43 / 80 | 黑色 |
| 图片说明 | 等线 Light | 26 / 48 | 暖灰 |
| 英文眉题 | 等线 Light | 25 / 48 | 暖灰 |
| 风土数据 / 标签 | 等线 Light | 40 / 70；28 / 52 | 酒红 / 暖灰，居中 |

正文一般左对齐自然换行，不使用两端强制撑字；标题显式分行。图片保留原比例；裁切是单独参数，原素材不被覆盖。酒款卡片保留左侧酒瓶、右侧说明的版式。

## 每篇的最短流程

1. 给出素材目录、可信文案、风格是否沿用、内容顺序。可以直接说：

   > 按 post_builder 工作流做下一篇，素材在……；沿用默认样式；顺序为……；先给可批注网页。

2. 创建 `projects/<活动名>/post.json`，复制素材，填写来源。新项目默认四节：风土、酒庄、酒款、报名；可以按活动内容调整。
3. 用Typora打开 `projects/<活动名>/正文.md`。双击同目录的 `开始编辑.cmd` 启动本机自动预览；也可由Codex启动 `serve` 并在内置浏览器打开返回的HTTP地址。文字修改后保存，网页会自动重排刷新并尽量保持滚动位置。
4. 文字可以自己改，无需再转述给Codex。版式意见仍可在网页中批注。文字修改只改正文.md；图片、裁切和组件结构改post.json；统一样式改theme.json。
5. 用户明确说“可以生成图片”等后，记录当前版本确认并导出。不要把旧稿的确认套用到修改后的稿件。
6. 图片在 `projects/<活动名>/exports/<版本摘要>/`，按编号插入公众号。manifest记录尺寸；所有图片同宽，按同一画布连续切分，拼接不会缺行或重复。

## 直接编辑正文

- 每篇文字集中在 `正文.md`，Typora中可以按普通文档修改标题、段落、酒名、介绍、时间地点、致谢等，并查看图片参考。JSON只保存布局与文字引用，不再保留两套文案。
- 隐藏的 `pb-text` HTML注释负责定位，请保留。改现有段落、加减文字和换行即可；不要把新增内容写在两个编辑区之外。新增组件、重排章节仍交给Codex处理。
- Markdown是编辑格式，排版仍使用固定模板。Markdown标题会映射为原有角色；加粗标记和行内代码的文字按固定字形读取。暂不把Markdown表格、HTML等复杂内容自动转换成新组件。
- 图片参考位于自动生成的 `editing-assets/`，用于阅读，不改变原图或导出。替换图片、调整裁切仍修改组件配置。
- 自动预览只监听本机127.0.0.1，不上传正文或素材。网页右下角显示连接/更新状态；格式错误时保留上一版并显示原因。修正并保存后继续更新。
- 双击 `停止预览.cmd` 或关闭运行窗口可停止服务。服务停止后，正文仍能编辑，静态预览也仍可打开；再次启动即可恢复自动刷新。
- 本地HTTP预览可在普通浏览器查看。要继续用应用内的网页批注，请在内置浏览器打开同一个HTTP地址。
- 新项目 `new` 默认生成正文.md。已存在的纯JSON项目可运行 `markdown` 迁移，原JSON会先备份。结构变化后用 `markdown-refresh` 重建编辑区；现有文字会被保留，旧正文也会备份。

## 内容格式与组件

`post.json` 的顶层字段：

- `schema_version`: 固定1。
- `title`: 本篇名称的Markdown引用。
- `text_source`: 正文Markdown路径；默认为正文.md。
- `text_schema`: 稳定文字引用与字符串/多行/段落类型，自动管理。
- `theme`: 固定主题id。
- `assets`: 本地图片字典，`path`相对于项目目录；可附`source`说明。
- `sources`: 来源字典，如用户确认的文案、酒庄资料、图片原件。
- `expected_wine_count`: 本篇正式酒单总数，未公开彩蛋不计入。
- `sections`: 顺序就是图文顺序，也是分图顺序；每节包含唯一`id`、显示名`label`与`blocks`。

每个block必须有稳定、唯一的`id`及`type`。常用组件：

段落可用 `{grape_wine_count}`、`{rice_wine_count}`、`{wine_count}` 自动插入葡萄酒、米酒及正式酒单总数，避免补入酒款后忘记同步数量。其他文案中的花括号保持原样。

| type | 主要内容 |
|---|---|
| cover | `brand`, `title_lines`, `subtitle`, `meta`，可选`logo`图片规格 |
| heading | `text`，可选`eyebrow`, `role`, `color`, `align` |
| paragraph | `text`，可选`role`与`after`段后距 |
| image | `asset`，可选`crop:[x,y,w,h]`、说明`caption`、宽高；坐标以原图像素计 |
| stats | `items:[{value,label},…]`，自动等分居中 |
| table | `columns:[{label,width},…]`、`rows:[{id,cells:[文字,…]},…]`；列宽之和等于内容区宽度（当前936px），单元格自动换行，行高随内容增长；表头与单元格文字均由正文.md管理 |
| wine_list | `items`中每项有`brand`, `name`, `category`, `meta`, `description`, `image`, `sources`；自动编号 |
| speaker | `image`, `name`, `description` |
| callout | `text`，可选`eyebrow`；不自动重复增加一个彩蛋标题 |
| event | `when`, `where`, `contact`, `speakers`, `speaker_roles`；可选`horse`与`horse_mask` |
| notice | `text`, `confirmed:true`；不自动编造收费或退款规则 |
| sponsor | `thanks`, `logo`, `paragraphs`；标题默认黑色 |
| responsible | `image`, `text` |
| closing | `lines`, `brand`；文字和短线黑色 |
| spacer / rule | 受控留白、分隔线 |

图片规格通用写法：`{"asset":"图片id","crop":[0,1200,1000,304],"alt":"内容说明"}`。不需要裁切时省略crop。完整真实示例见 `projects/20261024-lewei/post.json`。

## 文件职责

```text
post_builder/
  AGENTS.md                  进入本目录时的约定
  SKILL.md                   给Codex执行的工作流入口
  WORKFLOW.md                本说明
  theme.json                 唯一的统一样式配置
  scripts/post_builder.py    通用组件、检查、网页、确认、导出入口
  scripts/export_images.cjs  分段图片栅格化
  assets/                    可长期复用的原始标志
  projects/<活动名>/
    正文.md                  直接用Typora编辑的唯一文字源
    post.json                组件、顺序、裁切、来源和Markdown文字引用
    assets/                  本次活动素材，复制归档，避免临时文件失效
    preview/index.html       当前可批注网页
    preview/layout.json      当前排版与版本摘要
    开始编辑.cmd / 停止预览.cmd  本机自动预览入口
    editing-assets/          Markdown中的图片参考，自动生成
    history/                 迁移前源稿和成功预览的正文快照
    approval.json            用户批准的版本摘要，仅确认后产生
    revisions.jsonl          每轮修改与导出记录
    exports/<版本摘要>/      当前确认版本的等宽分段图
```

预览与最终图片都从正文.md解析文字，使用同一套排版节点。导出时用本机同一字体转成轮廓。不要直接编辑生成的HTML，它不会写回正文。

## 命令

在本目录运行：

```powershell
python scripts/post_builder.py new 20261031-tasting --title "下一场品鉴"
python scripts/post_builder.py check 20261031-tasting
python scripts/post_builder.py preview 20261031-tasting --note "首稿"
python scripts/post_builder.py serve 20261031-tasting --open
# 保存正文.md后自动更新；停止时运行：
python scripts/post_builder.py stop 20261031-tasting
# 完成几轮网页批注；用户明确同意后才执行下面两步
python scripts/post_builder.py approve 20261031-tasting --note "用户实际确认的话"
python scripts/post_builder.py export 20261031-tasting
```

本机现有Python包含所需依赖，图片导出可使用Codex运行时自带sharp。换电脑时安装 `requirements.txt` 与 `package.json` 的依赖，并确认Windows字体路径；不复制分发系统字体。也可用 `POST_BUILDER_NODE_MODULES` 指向已有node_modules。

修改排版程序或导出逻辑后，可运行 `python scripts/test_workflow.py` 检查确认失效、缺酒检测和图片连续拼接。测试只创建临时fixture，不会批准真实推送。

## 版本与维护

- 修改文案：只改本篇正文.md，保存后自动预览；未启动服务时手动运行preview。
- 修改图片或裁切：改post.json，服务会自动重排；新增组件后运行markdown-refresh更新正文编辑区。
- 全协会统一换字号：改theme.json，主题id随重大样式变化升级；旧导出文件保留。
- 新增一种可复用版式：扩展一个组件，并用真实内容核对；不要为每一篇单独复制整个排版器。
- 旧赞助数据和10年树龄等有时效内容，不因“模板里有”就沿用。示例保留的是2026-10-24活动提供的材料。
- 当前工具只负责本地预览与制图，不自动发布公众号、不上传秀米、不代发消息。
