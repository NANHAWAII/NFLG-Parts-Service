# NFLG Parts Service — 南方路机配件服务门户（Nan, Inc. 内部）

单文件 HTML 站点，部署在 GitHub Pages。数据保存在同一仓库的 `data/db.json`，通过 GitHub Contents API 直接读写，不需要服务器。

```
index.html                   站点（全部逻辑在这一个文件里）
data/db.json                 数据：申请 / 配件 / 设备 / 维修 / 文档记录
data/manual-index/<机型>.json 零配件手册索引（申请时「查手册」用）
docs/<机型>/                  上传的手册、图纸（通过网页上传）
attachments/PR-xxxx/          申请附带的照片（网页自动压缩后上传）
tools/build_manual_index.py  从零配件手册 PDF 生成索引的脚本
README.md
```

## 语言 Language

左下角「EN / 中文」切换，按浏览器语言自动选默认，每人的选择存在自己浏览器里。界面文字全部双语；录入的数据（零件名、备注）原样显示——配件目录里中英文名各一栏，哪种语言下就先显示哪种名字。改界面文字在 `tools/i18n.py` 里，改完 `python tools/i18n.py` 重新注入。

## 两种角色

| | 申请人（工地 / 同事） | 采购部（Fang） |
|---|---|---|
| 打开站点看到 | 配件申请列表，点「新申请」 | 概览 Dashboard |
| 申请表 | 申请人、站点、设备、紧急度、需要日期、配件、原因、照片 | 同左 + 状态、报价、PO#、运输单号、ETA |
| 能做 | 提申请、传照片、看进度、查文档、记维修 | 全部：改状态（看板拖拽）、配件目录、库存、价格、文档上传 |
| 权限来源 | 打开一次采购部发的「团队链接」 | 自己的 token（设置里填） |

申请人提交后自动保存，不需要点「保存到 GitHub」。设置里可填采购部邮箱，申请人提交后可一键发邮件通知。

角色在「设置 → 角色」里切换，存在各自浏览器里。

## 团队链接（给申请人用）

采购部：设置 → 填好 Owner / Repo / Token → 「生成并复制链接」→ 发给同事。同事点开一次，浏览器就记住了，之后直接打开站点地址即可。

链接里带着仓库的写权限，所以只在公司内部发。建议专门为团队链接建一个 token（Repository access 只选这个仓库，Contents: Read and write），万一外泄在 GitHub 上撤销这个 token 就行，自己的 token 不受影响。

## 查手册：申请时按名称找零件号

申请表里的「查手册」框可以按零件号 / 英文 / 中文搜索该机型的零配件手册，点「添加」自动填入零件号、描述、图号、项目号，并能跳到 PDF 对应页（需要该机型的零配件手册已上传到文档库 → 配件手册 分类）。

新机型拿到零配件手册 PDF 后生成索引：

```
pip install pymupdf
python tools/build_manual_index.py "NFS550 Spare Parts Manual.pdf" NFS550 > data/manual-index/NFS550.json
```

提交到仓库后，该机型的申请表就能搜了。NFLG 手册的版式一致（Figure 图号 + Item / Part No / Description / Qty 表），脚本按版式解析；NFJ1175 的 2025V1 手册解析出 105 张图、1824 个零件。

## 功能

| 模块 | 内容 |
|---|---|
| 概览 Dashboard | 未关闭申请、紧急申请、低库存预警、停机设备、申请进度看板、最近维修 |
| 配件申请 Requests | 单号自动生成 (PR-0001…)，状态流：已申请 → 询价中 → 已下单 → 在途 → 已到货 → 关闭；看板拖拽改状态；采购部字段（报价、PO#、运输单号、ETA）；修改历史 |
| 配件目录 Parts | NFLG 图号、OEM 号、中英文名、适用机型、库存 / 安全库存 / 在途、最近价格与日期、交期、库位；CSV 导入导出；申请里填了新图号会自动建档 |
| 设备台账 Equipment | 机型、序列号、站点、状态、小时数、开放申请数、最近维修 |
| 维修记录 Service Log | 故障、处理过程、用料（保存时自动扣库存）、工时、停机时间、小时表读数（自动更新设备小时数）、是否反馈 NFLG / 保修 |
| 文档库 Documents | 按机型（NFJ1175 / NFS550 / NFI1111RS…，可随时添加）存放操作手册、维护手册、配件手册、技术参数、电气图、液压图、控制系统、发动机、选型/报价等；文件直接上传到仓库或填 OneDrive 链接 |
| 设置 Settings | GitHub 连接、站点列表、公告、JSON 备份 / 恢复、深色模式 |

到货（Received）时自动把申请数量加入库存；维修记录用料自动扣库存。

通用：全局搜索、列排序、撤销/重做 (Ctrl+Z / Ctrl+Y)、Ctrl+S 保存、未保存修改留在浏览器本地草稿，多人保存冲突检测。

## 部署（一次性，约 5 分钟）

1. 在 GitHub 建一个新仓库（建议放在 `NANHAWAII` 组织下，Private 也可以），例如 `NFLG-Parts-Service`。
2. 把 `index.html`、`data/db.json`、`README.md` 上传到仓库根目录（`data/db.json` 里是示例数据，可以先用，之后在网页里替换）。
3. 仓库 **Settings → Pages → Source: Deploy from a branch → Branch: main / (root) → Save**。
   几分钟后站点地址为 `https://<owner>.github.io/NFLG-Parts-Service/`。
   （私有仓库开 Pages 需要 GitHub Team / Enterprise 计划；否则仓库需为 Public。）

## 编辑权限（每个需要编辑的人各做一次）

只浏览不需要任何设置。需要编辑并保存的人：

1. GitHub → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**
   - Repository access: 只选 `NFLG-Parts-Service`
   - Permissions → Repository permissions → **Contents: Read and write**
   - 有效期按需（例如 1 年）
2. 打开站点 → **设置** → 填 Owner、Repo、Branch (`main`)、你的名字、Token → **保存连接设置** → **测试连接**。

Token 只保存在该电脑浏览器的 localStorage，不会写进仓库。

## 多人协作

- 每次保存前会检查 `data/db.json` 是否被别人改过；如果有，会提示你覆盖或先重新加载。
- 建议：改完就保存，不要长时间挂着未保存的修改。
- 每次保存都是一次 git commit，仓库历史就是完整的版本记录，出错可以在 GitHub 上回退。

## 文档库：文件放哪里

| 文件 | 做法 |
|---|---|
| ≤ 50 MB（手册、图纸、选型表） | 文档库里「添加文档 / 上传」，文件存到仓库 `docs/<机型>/`，Pages 上直接打开 |
| > 50 MB（如 243 MB 的 Operation Manual） | 放 OneDrive / SharePoint，文档库里填链接。GitHub 单文件硬上限 100 MB，仓库建议 < 1 GB |
| 报价、合同等只给内部看的 | 用 OneDrive 链接。Pages 上的文件任何拿到 URL 的人都能打开，仓库设为私有也一样 |

上传/删除文件会立即写入仓库，并自动保存一次 `db.json`。上传需要 token；只浏览和下载不需要。

新机型两种加法：文档库里「添加机型」，或在设备台账里新建设备时填一个新型号，文档库会自动出现该机型。

## 配件 CSV 导入格式

第一行为列名（与「导出 CSV」一致），`PartNo` 必填，其余可空：

```
PartNo,OEMNo,NameZh,NameEn,Models,Unit,Stock,MinStock,LastPrice,Currency,LastPriceDate,LeadTimeDays,Location,Notes
```

`Models` 多个机型用 `;` 分隔。导入时按 `PartNo` 匹配：已存在则更新，不存在则新增。

## 本地预览

直接双击 `index.html` 时浏览器会阻止读取 `data/db.json`（file:// 限制），用一个本地静态服务器即可：

```
python -m http.server 8000
```

然后打开 http://localhost:8000/
