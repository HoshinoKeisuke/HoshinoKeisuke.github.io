# 星野恵佑のホームページ運用方針

研究者が論文や講演資料をすぐ見つけられ、同じ情報をプログラムからも読める静的サイトを作る。トップを開いた人が最初に読むのは、名前と短い自己紹介だけでよい。

## 公開先と原稿

- 公開先は既存の GitHub Pages。従来の URL とリポジトリの履歴を引き継ぎ、`main` の更新時に GitHub Actions が `_site/` の静的ファイルを公開する。[公開サイト](https://hoshinokeisuke.github.io/)・[リポジトリ](https://github.com/HoshinoKeisuke/HoshinoKeisuke.github.io)
- 自己紹介とノートの原稿はサイトのリポジトリで Markdown として管理する。今の Profile・Papers・Talks・Notes 用 Google Docs は最初の移行元とする。移行後の編集は Git で行い、すでに公開しているスライドや PDF は既存の URL を利用する。[現在の Google Sites](https://sites.google.com/view/keisuke-hoshino/)
- 論文と講演の書誌情報は CV の `bibliography.bib` を正本とする。サイト側には参照する CV のコミットと、資料リンクや関連する業績などウェブ用の補足を持つ。CV のコンパイルに成功すると、CV リポジトリの GitHub Pages が生成済みの PDF を同じ URL で公開する。[書誌データ](https://github.com/HoshinoKeisuke/CV/blob/main/bibliography.bib)・[CV の公開処理](https://github.com/HoshinoKeisuke/CV/blob/main/.github/workflows/pages.yml)

## 画面に出すもの

| 場所 | 読めるもの |
| --- | --- |
| トップ | 星野 恵佑 / Keisuke Hoshino、所属、短い研究紹介と連絡先。Full profile から詳しいプロフィールへ進める。Papers・Talks・Notes にも直接リンクする。 |
| Profile | 研究関心、博士論文、連絡先。CV はプロフィール内の小さなリンクからブラウザで読める。 |
| Papers | 原題、著者、掲載誌と年。題名から個別ページへ進める。DOI・arXiv は短いリンクにする。 |
| Talks | 原題、会合名、開催日。資料のある講演には題目のそばに Slides を置き、一覧から直接開けるようにする。 |
| Notes | 題名と資料へのリンク。内容や言語の補足が役立つ場合だけ一行添える。 |
| 個別ページ | 出典、関連する論文・講演・資料。サイト上の記録の更新日を末尾に小さく置く。 |

英語を基本にし、氏名は日英併記、論文・講演は原題を保つ。一覧では題名自体を普通のリンクにする。「詳細を開く」という別の操作を足さず、キーボードで選んだときにはリンクの位置が分かるようにする。

初版は福尾匠さんのサイトのグレー（`#B5BCBA`）に黒い文字を組む。印刷時の背景は白。書体は欧文 EB Garamond、和文しっぽり明朝で、両方をサイトから配信する。公開時のホーム・プロフィール・論文・講演の画面は、Actions の `homepage-preview` から PNG でも確認できる。[千葉雅也さんのサイト](https://masayachiba.jp/)・[福尾匠さんのサイト](https://tfukuo.com/)・[平田賢吾さんのサイト](https://kengohirata.github.io/khirata/)

## 機械から読めるもの

同じ記録から、本文を含む静的 HTML と公開用の JSON 一覧（`/data/works.json`）を生成する。各一覧の HTML に JSON の場所を記し、検索・調査ツールが JavaScript を実行せずに題名、資料、更新日をたどれるようにする。河瀬悠人さんのサイトで参考にしたのは、論文・講演にキーを持たせ、資料の追加を講演日と別に記録する点。[河瀬さんのデータ構成](https://github.com/ykawase5048/ykawase5048.github.io#コンテンツの編集)・[公開されている更新記録](https://ykawase5048.github.io/databases/updates.json)

- **識別と関係**　各項目に安定した ID と URL を付ける。CV にあるものは既存の BibTeX キーに対応づけ、同題の論文と講演も別の記録にする。たとえば論文 `MR4875706` と講演 `austms` は、題名の一致に頼らずキーで関連づけられる。
- **内容と出典**　種別、原題、著者・講演者、掲載誌・会合、出版状況、判明している言語と日付を収める。DOI、arXiv、スライド、動画、関連項目は種類を区別してリンクする。
- **日付**　出版日と開催日は研究活動の日付。年しか分からない場合は年のまま保持する。`updated` はその項目の公開記録に書誌訂正・資料追加などを反映した日（日本時間、`YYYY-MM-DD`）。過去の更新日が分からないものは空欄にし、初回移行日は必要なら別に記録する。再ビルドや配色変更で全件の日付を書き換えない。

## 普段の更新

1. 「この論文が出版された」「この講演にスライドを追加」など、変更対象と出典をもとに該当する記録を特定する。
2. 著者・掲載誌・DOI や新しい講演は CV の BibTeX に一度記入する。CV に反映したコミットをサイト側でも指定する。スライド追加だけならサイト側に URL を記入する。どちらの場合も、公開内容が変わる項目の `updated` を記録する。
3. 同じ入力から HTML と JSON を生成する。対象項目の表示、公開 JSON の値、資料リンクを確認する。既存項目の URL が変わっていないこと、無関係な項目の日付が動いていないことも差分で分かるようにする。
4. プレビューを確認してから公開する。CV とサイトは別リポジトリなので、CV を変更したときは**サイト側の参照更新と再生成まで**を一回の更新作業に含める。

### 編集箇所とコマンド

自己紹介は `site/profile.md`、ノートは `data/notes/*.md` を編集する。論文と講演の資料リンク、関連項目、`updated` は `data/details.json` の対象キーに記入する。たとえば講演の資料リンクは `links.slides`。サイト全体は Python 3.11 以降の標準ライブラリでビルドできる。

```sh
python3 scripts/build.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory _site
```

ブラウザで `http://127.0.0.1:8000/` を開く。ビルド時に全項目の HTML・JSON・内部リンクを検証する。書誌情報を更新したときだけ、Git と Pandoc 3 を使って、CV の確定したコミットから `data/cv.json` を再作成してからビルドする。

```sh
cv_checkout=../CV/CVfujiiLike
git -C "$cv_checkout" fetch https://github.com/HoshinoKeisuke/CV.git main
python3 scripts/catalog_sync.py "$cv_checkout" FETCH_HEAD
python3 scripts/build.py
```

## 最初の移行

1. 既存の Pages リポジトリから作業ブランチを切る。Google Docs の公開用原稿と CV を照合し、片方にだけあるノート・講演・資料リンクも拾う。
2. まずトップと、実在する論文・関連講演を一組だけ作る。人が一覧からスライドに進めること、同じ関係と更新日を JSON から取得できることを確認する。
3. 配色と書体を決め、残りの資料を移す。ローカルの比較見本は公開用データから分ける。
4. 新サイトを既存の Pages URL に公開し、論文・スライド・CV が開くことを確認する。その後 Google Sites に移転先を掲示する。この順序なら、旧 URL を載せた研究会ページからも到達できる。
